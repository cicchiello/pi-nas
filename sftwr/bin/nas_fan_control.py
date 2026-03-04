#!/usr/bin/env python3

from pathlib import Path
import subprocess
import json
import glob
import time
import signal
import sys
import os

# ===== PWM config =====
PWMCHIP = Path("/sys/class/pwm/pwmchip0")
CHAN = 2                    # GPIO18 mapping on your Pi 5 setup
PWM = PWMCHIP / f"pwm{CHAN}"
PERIOD_NS = 40_000          # 25 kHz
STOP_DUTY_NS = PERIOD_NS    # fully stop fan
MIN_RUN_DUTY_NS = 32_000    # slowest reliable running point (user-tested)
FULL_SPEED_DUTY_NS = 0      # fastest

POLL_SEC = 10

# ===== temperature thresholds =====
STOP_BELOW_C = 34.0         # if control temp <= this, stop fan
RESTART_ABOVE_C = 37.0      # if stopped, don't restart until above this

# Linear ramp endpoints once fan is running
RAMP_START_C = 38.0         # start fan at MIN_RUN_DUTY_NS
RAMP_FULL_C = 55.0          # reach FULL_SPEED_DUTY_NS here

# ===== control smoothing =====
MAX_DUTY_STEP_NS = 4000     # limit per-loop duty change to reduce sudden jumps
MIN_APPLY_DELTA_NS = 500    # ignore tiny changes to reduce chatter

# ===== state =====
running = True
fan_is_stopped = False
current_duty_ns = STOP_DUTY_NS


def write(path: Path, value):
    path.write_text(str(value))


def ensure_exported():
    if not PWM.exists():
        write(PWMCHIP / "export", CHAN)
        time.sleep(0.1)


def enable_pwm():
    write(PWM / "period", PERIOD_NS)
    write(PWM / "enable", 1)


def set_pwm_duty_ns(duty_ns: int):
    duty_ns = max(0, min(PERIOD_NS, int(duty_ns)))
    write(PWM / "duty_cycle", duty_ns)


def cpu_temp_c() -> float:
    return int(Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip()) / 1000.0


def drive_temp_c(dev: str):
    try:
        out = subprocess.check_output(
            ["smartctl", "-j", "-A", dev],
            stderr=subprocess.DEVNULL,
            text=True
        )
        data = json.loads(out)

        table = data.get("ata_smart_attributes", {}).get("table", [])
        for attr in table:
            attr_id = attr.get("id")
            name = attr.get("name", "").lower()

            if attr_id in (190, 194) or "temperature" in name:
                raw = attr.get("raw", {})

                # Best case: smartctl provides a printable string like "37 (Min/Max 20/45)"
                raw_str = raw.get("string")
                if raw_str:
                    import re
                    m = re.search(r"-?\d+", raw_str)
                    if m:
                        t = float(m.group(0))
                        if 0 <= t <= 100:
                            return t

                # Fallback: raw.value, but only if sane
                raw_val = raw.get("value")
                if isinstance(raw_val, int) and 0 <= raw_val <= 100:
                    return float(raw_val)

        # NVMe-style fallback
        t = data.get("temperature", {}).get("current")
        if t is not None and 0 <= t <= 100:
            return float(t)

    except Exception:
        pass

    return None


def drive_temp_c_bak(dev: str):
    try:
        out = subprocess.check_output(
            ["smartctl", "-j", "-A", dev],
            stderr=subprocess.DEVNULL,
            text=True
        )
        data = json.loads(out)

        table = data.get("ata_smart_attributes", {}).get("table", [])
        for attr in table:
            name = attr.get("name", "").lower()
            if "temperature" in name:
                raw = attr.get("raw", {}).get("value")
                if isinstance(raw, int):
                    return float(raw)

        t = data.get("temperature", {}).get("current")
        if t is not None:
            return float(t)

    except Exception:
        pass
    return None


