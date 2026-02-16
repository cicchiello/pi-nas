# Pi5 NAS Enclosure — Design Specification

## Overview

Acrylic laser-cut enclosure for a Raspberry Pi 5 NAS with 4× 3.5" SATA HDDs, a Radxa Penta SATA HAT, and a top-mounted 80mm exhaust fan. Designed for vertical drive orientation with laminar airflow from bottom to top.

## Coordinate System

- **X**: Left-to-right (drive pitch direction)
- **Y**: Front-to-back (drive depth direction)
- **Z**: Bottom-to-top (vertical)

## Key Dimensions

| Parameter | Value | Notes |
|-----------|-------|-------|
| Interior X | 185mm | Drives + gaps + edge margins |
| Interior Y | 120mm | 2× screw clearance + 2× rail + HDD width |
| Exterior X | 191mm | Interior + 2× 3mm walls |
| Exterior Y | 126mm | Interior + 2× 3mm walls |
| Total height | 335.4mm | ~13.2 inches |
| Wall thickness | 3mm | All outer panels |
| Comb rail thickness | 5mm | Drive mounting rails |

## Z-Stack (bottom to top)

| Z (mm) | Feature |
|---------|---------|
| 0 | Bottom panel exterior |
| 3.0 | Bottom panel interior (T_WALL) |
| 10.0 | Pi5 PCB bottom (7mm standoff) |
| 27.2 | Pi5 top (USB connectors) |
| 30.2 | HAT PCB bottom (3mm gap above Pi5) |
| 42.5 | HAT top |
| 142.5 | Drive zone bottom (HAT top + 100mm cable zone) |
| 289.4 | Drive zone top |
| 299.4 | Fan bracket (10mm airflow gap above drives) |
| 327.4 | Fan top (bracket 3mm + fan 25mm) |
| 332.4 | Top panel interior (5mm clearance above fan) |
| 335.4 | Top panel exterior |

## Assembly Strategy

### Corner Structure
- **4 vertical M4 threaded rods** pass through the top and bottom horizontal panels (and fan bracket).
- Rods are inset 11mm (T_WALL + 2×ROD_DIA) from panel edges.
- Rubber grommets (10mm OD) at each rod hole for vibration isolation.
- Rods do NOT pass through any vertical panels (front, back, side).

### Panel Interlocking
- **Front/back panels**: Outward-protruding tabs (outer_tab) on L/R vertical edges pass through rectangular through-slots in the side panel faces. Notches (tab mode) on top/bottom edges receive top/bottom panel protrusions.
- **Side panels**: Straight L/R edges with rectangular through-slots to receive front/back tabs. Upward/downward-protruding tabs on top/bottom edges (central EXT_Y region only) pass through rectangular through-slots in the top/bottom panel faces. Flat SIDE_OVERLAP wings at each end of top/bottom edges.
- **Side panels** extend 6mm (SIDE_OVERLAP) past front/back on each end (138mm total width vs 126mm exterior Y) with 3mm material overhang around each through-slot.
- **Top/bottom panels**: 191 × 132mm (EXT_X × EXT_Y + 2×T_WALL). Finger protrusions on front/back edges interlock with front/back panel notches. Rectangular through-slots near L/R edges receive side panel tabs. Extend 3mm past side panels on each side.

### Finger Joints
- Nominal finger width: 12mm.
- Tab depth: 3mm (= T_WALL).
- Odd number of fingers per edge for symmetric pattern.

## Component Placement

### Raspberry Pi 5
- Mounted on bottom panel via M2.5 standoffs.
- **Rotated 90°**: Short edge (56mm, USB/Ethernet ports) faces the front panel.
- Centered left-to-right on the bottom panel.
- Port edge flush with front panel interior face (Y = T_WALL on bottom panel).

### Penta SATA HAT
- Stacked above Pi5 on M2.5 × 24mm copper standoffs.
- HAT top at Z = 35.6mm.

### HDDs (×4)
- Oriented vertically (length along Z, connector end down).
- Mounted on comb rail teeth via M3 side screws through SFF-8301 holes.
- Drive pitch: 46.11mm (26.11mm drive + 20mm gap).
- 10mm margin from outer drive faces to side walls.
- 20mm face-to-face gap between adjacent drives for laminar airflow.

### Drive Comb Rails (×2)
- 5mm acrylic, identical front and back rails.
- Horizontal bar (12mm tall) at top with 4 teeth (20mm wide) hanging downward.
- Each tooth holds one drive; drives are screwed to tooth faces from both sides.
- 3 screw holes per tooth face (matching SFF-8301 side-mount pattern).
- Bar spans full interior width (185mm).
- Tabs integrated into the cut path at each end of the bar, slotting into side panel slots.
- 4mm clearance between rail face and front/back panel for screw head access.
- Tooth length: ~137mm (HDD length minus 10mm margin at bottom).

### Fan
- Noctua NF-A8 80mm, top-mounted on internal fan bracket.
- Fan bracket is a 3mm acrylic shelf with rod clearance holes at corners.
- Top panel has a 74mm circular opening and fan screw holes.

## Panel Summary

| # | Panel | Bounding Box | Thickness | Finger Joints | Rod Holes |
|---|-------|-------------|-----------|---------------|----------|
| 01 | Bottom | 191 × 138 | 3mm | Front/back: protrusions, L/R: through-slots | 4 corners |
| 02 | Top | 191 × 138 | 3mm | Front/back: protrusions, L/R: through-slots | 4 corners |
| 03 | Front | 197 × 329.4 | 3mm | Top/bottom: notch, L/R: outer_tab | None |
| 04 | Back | 197 × 329.4 | 3mm | Top/bottom: notch, L/R: outer_tab | None |
| 05 | Left side | 138 × 335.4 | 3mm | Top/bottom: tab, L/R: flat + through-slots | None |
| 06 | Right side | 138 × 335.4 | 3mm | Top/bottom: tab, L/R: flat + through-slots | None |
| 07 | Comb rail (×2) | 185 × 137 | 5mm | Integrated tabs | None |
| 09 | Fan bracket | 183 × 118 | 3mm | None (flat rect) | 4 corners |

## Ventilation

- **Bottom panel**: Slots under Pi5 area.
- **Top panel**: 74mm fan opening with concentric vent ring finger guard.
- **Side panels**: Horizontal vent slots in cable zone and drive zone.
- **Back panel**: Horizontal vent slots in cable zone and drive zone.
- **Front panel**: Minimal (port cutouts provide some airflow).
- Airflow path: Bottom intake → Pi5/HAT → cable zone → drives → fan exhaust (top).

## Port Access

- **Front panel**: Pi5 Gigabit Ethernet (RJ45), 2× USB port cutouts.
- **Back panel**: 12mm panel-mount DC barrel jack (12V input). No Pi5 HDMI/USB-C access.

## SVG Conventions

- Red (`#ff0000`): Cut lines.
- Blue (`#0000ff`): Score/engrave lines (annotations, grommet rings, component outlines).
- All dimensions in mm.
- 6mm margin (T_WALL + 3) around panels with protruding tabs; 5mm default otherwise.
- Generated by `generate_panels.py` into `svg_output/`.
- `panel_review.html` provides on-screen review with print support (100mm scale ruler on each page).
