# Pi NAS Fan Control

Simple temperature-based fan control for a Raspberry Pi 5 NAS using:

- Raspberry Pi 5
- Radxa Penta SATA HAT
- Noctua NF-A8 PWM 4-wire fan
- GPIO18 for PWM control
- Hardware PWM via `/sys/class/pwm`
- CPU temperature plus SATA HDD SMART temperatures

This project uses a small transistor interface so the Pi can safely drive the fan's blue PWM control wire in the expected open-collector style.

## Repository Layout

- `bin/nas_fan_control.py`  
  Main control loop. Reads temperatures and sets fan PWM.

- `bin/toggle_gpio18.py`  
  Simple GPIO18 logic test script used during bring-up.

- `etc/systemd/system/nas-fan-control.service`  
  Systemd unit file for running the control loop at boot.

## Hardware Overview

The Noctua 4-wire fan is wired as follows:

- **Yellow** -> +12V
- **Black** -> GND
- **Blue** -> PWM control input
- **Green** -> Tach (unused in this project)

The fan's 12V power is provided directly from the NAS power source.

The Pi does **not** drive the blue PWM wire directly. Instead, GPIO18 drives a small transistor stage that pulls the blue wire low when commanded.

### Control Interface

A 2N2222-style NPN transistor is used as an open-collector pull-down:

- GPIO18 -> base resistor -> transistor base
- transistor emitter -> GND
- transistor collector -> fan blue PWM wire
- Pi GND and fan GND must be common

Because of this arrangement:

- lower PWM `duty_cycle` value in sysfs = **faster fan**
- higher PWM `duty_cycle` value in sysfs = **slower fan**
- `duty_cycle = 40000` (equal to period) = fan stopped
- `duty_cycle = 0` = full speed

## PWM Configuration

This setup uses:

- **GPIO18**
- **25 kHz PWM**
- PWM period of **40000 ns**

On this system, GPIO18 is exposed through:

- `/sys/class/pwm/pwmchip0/pwm2`

## Enable PWM on GPIO18

Edit:

```bash
sudo nano /boot/firmware/config.txt
```

Add to the end:

```txt
dtoverlay=pwm-2chan
```

This enables hardware PWM on GPIO18/GPIO19.

If you are not using onboard analog audio, it is a good idea to remove or comment out:

```txt
dtparam=audio=on
```

Then reboot:

```bash
sudo reboot
```

After reboot, you can confirm PWM is available:

```bash
ls -R /sys/class/pwm
pinctrl get 18-19
```

## Manual PWM Bring-Up Test

Export PWM channel 2 and try a fixed duty:

```bash
cd /sys/class/pwm/pwmchip0
echo 2 | sudo tee export
echo 40000 | sudo tee pwm2/period
echo 20000 | sudo tee pwm2/duty_cycle
echo 1 | sudo tee pwm2/enable
```

Useful behavior observed on this build:

- around `35000` to `36000` -> fan stalls/stops
- `32000` -> slowest reliable running value
- larger values -> slower fan
- smaller values -> faster fan

## Software Requirements

Install SMART monitoring tools:

```bash
sudo apt update
sudo apt install -y smartmontools
```

The control loop uses:

- `/sys/class/thermal/thermal_zone0/temp` for CPU temperature
- `smartctl -j -A /dev/sdX` for HDD temperatures

## Install the Control Script

Copy the script into place:

```bash
sudo install -m 755 bin/nas_fan_control.py /usr/local/bin/nas_fan_control.py
```

You can test it manually:

```bash
sudo /usr/local/bin/nas_fan_control.py
```

It will:

- read CPU temperature
- read all `/dev/sd?` SATA device temperatures that respond to SMART
- use the hottest temperature as the control input
- stop the fan when cool
- restart with hysteresis
- ramp speed smoothly with slew limiting

## Install the Systemd Service

Copy the included service file:

```bash
sudo install -D -m 644 \
  etc/systemd/system/nas-fan-control.service \
  /etc/systemd/system/nas-fan-control.service
```

Reload systemd and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nas-fan-control.service
```

Check status:

```bash
sudo systemctl status nas-fan-control.service
journalctl -u nas-fan-control.service -f
```

## Control Logic

The current default tuning is:

- stop fan at or below **34 C**
- restart only above **37 C**
- begin running at minimum reliable speed above **38 C**
- ramp to full speed by **55 C**

The fan speed is based on the higher of:

- CPU temperature
- hottest HDD temperature

This avoids letting the drives get warm while the CPU remains cool.

## Tuning Notes

The key tuning values are near the top of `bin/nas_fan_control.py`:

- `STOP_BELOW_C`
- `RESTART_ABOVE_C`
- `RAMP_START_C`
- `RAMP_FULL_C`
- `MIN_RUN_DUTY_NS`

If the fan chatters too much:

- increase the gap between stop and restart thresholds
- increase `MIN_APPLY_DELTA_NS`
- increase `POLL_SEC`

If the fan starts unreliably:

- reduce `MIN_RUN_DUTY_NS` (for example from `32000` to `30000`)

If the speed changes are too abrupt:

- reduce `MAX_DUTY_STEP_NS`

## GPIO Test Script

To verify GPIO18 can be toggled before enabling hardware PWM:

```bash
sudo python3 bin/toggle_gpio18.py
```

This is only for initial logic bring-up and is not used by the final control loop.

## Notes

- This project assumes the Radxa HAT's own fan-control software is **not** being used.
- If another service or overlay claims GPIO18/PWM, this project may conflict with it.
- The tach wire is currently unused, but RPM monitoring could be added later.

## Future Improvements

Possible future additions:

- tach/RPM monitoring
- per-drive weighting instead of simple max temperature
- configurable thresholds from a separate config file
- logging to syslog/journald only, without stdout status lines
- support for more explicit device lists instead of scanning `/dev/sd?`