def all_drive_temps():
    temps = {}
    for dev in sorted(glob.glob("/dev/sd?")):
        t = drive_temp_c(dev)
        if t is not None:
            temps[dev] = t
    return temps


def map_temp_to_target_duty(temp_c: float) -> int:
    """
    Returns target duty_cycle in ns.
    Lower duty = faster fan
    Higher duty = slower fan
    """
    if temp_c <= RAMP_START_C:
        return MIN_RUN_DUTY_NS

    if temp_c >= RAMP_FULL_C:
        return FULL_SPEED_DUTY_NS

    frac = (temp_c - RAMP_START_C) / (RAMP_FULL_C - RAMP_START_C)
    duty = MIN_RUN_DUTY_NS * (1.0 - frac)
    return int(round(duty))


def choose_target_duty(control_temp_c: float) -> int:
    global fan_is_stopped

    # Hysteresis for stop/start
    if fan_is_stopped:
        if control_temp_c < RESTART_ABOVE_C:
            return STOP_DUTY_NS
        fan_is_stopped = False
        return map_temp_to_target_duty(control_temp_c)

    if control_temp_c <= STOP_BELOW_C:
        fan_is_stopped = True
        return STOP_DUTY_NS

    return map_temp_to_target_duty(control_temp_c)


def slew_limit(prev_duty: int, target_duty: int) -> int:
    delta = target_duty - prev_duty
    if abs(delta) <= MAX_DUTY_STEP_NS:
        return target_duty
    if delta > 0:
        return prev_duty + MAX_DUTY_STEP_NS
    return prev_duty - MAX_DUTY_STEP_NS


def apply_duty_if_needed(target_duty: int):
    global current_duty_ns

    next_duty = slew_limit(current_duty_ns, target_duty)

    # Always apply when crossing into or out of STOP, otherwise ignore tiny adjustments
    crossing_stop = (
        (current_duty_ns >= STOP_DUTY_NS and next_duty < STOP_DUTY_NS) or
        (current_duty_ns < STOP_DUTY_NS and next_duty >= STOP_DUTY_NS)
    )

    if crossing_stop or abs(next_duty - current_duty_ns) >= MIN_APPLY_DELTA_NS:
        set_pwm_duty_ns(next_duty)
        current_duty_ns = next_duty


def handle_exit(signum, frame):
    global running
    running = False


def cleanup():
    try:
        if PWM.exists():
            write(PWM / "duty_cycle", STOP_DUTY_NS)
            write(PWM / "enable", 1)
    except Exception:
        pass


def main():
    global fan_is_stopped, current_duty_ns

    ensure_exported()
    enable_pwm()

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    temps = all_drive_temps()
    cpu = cpu_temp_c()
    hottest_drive = max(temps.values()) if temps else None
    control_temp = max([cpu] + ([hottest_drive] if hottest_drive is not None else []))

    fan_is_stopped = control_temp <= STOP_BELOW_C
    current_duty_ns = STOP_DUTY_NS if fan_is_stopped else choose_target_duty(control_temp)
    set_pwm_duty_ns(current_duty_ns)

    while running:
        cpu = cpu_temp_c()
        temps = all_drive_temps()
        hottest_drive = max(temps.values()) if temps else None
        control_temp = max([cpu] + ([hottest_drive] if hottest_drive is not None else []))

        target_duty = choose_target_duty(control_temp)
        apply_duty_if_needed(target_duty)

        drive_str = ", ".join(f"{k}:{v:.1f}C" for k, v in temps.items()) if temps else "no drive temps"
        state = "STOPPED" if current_duty_ns >= STOP_DUTY_NS else f"duty={current_duty_ns}"
        print(
            f"CPU={cpu:.1f}C | drives=({drive_str}) | control={control_temp:.1f}C "
            f"| target={target_duty} | fan={state}",
            flush=True
        )

        time.sleep(POLL_SEC)

    cleanup()


if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Please run as root (needed for /sys/class/pwm and smartctl).", file=sys.stderr)
        sys.exit(1)
    main()

