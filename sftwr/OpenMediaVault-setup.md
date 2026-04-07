# pi-nas Setup Reference

## Purpose

This file captures the working OpenMediaVault setup for **pi-nas**, including:
- base platform choices
- network configuration
- RAID/filesystem/share setup
- SMART and notifications
- custom fan-control integration
- important recovery notes
- known issues and fixes
- snapshot strategy

This is a **reference snapshot**, not an exact replay script.

---

## Current Working Baseline

### Host / platform
- Hostname: `pi-nas`
- Platform: Raspberry Pi 5
- OS base: Raspberry Pi OS Lite 64-bit
- OMV installed and working
- OMV web UI reachable
- SSH reachable
- Wired and Wi-Fi both enabled
- RAID1 array healthy
- SMB share accessible from macOS and Linux
- SMART monitoring enabled
- Email notifications working through Gmail
- `nas-fan-control.service` restored and running

### Storage
- Two 8TB Seagate drives
- Models:
  - `/dev/sda` = `ST8000DM004-2U9188` serial `WSC310LG`
  - `/dev/sdb` = `ST8000DM004-2U9188` serial `ZR16FJWN`
- RAID:
  - `/dev/md0`
  - RAID1 / Mirror
- Filesystem:
  - `ext4`
- Mounted path observed:
  - `/srv/dev-disk-by-uuid-1b03c883-24b8-4bbc-9e3f-9fdc70389470/`
- Shared folder created in OMV:
  - `pi-nas`
- SMB share created and working

### User access
- Linux user: `joe`
- OMV web login user: `admin`
- SMB access tested successfully with `joe`

---

## Snapshot / Rollback Strategy

The safest rollback method has been **external SD-card imaging** at key milestones.

### Good times to take an SD-card image
1. Fresh OMV install, networking working
2. After disks wiped, before RAID creation
3. After RAID creation
4. After filesystem creation and mount
5. After SMB share works from clients
6. After notifications/SMART are working
7. After full package update succeeds
8. Before any major future change:
   - network edits
   - plugin installs
   - Docker/Compose
   - HTTPS changes
   - major OMV upgrades

### Preferred rollback method
- Power down or remove SD card
- Image from another machine
- Keep images clearly labeled by milestone

### Note about OMV backup plugin
- `openmediavault-backup` was investigated
- It is essentially an image/backup UI for the OMV system disk, not a simple config-export tool
- Since external SD imaging is already working well, plugin was removed

---

## Base OS / Non-OMV Customization

### Locale
Set and generated:
- `en_US.UTF-8`

### Editor
Installed:
- `emacs-lucid`

This was chosen because it had previously behaved better over X11/XQuartz than the GTK build.

### Useful packages installed/restored during bring-up
- `smartmontools`
- `samba`
- `avahi-daemon`
- `rpi-connect`
- `emacs-lucid`

### Root SSH login
- Disabled later for security
- Keep using normal user + `sudo`

---

## Custom Fan Control

A custom fan-control loop was restored and is still in use.

### Service
- File: `/etc/systemd/system/nas-fan-control.service`

Contents:

```ini
[Unit]
Description=NAS fan control loop
After=local-fs.target
Wants=local-fs.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/bin/nas_fan_control.py
Restart=always
RestartSec=5
User=root
WorkingDirectory=/usr/local/bin

[Install]
WantedBy=multi-user.target
```

### Script
- File: `/usr/local/bin/nas_fan_control.py`
- Ownership/permissions:
  - `root:root`
  - executable

### Important script behavior
- PWM path: `/sys/class/pwm/pwmchip0`
- Channel: `2`
- Period: `40000 ns` (25 kHz)
- Uses:
  - CPU thermal zone
  - `smartctl -j -A /dev/sd?` for disk temperatures
- Current control logic uses drive temps for control threshold behavior and logs status periodically

### Verified working signs
- Service active and running
- Reads `/dev/sda` and `/dev/sdb` temperatures
- Example logs showed:
  - CPU around 50C+
  - drives around 34C–35C
  - fan state `STOPPED` when below threshold

---

## Boot Configuration

### Important retained `config.txt` lines
These matter for SATA/PCIe and PWM:

```text
dtparam=pciex1
dtparam=pciex1_gen=3
dtoverlay=pwm-2chan
```

These were important enough to preserve from the earlier setup.

### Less important desktop-era lines
Desktop/display-related settings were intentionally not treated as critical during the Lite rebuild.

---

## Network Configuration

### Final intent
- Wired should be the preferred path
- Wi-Fi should remain available as fallback
- Host should stay reachable even if Ethernet has issues

### Key actual interface names
- Wired interface: `end0`
- Wi-Fi interface: `wlan0`

### Important lesson
OMV stored and generated config originally assumed `eth0`, but the actual system used `end0`.  
That mismatch later broke networking when OMV re-applied netplan.

### Working wired network values
- Static IPv4:
  - `10.0.0.214/24`
- Gateway:
  - `10.0.0.1`
