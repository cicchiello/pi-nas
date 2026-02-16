# Pi5 NAS Enclosure — Bill of Materials

## Acrylic Panels (Laser Cut)

| # | Part | Material | Thickness | Bounding Box (mm) | Qty |
|---|------|----------|-----------|-------------------|-----|
| 01 | Bottom panel | Clear acrylic | 3mm | 191 × 138 | 1 |
| 02 | Top panel | Clear acrylic | 3mm | 191 × 138 | 1 |
| 03 | Front panel | Clear acrylic | 3mm | 197 × 329.4 | 1 |
| 04 | Back panel | Clear acrylic | 3mm | 197 × 329.4 | 1 |
| 05 | Left side panel | Clear acrylic | 3mm | 138 × 335.4 | 1 |
| 06 | Right side panel | Clear acrylic | 3mm | 138 × 335.4 | 1 |
| 07 | Drive comb rail | Clear acrylic | 5mm | 185 × 137 | 2 |
| 09 | Fan bracket | Clear acrylic | 3mm | 183 × 118 | 1 |

## Electronics

| Part | Specification | Qty | Notes |
|------|--------------|-----|-------|
| Raspberry Pi 5 | 4GB or 8GB | 1 | |
| Radxa Penta SATA HAT | For Pi5 | 1 | Provides 5× SATA ports |
| 3.5" HDD | Seagate Barracuda (or similar) | 4 | 146.99 × 101.6 × 26.11mm |
| Noctua NF-A8 | 80mm fan, 5V or 12V | 1 | Top-mounted exhaust |
| 12V DC power supply | 5.5 × 2.5mm barrel jack | 1 | Sized for drives + Pi5 |
| DC barrel jack | 5.5 × 2.5mm panel-mount | 1 | Mounts in back panel |

## Structural Hardware

| Part | Specification | Qty | Notes |
|------|--------------|-----|-------|
| M4 threaded rod | ~345mm length | 4 | Vertical clamping rods through top+bottom panels |
| M4 nut | Stainless | 8 | 2 per rod (top + bottom) |
| M4 washer | Stainless | 8 | 2 per rod |
| Rubber grommet | 10mm OD, 4.5mm ID | 8 | Vibration isolation at rod holes |
| M4 wing nut or knob | (optional) | 4 | For tool-free top panel removal |

## Drive Mounting Hardware

| Part | Specification | Qty | Notes |
|------|--------------|-----|-------|
| M3 × 6mm screw | Pan head, #6-32 UNC also acceptable | 24 | 3 holes × 2 sides × 4 drives |
| M3 nut | Stainless | 24 | Behind comb rail teeth |
| M3 rubber washer | Silicone or neoprene | 24 | Vibration isolation between drive and tooth |

## Pi5 / HAT Mounting

| Part | Specification | Qty | Notes |
|------|--------------|-----|-------|
| M2.5 × 7mm standoff | Female-female, nylon or brass | 4 | Pi5 to bottom panel |
| M2.5 × 24mm standoff | Male-female, copper | 4 | Pi5 to Penta SATA HAT (18mm post + 6mm) |
| M2.5 × 6mm screw | Pan head | 8 | 4 bottom + 4 top |

## Fan Mounting

| Part | Specification | Qty | Notes |
|------|--------------|-----|-------|
| M4 × 30mm screw | Pan head | 4 | Through fan bracket + fan |
| M4 nut | Stainless | 4 | |
| Rubber fan mount | Noctua anti-vibration | 4 | Optional, replaces screws |

## Notes

- Side panels are 138mm wide (126mm exterior Y + 6mm overlap on each end) to wrap around front/back panel edges for interlocking.
- Top/bottom panels are 191 × 132mm (126mm exterior Y + 3mm extension on each side to overlap side panels).
- Front/back panels have outward-protruding tabs (outer_tab) on L/R edges that pass through rectangular slots in the side panel faces.
- Side panels have upward/downward-protruding tabs on top/bottom edges that pass through rectangular slots in the top/bottom panel faces.
- Top/bottom panels have finger protrusions on front/back edges that interlock with notches on the front/back panel top/bottom edges.
- Comb rails are 5mm acrylic for rigidity; all other panels are 3mm.
- Two identical comb rails are used: one near the front, one near the back of the drive group, with 4mm clearance to the front/back panels for screw head access.
- Each drive is screwed to one comb rail tooth from both sides (front + back rail).
- Threaded rods only pass through horizontal panels (top, bottom, fan bracket) — not through any vertical panels.
- Rod holes are inset 11mm (T_WALL + 2×ROD_DIA) from panel edges.
