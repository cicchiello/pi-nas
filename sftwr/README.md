# pi-nas

`pi-nas` is a Raspberry Pi 5-based NAS bring-up project for a home lab storage server.

The system is intended to provide:

- LAN backup storage
- media storage and serving
- photo storage
- general-purpose file serving

This repository is the working documentation and configuration space for the full NAS build. It currently includes fan-control bring-up and will later expand to cover enclosure and mechanical notes as well.

## Platform

The current hardware and software stack is:

- Raspberry Pi 5
- Radxa Penta SATA HAT
- up to 4 HDDs
- first planned drive: Seagate Barracuda 8TB
- Noctua NF-A8 80mm PWM fan
- Raspberry Pi OS (64-bit)

The storage subsystem is intended to become a RAID-based array, but RAID configuration is not finalized yet.

## Network Services

The NAS is intended to be exposed on the local network using:

- SMB
- NFS
- possibly AFP

These services are part of the overall bring-up plan, but may not all be configured yet.

## Repository Scope

This repo is for the full `pi-nas` bring-up, including:

- platform setup
- hardware integration notes
- service configuration
- subsystem-specific guides
- future enclosure and mechanical documentation

## Fan Control Guide

Fan-control design, wiring, PWM setup, temperature control logic, and service installation are documented separately in:

- [FAN.md](./FAN.md)

`FAN.md` is the subsystem guide for the Noctua NF-A8 fan driven from GPIO18 using hardware PWM.

## Current Repository Layout

The repository currently contains:

- `bin/nas_fan_control.py` - Python control loop for fan speed based on CPU and HDD temperatures
- `bin/toggle_gpio18.py` - GPIO18 bring-up and wiring test script
- `etc/systemd/system/nas-fan-control.service` - systemd unit for automatic fan-control startup
- `FAN.md` - fan-control subsystem guide

Additional top-level documentation and subsystem guides can be added over time as the NAS build matures.

## Status

Current status:

- base NAS platform defined
- fan hardware wired and PWM control validated
- Python fan-control loop implemented
- systemd service defined
- broader RAID, file-serving, and enclosure work still in progress

## Planned Next Steps

Planned areas for expansion include:

- RAID layout and filesystem decisions
- SMB/NFS service configuration
- optional AFP evaluation
- drive provisioning and health monitoring
- enclosure and airflow/mechanical notes
- additional bring-up scripts and operational docs

## Notes

This README is intended as the top-level overview for the overall `pi-nas` project.

Detailed implementation notes for specific subsystems should live in their own markdown files and be referenced from here.