- DNS:
  - `8.8.8.8`
  - `10.0.0.1`

### Working Wi-Fi
- `wlan0` exists and was configured successfully
- Wi-Fi should be kept available as fallback
- No further Wi-Fi changes were desired after it was working

### OMV network apply failure that was fixed
OMV had pending changes involving:
- `apticron`
- `smartmontools`
- `ssh`
- `systemd-networkd`

Applying failed with `500 - Internal Server Error` because OMV was generating invalid netplan YAML.

#### Root cause
In `/etc/openmediavault/config.xml`, the stored values for:
- `<gateway>`
- `<dnsnameservers>`

contained duplicated line content, and OMV also had:
- `<devicename>eth0</devicename>`

instead of:
- `<devicename>end0</devicename>`

This caused OMV to keep regenerating broken `/etc/netplan/20-openmediavault-eth0.yaml`.

#### Bad stored XML that was observed
```xml
<gateway>10.0.0.1
10.0.0.1</gateway>

<dnsnameservers>8.8.8.8 10.0.0.1
10.0.0.1</dnsnameservers>
```

#### Corrected stored XML
```xml
<devicename>end0</devicename>
<gateway>10.0.0.1</gateway>
<dnsnameservers>8.8.8.8 10.0.0.1</dnsnameservers>
```

#### Generated netplan that needed manual correction on SD card
Final working content:

```yaml
network:
  ethernets:
    end0:
      match:
        name: end0
      addresses:
      - 10.0.0.214/24
      routes:
      - to: 0.0.0.0/0
        via: 10.0.0.1
      dhcp4: no
      dhcp6: no
      link-local: []
      nameservers:
        addresses:
        - 8.8.8.8
        - 10.0.0.1
```

### Recovery note
If networking breaks again after an OMV apply:
1. Check `/etc/openmediavault/config.xml` first
2. Confirm `<devicename>` is `end0`
3. Confirm gateway and DNS are single-line values
4. If necessary, edit the generated `/etc/netplan/20-openmediavault-eth0.yaml` on the SD card offline so the system can boot reachable again

---

## OMV Install / Storage Bring-up

### OMV install path
- Installed on Raspberry Pi OS Lite 64-bit
- Desktop image was rejected by OMV installer earlier
- Lite rebuild was used instead

### Disk handling strategy
- Did **not** reuse old `fstab` for the data disks
- Let OMV manage data disks/filesystem/mounts itself

### Basic storage steps taken
1. Confirmed correct disks in **Storage → Disks**
2. Quick-wiped both 8TB drives
3. Installed `openmediavault-md` plugin because RAID management was not initially present in core UI
4. Used **Storage → Multiple Devices**
5. Created:
   - name: `md0`
   - type: `Mirror`
6. Waited for RAID1 resync
7. Created `ext4` filesystem on `/dev/md0`
8. Mounted filesystem in OMV
9. Created shared folder `pi-nas`
10. Enabled SMB/CIFS
11. Added SMB share for the shared folder

### Important note
The full RAID resync took a long time (many hours).  
This was normal and the array remained usable during resync.

### Healthy RAID state example
`/proc/mdstat`:

```text
md0 : active raid1 sda[0] sdb[1]
      7813894464 blocks super 1.2 [2/2] [UU]
```

`mdadm --detail /dev/md0` showed:
- `State : clean`
- `Active Devices : 2`
- `Working Devices : 2`
- `Failed Devices : 0`

---

## SMB / Client Access

### macOS
- Finder connection succeeded after:
  - enabling SMB service
  - applying OMV changes
  - ensuring `joe` could authenticate

### Important SMB gotcha
At one point, the SMB share existed but access failed because:
- `smbd` was inactive
- enabling SMB in OMV and applying changes fixed it

### Linux client mount
Observed issue:
- Linux client could mount and read, but not write

Cause:
- CIFS mount was presented as `uid=0,gid=0` with `0755` permissions

Working remount approach:
```bash
sudo mount -t cifs //10.0.0.214/pi-nas /mnt/extra \
  -o username=joe,uid=$(id -u),gid=$(id -g),file_mode=0664,dir_mode=0775
```

This made the mounted files writable by the local Linux user.

### Share security settings
- Share is browseable
- Public = `No`
- `joe` has read/write access
- Write/rename/delete tested successfully from macOS

---

## SMART / Monitoring / Notifications

### SMART
Configured in OMV:
- Global SMART enabled
- Individual monitoring enabled for both `/dev/sda` and `/dev/sdb`

### Scheduled SMART tests
Configured:
- Short test weekly
- Long test monthly

The UI displayed only hour-level scheduling, not minute-level editing.

### Gmail notifications
Working configuration required:
- SMTP server: `smtp.gmail.com`
- Port: `587`
- Security: `STARTTLS`
- Username: full Gmail address
- Password: **Google app password**
- App password entered **without spaces**

### Important Gmail troubleshooting lesson
Using the wrong security/port pairing caused:
- `SSL_connect ... wrong version number`
- TLS handshake failure

Correct pairings:
- `587 + STARTTLS`
- or `465 + SSL/TLS`

Working choice here:
- `587 + STARTTLS`

---

## mdadm False Alert Problem

### Symptom
Repeated email alerts like:
- `DeviceDisappeared event detected on md device /dev/md/md0`
- `NewArray event detected on md device /dev/md0`

These happened many times even though RAID was healthy.

### Verified healthy state during alerts
- `/proc/mdstat` showed `[UU]`
- `mdadm --detail /dev/md0` showed clean, active, no failed devices

### Cause
OMV/mdadm false-alert behavior tied to `/dev/md/md0` vs `/dev/md0` device path handling.

### Fix that worked
A udev rule was added/activated so `/dev/md/md0` exists:

Expected resulting symlink:
```text
/dev/md/md0 -> ../md0
```

After that, this stopped reproducing the false alert:

```bash
sudo mdadm --monitor --scan --oneshot
```

### Validation
Observed:
```text
total 0
lrwxrwxrwx 1 root root 6 ... md0 -> ../md0
```

After the symlink existed, the false mdadm monitor messages stopped.

---

## Monitoring Alert: High Load Average

### Observed email
OMV/Monit sent:
- `loadavg (1min) > 8.0`

### Interpretation
Likely transient and related to:
- large file transfers
- storage activity
- RAID resync / disk-heavy workload

Not treated as evidence of failure since the system stayed responsive.

---

## OMV Admin / Password Notes

### OMV web login user
- `admin`

### Shell login user
- `joe`

### Password recovery method
If OMV web password is forgotten:
```bash
sudo omv-firstaid
```

Use it to reset the Workbench/web administrator password.

---

## Update Strategy Used

### OMV UI behavior
OMV web Update Management did not support the desired selective package install workflow in a practical way.

### Final decision
Because there was already a recent SD-card image, a full package update was done with the willingness to roll back if necessary.

### Result
- Full update completed successfully
- System remained healthy after reboot

Afterward, another SD-card image was taken.

---

## Plugins / Optional Components

### Installed during setup
- `openmediavault-md`
- `openmediavault-backup` (temporary)
- later removed `openmediavault-backup`

### Deferred / intentionally not pursued now
- `openmediavault-compose`
- `openmediavault-clamav`
- HTTPS for OMV web UI
- broader plugin/app ecosystem

Reason: stop at a stable baseline before expanding the system further.

---

## Current “Stop Here” Baseline

At the agreed stopping point:
- keep Wi-Fi enabled
- no further optional plugins
- no further major configuration changes for now

System is considered a good stable baseline with:
- OMV working
- RAID1 working
- SMB working
- SMART monitoring working
- email notifications working
- root SSH login disabled
- rollback images taken

---

## Recovery Checklist (Short)

If `pi-nas` becomes unreachable after a network apply:
1. Check whether it still answers `ping`
2. If not reachable, power-cycle once
3. If still broken, move SD card to helper Linux machine
4. Inspect:
   - `/etc/openmediavault/config.xml`
   - `/etc/netplan/20-openmediavault-eth0.yaml`
5. Ensure:
   - `end0` is used, not `eth0`
   - gateway is one line
   - DNS nameservers are one line
   - netplan YAML is valid
6. Reinsert card and reboot

If RAID emails look suspicious:
1. Check `/proc/mdstat`
2. Check `sudo mdadm --detail /dev/md0`
3. If `[UU]` and `clean`, the array is fine
4. Be aware of the past false `/dev/md/md0` alert issue

If OMV web login is forgotten:
1. SSH into the Pi
2. Run:
   ```bash
   sudo omv-firstaid
   ```

---

## Useful Commands

### RAID health
```bash
cat /proc/mdstat
sudo mdadm --detail /dev/md0
```

### Fan service
```bash
systemctl status nas-fan-control.service --no-pager
```

### Netplan / network
```bash
ip -br addr
sudo omv-salt deploy run systemd-networkd
sudo nl -ba /etc/netplan/20-openmediavault-eth0.yaml
sudo grep -n -C 3 '<devicename>\|<address>\|<gateway>\|<dnsnameservers>' /etc/openmediavault/config.xml
```

### SMTP / mail troubleshooting
```bash
sudo journalctl -u postfix -n 50 --no-pager
sudo tail -n 50 /var/log/mail.log
```

### mdadm false-alert test
```bash
sudo mdadm --monitor --scan --oneshot
ls -l /dev/md
```

### Forgot OMV admin password
```bash
sudo omv-firstaid
```

---

## Final Notes

This setup is now at a good baseline. Future likely areas of work:
- additional shares and user structure
- HTTPS for OMV web UI
- Docker / Compose
- data-backup strategy beyond SD-card rollback
- optional monitoring threshold tuning

For now, the main recommendation is:
- avoid unnecessary changes
- keep taking SD-card images before major changes
- treat this file as the setup reference paired with those images
