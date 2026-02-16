#!/usr/bin/env python3
"""
Pi5 NAS Acrylic Enclosure — SVG Panel Generator (v3)

Generates laser-cut SVG files for all enclosure panels.
All dimensions in mm. SVG output uses mm units.
Red lines = cut. Blue lines = score/engrave.

Assembly strategy:
  - Front/back panels have outward-protruding tabs on L/R edges (through side panel face slots).
  - Side panels have through-slots in their faces for front/back tabs, and tabs on top/bottom edges.
  - Side panels extend SIDE_OVERLAP (6mm) past front/back on each end for overlap.
  - Top/bottom panels (191x132mm) have finger protrusions on front/back edges and through-slots
    near L/R edges to receive side panel tabs. They extend 3mm past side panels on each side.
  - 4 vertical M4 threaded rods pass through top, bottom, and fan bracket only.
  - Comb rails slot into side panels via integrated tabs.
"""

import math
import os

# ============================================================
# PARAMETERS
# ============================================================

T_WALL = 3.0        # outer panel acrylic thickness
T_BRACKET = 5.0     # drive bracket / comb rail acrylic thickness
KERF = 0.1          # laser kerf half-width

# Corner threaded rods (M4) — vertical only, through top+bottom panels
ROD_DIA = 4.0
ROD_HOLE = 4.5      # clearance hole
GROMMET_OD = 10.0   # rubber grommet outer diameter

# Raspberry Pi 5
PI5_L = 85.0         # long edge (USB-C, HDMI, audio on this edge)
PI5_W = 56.0         # short edge (USB-A, RJ45 Ethernet on this edge)
PI5_HOLE_SPACING_X = 58.0
PI5_HOLE_SPACING_Y = 49.0
PI5_HOLE_DIA = 2.7   # M2.5 clearance
PI5_HOLE_OFFSET_X = 3.5
PI5_HOLE_OFFSET_Y = 3.5

# Penta SATA HAT
HAT_L = 100.0
HAT_W = 56.0

# Seagate Barracuda 3.5" HDD
HDD_L = 146.99       # length — becomes vertical height
HDD_W = 101.6        # width — becomes depth (Y)
HDD_T = 26.11        # thickness — becomes horizontal pitch (X)
# SFF-8301 side mounting holes: 3 per side, #6-32 UNC (M3 compatible)
# Measured from connector end of drive along length:
HDD_SIDE_HOLE_Z = [28.50, 70.50, 130.50]
HDD_SIDE_HOLE_INSET = 6.35  # mm from drive face to hole center

# Noctua NF-A8 80mm fan
FAN_SIZE = 80.0
FAN_DEPTH = 25.0     # fan thickness
FAN_HOLE_SPACING = 71.5
FAN_MOUNT_HOLE = 4.3

# Layout
NUM_DRIVES = 4
DRIVE_GAP = 20.0       # 20mm face-to-face between adjacent drives for laminar airflow
DRIVE_EDGE_MARGIN = 10.0  # 10mm from outer drive face to side wall
CABLE_ZONE_H = 100.0   # 10cm for SATA cables
PI5_STANDOFF_H = 7.0   # M2.5 standoff under Pi5 (clears ~2mm bottom protrusion)
PI5_ENVELOPE_H = 18.0  # Pi5 PCB bottom to top of tallest connector (RJ45, from STEP)
PI5_TO_HAT_GAP = 3.0   # gap from Pi5 USB top to HAT PCB bottom (GPIO seated)
HAT_ENVELOPE_H = 12.25 # HAT PCB bottom to top of tallest connector (from STEP)

# Comb rail — horizontal bar at top with teeth hanging downward
COMB_BAR_H = 12.0      # height of the horizontal bar at top of comb
COMB_TOOTH_W = 20.0    # tooth width (X direction) — wide enough for M3 holes + margin
SCREW_HEAD_CLR = 4.0   # clearance between comb face and front/back panel for screw heads

# Assembly
SIDE_OVERLAP = 3.0 + T_WALL          # 3mm overhang + 3mm slot = 6mm

# Finger joints
FINGER_WIDTH = 12.0

# ============================================================
# DERIVED DIMENSIONS
# ============================================================

# Drive group: 4 drives + 3 gaps (face-to-face)
DRIVE_GROUP_W = NUM_DRIVES * HDD_T + (NUM_DRIVES - 1) * DRIVE_GAP
DRIVE_ZONE_W = DRIVE_GROUP_W + 2 * DRIVE_EDGE_MARGIN  # + margins to side walls

INTERIOR_X = max(DRIVE_ZONE_W, HAT_L + 20, PI5_L + 20)
# Y interior must fit: screw_clr + rail(5mm) + HDD_W + rail(5mm) + screw_clr
INTERIOR_Y = max(2 * SCREW_HEAD_CLR + 2 * T_BRACKET + HDD_W, PI5_W + 20)
INTERIOR_X = math.ceil(INTERIOR_X / 5) * 5
INTERIOR_Y = math.ceil(INTERIOR_Y / 5) * 5

EXT_X = INTERIOR_X + 2 * T_WALL
EXT_Y = INTERIOR_Y + 2 * T_WALL

# Z-stack (from bottom of enclosure)
Z_BOT_TOP = T_WALL
Z_PI5_PCB = Z_BOT_TOP + PI5_STANDOFF_H
Z_PI5_TOP = Z_PI5_PCB + PI5_ENVELOPE_H           # top of USB connectors
Z_HAT_PCB = Z_PI5_TOP + PI5_TO_HAT_GAP           # bottom of HAT PCB
Z_HAT_TOP = Z_HAT_PCB + HAT_ENVELOPE_H           # top of HAT connectors
Z_DRIVE_BOT = Z_HAT_TOP + CABLE_ZONE_H
Z_DRIVE_TOP = Z_DRIVE_BOT + HDD_L
# Fan zone above drives:
#   10mm airflow gap + 3mm fan bracket + 25mm fan + 5mm clearance to top panel
FAN_GAP = 10.0          # gap between drive tops and fan bracket for airflow
Z_FAN_BRACKET = Z_DRIVE_TOP + FAN_GAP           # bottom of fan bracket
Z_FAN_TOP = Z_FAN_BRACKET + T_WALL + FAN_DEPTH  # top of fan (bracket=3mm + fan=25mm)
Z_TOP_PANEL = Z_FAN_TOP + 5                     # 5mm clearance above fan to top panel
TOTAL_H = Z_TOP_PANEL + T_WALL

SIDE_H = Z_TOP_PANEL  # front/back/side panel height (Z=0 to Z=Z_TOP_PANEL)

# Comb rail: bar top edge at Z_DRIVE_TOP, bar extends downward, teeth below that
# This keeps the bar within the drive zone, leaving fan zone clear above.
COMB_BAR_Z = Z_DRIVE_TOP - COMB_BAR_H  # bar bottom edge = Z_DRIVE_TOP - 12mm
COMB_TOOTH_LEN = HDD_L - COMB_BAR_H - 10  # tooth hangs below bar, leave 10mm at bottom
COMB_TOTAL_H = COMB_BAR_H + COMB_TOOTH_LEN

ROD_INSET = T_WALL + 2 * ROD_DIA  # rod hole inset from panel edge

print(f"Interior: {INTERIOR_X} x {INTERIOR_Y} mm")
print(f"Exterior: {EXT_X:.1f} x {EXT_Y:.1f} mm")
print(f"Total height: {TOTAL_H:.1f} mm ({TOTAL_H/25.4:.1f} in)")
print(f"Drive bottom Z: {Z_DRIVE_BOT:.1f} mm")
print(f"Side panel H: {SIDE_H:.1f} mm")

# ============================================================
# SVG WRITER
# ============================================================

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "svg_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class SVG:
    def __init__(self, w, h, fname, margin=5):
        self.w = w
        self.h = h
        self.margin = margin
        self.fname = fname
        self.els = []

    def _f(self, v):
        return f"{v:.3f}".rstrip('0').rstrip('.')

    def _mx(self, x):
        return x + self.margin

    def _my(self, y):
        return y + self.margin

    def rect(self, x, y, w, h, style="cut"):
        c = "#ff0000" if style == "cut" else "#0000ff"
        self.els.append(f'<rect x="{self._f(self._mx(x))}" y="{self._f(self._my(y))}" '
                        f'width="{self._f(w)}" height="{self._f(h)}" '
                        f'fill="none" stroke="{c}" stroke-width="0.1"/>')

    def rrect(self, x, y, w, h, r=1.0, style="cut"):
        c = "#ff0000" if style == "cut" else "#0000ff"
        self.els.append(f'<rect x="{self._f(self._mx(x))}" y="{self._f(self._my(y))}" '
                        f'width="{self._f(w)}" height="{self._f(h)}" '
                        f'rx="{self._f(r)}" ry="{self._f(r)}" '
                        f'fill="none" stroke="{c}" stroke-width="0.1"/>')

    def circle(self, cx, cy, r, style="cut"):
        c = "#ff0000" if style == "cut" else "#0000ff"
        self.els.append(f'<circle cx="{self._f(self._mx(cx))}" cy="{self._f(self._my(cy))}" '
                        f'r="{self._f(r)}" fill="none" stroke="{c}" stroke-width="0.1"/>')

    def slot(self, x, y, w, h, style="cut"):
        r = min(w, h) / 2
        self.rrect(x, y, w, h, r, style)

    def path_d(self, pts, closed=True):
        d = f'M {self._f(self._mx(pts[0][0]))},{self._f(self._my(pts[0][1]))}'
        for p in pts[1:]:
            d += f' L {self._f(self._mx(p[0]))},{self._f(self._my(p[1]))}'
        if closed:
            d += ' Z'
        return d

    def path(self, pts, closed=True, style="cut"):
        c = "#ff0000" if style == "cut" else "#0000ff"
        self.els.append(f'<path d="{self.path_d(pts, closed)}" fill="none" stroke="{c}" stroke-width="0.1"/>')

    def text(self, x, y, txt, size=3):
        self.els.append(f'<text x="{self._f(self._mx(x))}" y="{self._f(self._my(y))}" '
                        f'font-size="{size}" fill="#999" font-family="monospace">{txt}</text>')

    def save(self):
        tw = self.w + 2 * self.margin
        th = self.h + 2 * self.margin
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self._f(tw)}mm" height="{self._f(th)}mm" '
            f'viewBox="0 0 {self._f(tw)} {self._f(th)}">',
            '<!-- Red=cut, Blue=score/engrave. All dims in mm. -->',
        ]
        lines.extend(f'  {e}' for e in self.els)
        lines.append('</svg>')
        fp = os.path.join(OUTPUT_DIR, self.fname)
        with open(fp, 'w') as f:
            f.write('\n'.join(lines) + '\n')
        print(f"  {self.fname}")
        return fp


# ============================================================
# FINGER JOINT OUTLINE BUILDER
# ============================================================

def finger_outline(w, h, top='flat', bottom='flat', left='flat', right='flat', depth=T_WALL, skip_lr_ends=False):
    """
    Build a closed polygon for a rectangular panel with optional finger joints.
    Each edge: 'tab' = fingers protrude outward, 'slot' = notches cut inward, 'flat' = straight.
    Traversal: clockwise starting from top-left.
    """
    def edge_pts(length, n, mode, axis, start, perp, direction, inward, skip_ends=False):
        pts = []
        fw = length / n
        for i in range(n):
            s = i * fw
            e = (i + 1) * fw
            is_finger = (i % 2 == 0)
            # If skip_ends, treat first and last finger positions as flat
            if skip_ends and is_finger and (i == 0 or i == n - 1):
                is_finger = False
            is_last = (i == n - 1)
            if mode == 'flat':
                if axis == 'x':
                    pts.append((start + direction * s, perp))
                else:
                    pts.append((perp, start + direction * s))
            elif (mode in ('tab', 'outer_tab', 'slot') and is_finger):
                # tab: edge recedes inward; slot/outer_tab: edge protrudes outward
                d = -depth if mode == 'tab' else depth
                if axis == 'x':
                    pts.append((start + direction * s, perp))
                    pts.append((start + direction * s, perp + inward * d))
                    pts.append((start + direction * e, perp + inward * d))
                    pts.append((start + direction * e, perp))
                else:
                    pts.append((perp, start + direction * s))
                    pts.append((perp + inward * d, start + direction * s))
                    pts.append((perp + inward * d, start + direction * e))
                    pts.append((perp, start + direction * e))
            else:
                if axis == 'x':
                    pts.append((start + direction * s, perp))
                    pts.append((start + direction * e, perp))
                else:
                    pts.append((perp, start + direction * s))
                    pts.append((perp, start + direction * e))
        return pts

    def nfingers(length):
        n = max(3, round(length / FINGER_WIDTH))
        if n % 2 == 0:
            n += 1
        return n

    # Skip first/last fingers on top/bottom edges when adjacent left/right edges
    # have finger joints, to avoid stray notch-wall segments at corners.
    skip_tb = (left != 'flat' or right != 'flat')

    pts = []
    # Top edge: left to right, y=0
    pts.extend(edge_pts(w, nfingers(w), top, 'x', 0, 0, 1, -1, skip_ends=skip_tb))
    # Right edge: top to bottom, x=w
    pts.extend(edge_pts(h, nfingers(h), right, 'y', 0, w, 1, 1, skip_ends=skip_lr_ends))
    # Bottom edge: right to left, y=h
    pts.extend(edge_pts(w, nfingers(w), bottom, 'x', w, h, -1, 1, skip_ends=skip_tb))
    # Left edge: bottom to top, x=0
    pts.extend(edge_pts(h, nfingers(h), left, 'y', h, 0, -1, -1, skip_ends=skip_lr_ends))

    # Remove consecutive duplicate points
    clean = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - clean[-1][0]) > 0.001 or abs(p[1] - clean[-1][1]) > 0.001:
            clean.append(p)
    return clean


# ============================================================
# HELPER: corner rod holes (top/bottom panels only)
# ============================================================

def add_rod_holes(svg, pw, ph, inset=ROD_INSET):
    """Add vertical rod clearance holes at 4 corners of a horizontal panel."""
    for cx, cy in [(inset, inset), (pw - inset, inset),
                   (inset, ph - inset), (pw - inset, ph - inset)]:
        svg.circle(cx, cy, ROD_HOLE / 2)
        svg.circle(cx, cy, GROMMET_OD / 2, style="engrave")


# ============================================================
# HELPER: top/bottom panel outline
# ============================================================

def tb_panel_outline(w, h):
    """
    Custom outline for top/bottom panels (w=EXT_X, h=EXT_Y+2*T_WALL).
    - Top/bottom edges: finger protrusions spanning EXT_X (mate with front/back panel notches).
    - Left/right edges: straight (through-slots added separately as rects).
    """
    pts = []
    depth = T_WALL

    # --- Finger parameters for top/bottom edges (front/back mating) ---
    n_fb = max(3, round(w / FINGER_WIDTH))
    if n_fb % 2 == 0:
        n_fb += 1
    fw_fb = w / n_fb

    # Top edge: left to right, y=0. Protrusions go upward (y=-depth).
    for i in range(n_fb):
        x0 = i * fw_fb
        x1 = (i + 1) * fw_fb
        if i % 2 == 0:  # protrusion
            pts.append((x0, 0))
            pts.append((x0, -depth))
            pts.append((x1, -depth))
            pts.append((x1, 0))
        else:
            pts.append((x0, 0))
            pts.append((x1, 0))

    # Right edge: straight
    pts.append((w, 0))
    pts.append((w, h))

    # Bottom edge: right to left, y=h. Protrusions go downward (y=h+depth).
    for i in range(n_fb - 1, -1, -1):
        x0 = i * fw_fb
        x1 = (i + 1) * fw_fb
        if i % 2 == 0:  # protrusion
            pts.append((x1, h))
            pts.append((x1, h + depth))
            pts.append((x0, h + depth))
            pts.append((x0, h))
        else:
            pts.append((x1, h))
            pts.append((x0, h))

    # Left edge: straight
    pts.append((0, h))
    pts.append((0, 0))

    # Remove consecutive duplicate points
    clean = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - clean[-1][0]) > 0.001 or abs(p[1] - clean[-1][1]) > 0.001:
            clean.append(p)
    return clean


def add_tb_side_slots(svg, w, h):
    """
    Add rectangular through-slots near the left/right edges of a top/bottom panel
    to receive the side panel tabs. Slot positions match the side panel tab positions.
    """
    n_lr = max(3, round(EXT_Y / FINGER_WIDTH))
    if n_lr % 2 == 0:
        n_lr += 1
    fw_lr = EXT_Y / n_lr
    slot_w = T_WALL  # slot width = side panel thickness
    min_overhang = 3.0  # material between slot and panel edge

    for edge_side in ['left', 'right']:
        if edge_side == 'left':
            slot_x = min_overhang
        else:
            slot_x = w - min_overhang - slot_w
        for i in range(n_lr):
            if i % 2 == 0:  # tabs are at even indices on side panels
                slot_y = T_WALL + i * fw_lr
                svg.rect(slot_x, slot_y, slot_w, fw_lr)


# ============================================================
# PANEL: Bottom
# ============================================================

def gen_bottom():
    w = EXT_X
    h = EXT_Y + 2 * T_WALL  # extend 3mm past side panels on each side
    s = SVG(w, h, "01_bottom_panel.svg", margin=T_WALL + 3)
    s.text(0, -3, f"BOTTOM PANEL {w:.0f}x{h:.0f}mm (3mm)")

    # Custom outline: finger protrusions on top/bottom (front/back mating), straight left/right.
    outline = tb_panel_outline(w, h)
    s.path(outline)

    # Through-slots near left/right edges to receive side panel tabs.
    add_tb_side_slots(s, w, h)

    # Corner rod holes — vertical rods through top+bottom only
    add_rod_holes(s, w, h)

    # Pi5 mounting holes — USB-A/RJ45 end flush with front panel
    # The Pi5's USB-A and RJ45 Ethernet ports are on the SHORT edge (56mm).
    # Rotate Pi5 so short edge (56mm) runs along X (left-right),
    # long edge (85mm) runs along Y (front-to-back).
    # Port edge at Y = T_WALL (front panel interior face).
    pi_w_on_panel = PI5_W   # 56mm along X (left-right)
    pi_h_on_panel = PI5_L   # 85mm along Y (front-to-back)
    pi_ox = (w - pi_w_on_panel) / 2   # centered left-to-right
    pi_oy = T_WALL                     # port edge flush with front panel interior
    # Mounting holes: Pi5 native coords have origin at GPIO corner.
    # Native X runs along 85mm (long edge), native Y along 56mm (short edge).
    # After 90° rotation with USB/Eth end at front:
    #   panel_x_offset = native_y  (short edge maps to panel X)
    #   panel_y_offset = PI5_L - native_x  (long edge reversed: USB end X=85 -> Y=0=front)
    for nx, ny in [(PI5_HOLE_OFFSET_X, PI5_HOLE_OFFSET_Y),
                   (PI5_HOLE_OFFSET_X + PI5_HOLE_SPACING_X, PI5_HOLE_OFFSET_Y),
                   (PI5_HOLE_OFFSET_X, PI5_HOLE_OFFSET_Y + PI5_HOLE_SPACING_Y),
                   (PI5_HOLE_OFFSET_X + PI5_HOLE_SPACING_X, PI5_HOLE_OFFSET_Y + PI5_HOLE_SPACING_Y)]:
        hx = ny                  # native Y -> panel X
        hy = PI5_L - nx          # native X -> panel Y (reversed)
        s.circle(pi_ox + hx, pi_oy + hy, PI5_HOLE_DIA / 2)

    # Ventilation slots under Pi area
    for row in range(3):
        vy = pi_oy + 15 + row * 25
        for col in range(2):
            vx = pi_ox + 8 + col * 28
            s.slot(vx, vy, 18, 2.5)

    # SD card access hole — SD slot is on the back edge (X- in STEP = high Y on panel).
    # Slot spans ~22–34mm along the 56mm short edge (from STEP Z coords).
    # Rounded rect straddling the Pi5 back edge for finger access.
    sd_cx = 22.05   # offset from pi_ox along 56mm edge
    sd_w = 14.0     # slightly wider than 12mm slot for finger access
    sd_h = 20.0     # extends past PCB edge for finger reach
    sd_x = pi_ox + sd_cx + (34.0 - 22.05 - sd_w) / 2  # centered on slot
    sd_y = pi_oy + pi_h_on_panel - sd_h / 4            # skewed past back edge for finger access
    s.rrect(sd_x, sd_y, sd_w, sd_h, r=3)
    s.text(sd_x, sd_y - 1.5, "SD card", size=2)

    # Score: Pi5 outline (rotated)
    s.rect(pi_ox, pi_oy, pi_w_on_panel, pi_h_on_panel, style="engrave")
    s.text(pi_ox + 2, pi_oy + 10, "Pi5 (USB-A/RJ45 end at front)", size=3)

    s.save()


# ============================================================
# PANEL: Top
# ============================================================

def gen_top():
    w = EXT_X
    h = EXT_Y + 2 * T_WALL  # extend 3mm past side panels on each side
    s = SVG(w, h, "02_top_panel.svg", margin=T_WALL + 3)
    s.text(0, -3, f"TOP PANEL {w:.0f}x{h:.0f}mm (3mm)")

    # Custom outline: finger protrusions on top/bottom (front/back mating), straight left/right.
    outline = tb_panel_outline(w, h)
    s.path(outline)

    # Through-slots near left/right edges to receive side panel tabs.
    add_tb_side_slots(s, w, h)

    add_rod_holes(s, w, h)

    # Fan opening — centered
    cx, cy = w / 2, h / 2
    s.circle(cx, cy, 37)  # 74mm opening

    # Fan mounts to internal bracket, not top panel — no screw holes here

    # Finger guard — concentric vent rings
    for r in [10, 18, 26, 34]:
        n = max(6, int(2 * math.pi * r / 6))
        for i in range(n):
            a = 2 * math.pi * i / n
            s.circle(cx + r * math.cos(a), cy + r * math.sin(a), 1.2)

    s.save()


# ============================================================
# PANEL: Front (Pi5 USB/Ethernet port side)
# ============================================================

def gen_front():
    w, h = EXT_X, SIDE_H
    s = SVG(w, h, "03_front_panel.svg", margin=T_WALL + 3)
    s.text(0, -3, f"FRONT PANEL {w:.0f}x{h:.1f}mm (3mm)")

    # tab on top/bottom = notches to receive top/bottom panel protrusions.
    # outer_tab on left/right = tabs protruding outward into side panel through-slots.
    # skip_lr_ends: omit first/last tabs — no matching slots at side panel corners.
    outline = finger_outline(w, h, top='tab', bottom='tab', left='outer_tab', right='outer_tab', skip_lr_ends=True)
    s.path(outline)

    # No rod holes — vertical rods pass through top/bottom panels only

    # Panel Y axis: Y=0 = top (Z=Z_TOP_PANEL), Y=SIDE_H = bottom (Z=0)
    def z_to_y(z_enc):
        return Z_TOP_PANEL - z_enc

    # Pi5 port cutouts (dimensions from STEP file, confirmed by user)
    # Pi5 is rotated: short edge (56mm, USB-A/RJ45) faces this panel.
    # Front panel SVG X is mirrored vs bottom panel X (viewed from outside).
    # Facing the front panel from outside, left-to-right: GbE, USB3, USB2.
    pi_x = (w - PI5_W) / 2   # Pi5 short edge (56mm) centered in X
    pi_pcb_y = z_to_y(Z_PI5_PCB)  # PCB bottom in panel Y coords

    # Port positions along the 56mm short edge (from STEP model).
    # (name, x_offset_from_pi_left, z_offset_from_pcb_bottom, width, height)
    # z_offset: height of connector housing bottom above PCB bottom.
    #   Ethernet is flush with PCB top (1.45mm above PCB bottom).
    #   USB stacks are elevated ~1mm above PCB top (2.45mm above PCB bottom).
    # Includes ~1mm clearance margin per side.
    # Order left-to-right on front panel: GbE | USB 3.0 | USB 2.0
    ports = [
        ("GbE",   1.25,   0.45, 17.9, 15.5),   # RJ45 Ethernet (flush with PCB top = 1.45 above PCB bot)
        ("USB3", 21.30,   1.45, 15.6, 16.6),   # Stacked USB 3.0 pair (~1mm above PCB top = 2.45 above PCB bot)
        ("USB2", 39.10,   1.45, 15.8, 16.6),   # Stacked USB 2.0 pair (~1mm above PCB top = 2.45 above PCB bot)
        ("HAT",  35.10,  22.05, 19.8,  6.1),   # Penta SATA HAT connector (4mm above USB2 top, right-aligned with USB2)
    ]
    for name, px, pz, pw, ph in ports:
        cx = pi_x + px
        # pz is height of cutout bottom above PCB bottom, ph extends upward
        # In panel coords: cutout top = pi_pcb_y - (pz + ph)
        cy = pi_pcb_y - pz - ph
        s.rrect(cx, cy, pw, ph, r=1.5)
        s.text(cx, cy - 1.5, name, size=2)

    # DC barrel jack — 8mm hole (7.85mm threaded OD), centered 30mm left of Pi5, 15mm above bottom panel top
    dc_x = pi_x - 30
    dc_y = z_to_y(T_WALL + 15)
    s.circle(dc_x, dc_y, 4.0)
    s.text(dc_x + 6, dc_y + 1, "DC 12V", size=2)

    # Score line showing drive zone start
    dz_y = z_to_y(Z_DRIVE_BOT)
    s.rect(10, dz_y - 0.15, w - 20, 0.3, style="engrave")
    s.text(2, dz_y + 3, f"drive zone", size=2)

    s.save()


# ============================================================
# PANEL: Back (DC jack + vents, no Pi5 port access)
# ============================================================

def gen_back():
    w, h = EXT_X, SIDE_H
    s = SVG(w, h, "04_back_panel.svg", margin=T_WALL + 3)
    s.text(0, -3, f"BACK PANEL {w:.0f}x{h:.1f}mm (3mm)")

    # tab on top/bottom = notches to receive top/bottom panel protrusions.
    # outer_tab on left/right = tabs protruding outward into side panel through-slots.
    # skip_lr_ends: omit first/last tabs — no matching slots at side panel corners.
    outline = finger_outline(w, h, top='tab', bottom='tab', left='outer_tab', right='outer_tab', skip_lr_ends=True)
    s.path(outline)

    # No rod holes — vertical rods pass through top/bottom panels only

    # Panel Y axis: Y=0 = top (Z=Z_TOP_PANEL), Y=SIDE_H = bottom (Z=0)
    def z_to_y(z_enc):
        return Z_TOP_PANEL - z_enc

    # Pi5 HDMI/USB-C/Audio ports — NOT cut out (user doesn't need access)
    # Pi5 is rotated: long edge (85mm) runs front-to-back (Y on back panel = enclosure X)
    pi_x = (w - PI5_W) / 2  # 56mm short edge centered in X
    pi_z_y = z_to_y(Z_PI5_PCB + 1.45)  # top of PCB (1.45mm thick from STEP)
    s.rect(pi_x, pi_z_y, PI5_W, 1.45, style="engrave")
    s.text(pi_x, pi_z_y - 1.5, "Pi5 (no port access this side)", size=2)

    # DC barrel jack — moved to front panel

    # Ventilation: cable zone
    vx_start, vx_end = 20, w - 20
    slot_w, slot_h = 22, 2.5
    cable_z0 = Z_HAT_TOP + 15
    cable_z1 = Z_DRIVE_BOT - 10
    if cable_z1 > cable_z0:
        for i in range(5):
            vz = cable_z0 + i * (cable_z1 - cable_z0) / 4
            for j in range(3):
                vx = vx_start + j * (vx_end - vx_start - slot_w) / 2
                s.slot(vx, z_to_y(vz), slot_w, slot_h)

    # Ventilation: drive zone
    dz0 = Z_DRIVE_BOT + 15
    dz1 = Z_DRIVE_TOP - 10
    for i in range(8):
        vz = dz0 + i * (dz1 - dz0) / 7
        for j in range(3):
            vx = vx_start + j * (vx_end - vx_start - slot_w) / 2
            s.slot(vx, z_to_y(vz), slot_w, slot_h)

    s.save()


# ============================================================
# PANEL: Side (left and right are mirrors)
# ============================================================

def gen_side(side='left'):
    # Side panel extends SIDE_OVERLAP past front and back panels
    w = EXT_Y + 2 * SIDE_OVERLAP  # wider to wrap around front/back
    h = SIDE_H
    idx = "05" if side == 'left' else "06"
    s = SVG(w, h, f"{idx}_{side}_side_panel.svg", margin=T_WALL + 3)
    s.text(0, -3, f"{side.upper()} SIDE {w:.1f}x{h:.1f}mm (3mm)")

    # Custom outline: top/bottom edges have tabs in the central EXT_Y region
    # (mating with top/bottom panel slots), with flat SIDE_OVERLAP wings on each end.
    # Left/right edges are FLAT — interlocking with front/back is via through-slots in the face.
    def side_outline():
        pts = []
        n_tb = max(3, round(EXT_Y / FINGER_WIDTH))
        if n_tb % 2 == 0:
            n_tb += 1
        fw = EXT_Y / n_tb
        depth = T_WALL

        # Top edge: left to right, y=0
        # Left wing (flat)
        pts.append((0, 0))
        pts.append((SIDE_OVERLAP, 0))
        # Central tabs
        for i in range(n_tb):
            x0 = SIDE_OVERLAP + i * fw
            x1 = SIDE_OVERLAP + (i + 1) * fw
            if i % 2 == 0:  # tab — protrudes upward (negative y)
                pts.append((x0, 0))
                pts.append((x0, -depth))
                pts.append((x1, -depth))
                pts.append((x1, 0))
            else:
                pts.append((x0, 0))
                pts.append((x1, 0))
        # Right wing (flat)
        pts.append((SIDE_OVERLAP + EXT_Y, 0))
        pts.append((w, 0))

        # Right edge: top to bottom (flat)
        pts.append((w, 0))
        pts.append((w, h))

        # Bottom edge: right to left, y=h
        # Right wing (flat)
        pts.append((w, h))
        pts.append((SIDE_OVERLAP + EXT_Y, h))
        # Central tabs
        for i in range(n_tb - 1, -1, -1):
            x0 = SIDE_OVERLAP + i * fw
            x1 = SIDE_OVERLAP + (i + 1) * fw
            if i % 2 == 0:  # tab — protrudes downward (positive y)
                pts.append((x1, h))
                pts.append((x1, h + depth))
                pts.append((x0, h + depth))
                pts.append((x0, h))
            else:
                pts.append((x1, h))
                pts.append((x0, h))
        # Left wing (flat)
        pts.append((SIDE_OVERLAP, h))
        pts.append((0, h))

        # Left edge: bottom to top (flat)
        pts.append((0, h))
        pts.append((0, 0))

        # Remove consecutive duplicate points
        clean = [pts[0]]
        for p in pts[1:]:
            if abs(p[0] - clean[-1][0]) > 0.001 or abs(p[1] - clean[-1][1]) > 0.001:
                clean.append(p)
        return clean

    outline = side_outline()
    s.path(outline)

    # Through-slots for front/back panel tabs.
    # The front/back panels sit at x=SIDE_OVERLAP and x=w-SIDE_OVERLAP on this panel.
    # Their tabs protrude through the side panel face.
    # Tab positions match the front/back panel's left/right edge finger pattern.
    fb_h = SIDE_H  # front/back panel height (same as side)
    n_fingers = max(3, round(fb_h / FINGER_WIDTH))
    if n_fingers % 2 == 0:
        n_fingers += 1
    fw = fb_h / n_fingers
    tab_depth = T_WALL  # 3mm tab protrusion — no extra clearance, laser kerf provides it
    slot_w = tab_depth
    min_overhang = 3.0  # minimum material between slot edge and panel edge
    for edge_side in ['left', 'right']:
        # Place slot so outer edge is exactly min_overhang from the panel edge
        if edge_side == 'left':
            slot_x = min_overhang
        else:
            slot_x = w - min_overhang - slot_w
        for i in range(n_fingers):
            if i % 2 == 0:  # tabs are at even indices on front/back panels
                # Skip first and last finger — too close to top/bottom edges
                # where the top/bottom panel finger joint slots are
                if i == 0 or i == n_fingers - 1:
                    continue
                slot_y = i * fw
                s.rect(slot_x, slot_y, slot_w, fw)

    # Side panel Y axis: Y=0 = top (Z=Z_TOP_PANEL), Y=SIDE_H = bottom (Z=0)
    # To convert enclosure Z to side panel Y: panel_y = Z_TOP_PANEL - enclosure_z
    def z_to_y(z_enc):
        return Z_TOP_PANEL - z_enc

    # Comb rail mounting slots — two rails (front + back of drives)
    # X on side panel = SIDE_OVERLAP + (enclosure Y position - T_WALL)
    rail_front_y = T_WALL + SCREW_HEAD_CLR + T_BRACKET / 2
    rail_back_y = EXT_Y - T_WALL - SCREW_HEAD_CLR - T_BRACKET / 2

    tab_slot_w = T_BRACKET + 0.3  # 5mm rail + clearance
    tab_slot_h = 10.3  # matches tab_h=10 + clearance
    # Comb bar center Z in enclosure = COMB_BAR_Z + COMB_BAR_H/2
    bar_center_y = z_to_y(COMB_BAR_Z + COMB_BAR_H / 2)
    for rail_y in [rail_front_y, rail_back_y]:
        slot_x = SIDE_OVERLAP + (rail_y - T_WALL) - tab_slot_w / 2
        slot_y = bar_center_y - tab_slot_h / 2
        s.rect(slot_x, slot_y, tab_slot_w, tab_slot_h)

    # Ventilation: cable zone
    slot_w, slot_h = 18, 2.5
    vy_start, vy_end = 15, w - 15
    cable_z0 = Z_HAT_TOP + 15
    cable_z1 = Z_DRIVE_BOT - 10
    if cable_z1 > cable_z0:
        for i in range(4):
            vz = cable_z0 + i * (cable_z1 - cable_z0) / 3
            for j in range(2):
                vy = vy_start + j * (vy_end - vy_start - slot_w)
                s.slot(vy, z_to_y(vz), slot_w, slot_h)

    # Ventilation: drive zone
    dz0 = Z_DRIVE_BOT + 20
    dz1 = Z_DRIVE_TOP - 10
    for i in range(6):
        vz = dz0 + i * (dz1 - dz0) / 5
        for j in range(2):
            vy = vy_start + j * (vy_end - vy_start - slot_w)
            s.slot(vy, z_to_y(vz), slot_w, slot_h)

    s.save()


# ============================================================
# PANEL: Drive Comb Rail (x2, front and back of drive group)
# ============================================================

def gen_comb_rail():
    """
    Comb rail: 5mm acrylic. Two identical pieces (front + back of drives).

    Shape: horizontal bar at top with 4 teeth hanging DOWNWARD.
    Each tooth holds one drive — the drive is screwed to the tooth face.
    The bar runs along X (left-to-right). Teeth hang in Z.

    4 teeth for 4 drives. Tooth pitch = HDD_T + DRIVE_GAP.
    20mm face-to-face gap between adjacent drives.
    10mm from outer drive faces to side walls.

    SVG layout (flat for laser cutting):
      X = across drives (enclosure X axis)
      Y = vertical: Y=0 is bar top, Y increases downward (teeth hang down)
    """
    rail_w = INTERIOR_X  # full interior width
    n_teeth = NUM_DRIVES  # 4 teeth, one per drive
    tooth_w = COMB_TOOTH_W  # 20mm wide
    tooth_len = COMB_TOOTH_LEN
    bar_h = COMB_BAR_H
    total_h = COMB_TOTAL_H

    # Tooth pitch: center-to-center distance between adjacent teeth/drives
    tooth_pitch = HDD_T + DRIVE_GAP  # 26.11 + 20 = 46.11mm

    # Position teeth so outer drive faces are DRIVE_EDGE_MARGIN from side walls.
    def tooth_x(i):
        """X position of tooth i (left edge) within the rail."""
        drive_cx = DRIVE_EDGE_MARGIN + HDD_T / 2 + i * tooth_pitch
        return drive_cx - tooth_w / 2

    s = SVG(rail_w + 20, total_h + 20, "07_drive_comb_rail.svg")
    s.text(0, -3, f"DRIVE COMB RAIL (x2) {rail_w:.1f}x{total_h:.1f}mm (5mm acrylic)")

    # Tab dimensions — integrated into the outline path
    tab_len = 8    # how far tab protrudes into side panel slot
    tab_h = 10     # tab height (vertical extent)
    tab_y0 = bar_h / 2 - tab_h / 2  # top of tab
    tab_y1 = tab_y0 + tab_h          # bottom of tab

    # Build outline as a single closed path including tabs
    pts = []
    pts.append((0, 0))                        # top-left of bar
    pts.append((rail_w, 0))                   # top-right of bar
    # Right tab (protrudes right from bar)
    pts.append((rail_w, tab_y0))
    pts.append((rail_w + tab_len, tab_y0))
    pts.append((rail_w + tab_len, tab_y1))
    pts.append((rail_w, tab_y1))
    pts.append((rail_w, bar_h))               # bar right edge, bar bottom

    # Walk left along bar bottom, dipping down for each tooth (right to left)
    for i in range(n_teeth - 1, -1, -1):
        tx = tooth_x(i)
        pts.append((tx + tooth_w, bar_h))      # bar bottom -> right of tooth
        pts.append((tx + tooth_w, total_h))    # tooth bottom-right
        pts.append((tx, total_h))              # tooth bottom-left
        pts.append((tx, bar_h))                # back up to bar bottom

    # Left end of bar + left tab
    pts.append((0, bar_h))
    pts.append((0, tab_y1))
    pts.append((-tab_len, tab_y1))
    pts.append((-tab_len, tab_y0))
    pts.append((0, tab_y0))
    # Path auto-closes back to (0,0)

    s.path(pts)

    # Screw holes in each tooth — 3 holes per tooth, centered in tooth width
    drive_y_bottom = total_h - 5  # 5mm above tooth tip for margin

    for i in range(n_teeth):
        tx = tooth_x(i)
        tooth_cx = tx + tooth_w / 2

        for hz in HDD_SIDE_HOLE_Z:
            hy = drive_y_bottom - hz
            s.circle(tooth_cx, hy, 1.7)  # M3 clearance = 3.4mm dia
            s.circle(tooth_cx, hy, 3.5, style="engrave")  # washer ring

    # Score lines showing drive positions on teeth
    for i in range(n_teeth):
        tx = tooth_x(i)
        drive_cx = tx + tooth_w / 2
        drive_left = drive_cx - HDD_T / 2
        s.rect(drive_left, drive_y_bottom - HDD_L, HDD_T, HDD_L, style="engrave")
        s.text(tx + 1, drive_y_bottom - HDD_L / 2, f"HDD{i+1}", size=3)

    s.save()


# ============================================================
# PANEL: Fan Bracket (internal shelf for fan)
# ============================================================

def gen_fan_bracket():
    bw = INTERIOR_X - 2
    bh = INTERIOR_Y - 2
    s = SVG(bw + 10, bh + 10, "09_fan_bracket.svg")
    s.text(0, -3, f"FAN BRACKET {bw:.0f}x{bh:.0f}mm (3mm acrylic)")

    s.rect(0, 0, bw, bh)

    # Rod holes — vertical rods pass through this bracket
    ri = ROD_INSET - 1  # slightly less inset since bracket is 2mm smaller than interior
    for rcx, rcy in [(ri, ri), (bw - ri, ri), (ri, bh - ri), (bw - ri, bh - ri)]:
        s.circle(rcx, rcy, ROD_HOLE / 2)

    # Fan opening
    cx, cy = bw / 2, bh / 2
    s.circle(cx, cy, 37)

    # Fan screw holes
    fhs = FAN_HOLE_SPACING / 2
    for dx, dy in [(-fhs, -fhs), (fhs, -fhs), (-fhs, fhs), (fhs, fhs)]:
        s.circle(cx + dx, cy + dy, FAN_MOUNT_HOLE / 2)

    s.save()


# ============================================================
# GENERATE ALL + HTML VIEWER
# ============================================================

def gen_html_viewer():
    """Generate an HTML page that displays all SVG panels for visual review."""
    svgs = sorted(f for f in os.listdir(OUTPUT_DIR) if f.endswith('.svg'))
    # Scale ruler SVG: 100mm reference bar with 10mm ticks
    ruler_svg = """<svg xmlns="http://www.w3.org/2000/svg" class="ruler"
      width="110mm" height="12mm" viewBox="0 0 110 12">
  <rect x="5" y="2" width="100" height="4" fill="none" stroke="#000" stroke-width="0.3"/>
  <line x1="5" y1="2" x2="5" y2="10" stroke="#000" stroke-width="0.3"/>
  <text x="5" y="11.5" font-size="2.5" font-family="monospace" text-anchor="middle">0</text>
  <line x1="15" y1="4" x2="15" y2="8" stroke="#000" stroke-width="0.2"/>
  <line x1="25" y1="4" x2="25" y2="8" stroke="#000" stroke-width="0.2"/>
  <line x1="35" y1="4" x2="35" y2="8" stroke="#000" stroke-width="0.2"/>
  <line x1="45" y1="4" x2="45" y2="8" stroke="#000" stroke-width="0.2"/>
  <line x1="55" y1="2" x2="55" y2="10" stroke="#000" stroke-width="0.3"/>
  <text x="55" y="11.5" font-size="2.5" font-family="monospace" text-anchor="middle">50</text>
  <line x1="65" y1="4" x2="65" y2="8" stroke="#000" stroke-width="0.2"/>
  <line x1="75" y1="4" x2="75" y2="8" stroke="#000" stroke-width="0.2"/>
  <line x1="85" y1="4" x2="85" y2="8" stroke="#000" stroke-width="0.2"/>
  <line x1="95" y1="4" x2="95" y2="8" stroke="#000" stroke-width="0.2"/>
  <line x1="105" y1="2" x2="105" y2="10" stroke="#000" stroke-width="0.3"/>
  <text x="105" y="11.5" font-size="2.5" font-family="monospace" text-anchor="middle">100mm</text>
</svg>"""

    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Pi5 NAS Enclosure — Panel Review</title>
<style>
  /* === Screen styles === */
  body { font-family: system-ui, sans-serif; background: #1a1a2e; color: #eee; margin: 2em; }
  h1 { color: #e94560; }
  .panel { background: #16213e; border: 1px solid #0f3460; border-radius: 8px;
           padding: 1.5em; margin: 1.5em 0; }
  .panel h2 { color: #e94560; margin-top: 0; }
  .panel svg:not(.ruler) { background: #fff; border: 1px solid #333; display: block; margin: 1em auto;
               max-width: 100%; height: auto; }
  .dims { color: #aaa; font-size: 0.9em; }
  .summary { background: #0f3460; padding: 1em; border-radius: 8px; margin-bottom: 2em; }
  .summary td { padding: 4px 12px; }
  .summary th { text-align: left; padding: 4px 12px; color: #e94560; }
  .ruler { display: none; }
  .print-note { display: none; }
  .print-btn { background: #e94560; color: #fff; border: none; padding: 10px 24px;
               border-radius: 6px; font-size: 1em; cursor: pointer; margin-bottom: 1em; }
  .print-btn:hover { background: #c73650; }

  /* === Print styles === */
  @media print {
    body { background: #fff; color: #000; margin: 0; padding: 5mm; }
    h1 { color: #000; font-size: 14pt; }
    .panel { background: #fff; border: none; padding: 0; margin: 0;
             page-break-inside: avoid; page-break-after: always; }
    .panel h2 { color: #000; font-size: 12pt; margin-bottom: 2mm; }
    .panel svg:not(.ruler) { border: none; margin: 0; background: #fff;
                 max-width: none; width: auto; height: auto; }
    .summary { background: #fff; border: 1px solid #ccc; }
    .summary th { color: #000; }
    .ruler { display: block; margin: 2mm 0; }
    .print-note { display: block; font-size: 9pt; color: #666; margin-bottom: 3mm; }
    .print-btn { display: none; }
  }
</style>
</head><body>
<h1>Pi5 NAS Acrylic Enclosure — Panel Review</h1>
<button class="print-btn" onclick="window.print()">Print at Actual Size</button>
<p class="print-note">Verify the ruler below measures exactly 100mm. If not, adjust print scale to 100%.</p>
""" + ruler_svg + """
<div class="summary">
<table>
<tr><th>Exterior</th><td>""" + f"{EXT_X:.0f} x {EXT_Y:.0f} x {TOTAL_H:.0f} mm" + """</td></tr>
<tr><th>Interior</th><td>""" + f"{INTERIOR_X} x {INTERIOR_Y} mm" + """</td></tr>
<tr><th>Total Height</th><td>""" + f"{TOTAL_H:.1f} mm ({TOTAL_H/25.4:.1f} in)" + """</td></tr>
<tr><th>Drive Bottom Z</th><td>""" + f"{Z_DRIVE_BOT:.1f} mm from bottom" + """</td></tr>
<tr><th>Assembly</th><td>Vertical M4 rods (top/bottom only) + finger joint tabs (front/back into side)</td></tr>
<tr><th>Panels</th><td>""" + str(len(svgs)) + """ SVG files</td></tr>
</table>
</div>
"""
    for fname in svgs:
        name = fname.replace('.svg', '').replace('_', ' ').lstrip('0123456789 ')
        html += f'<div class="panel">\n<h2>{name}</h2>\n'
        html += f'<p class="print-note">Verify ruler = 100mm. Print at 100% scale (no fit-to-page).</p>\n'
        html += ruler_svg + '\n'
        with open(os.path.join(OUTPUT_DIR, fname)) as f:
            svg_content = f.read()
        html += svg_content + '\n</div>\n'

    html += '</body></html>\n'
    fp = os.path.join(OUTPUT_DIR, 'panel_review.html')
    with open(fp, 'w') as f:
        f.write(html)
    print(f"  panel_review.html")


print("\n=== Generating SVG panels ===\n")
gen_bottom()
gen_top()
gen_front()
gen_back()
gen_side('left')
gen_side('right')
gen_comb_rail()
gen_fan_bracket()
gen_html_viewer()

print(f"\n=== Done! Output: {OUTPUT_DIR} ===")
print(f"  Open panel_review.html in a browser to visually inspect all panels.")
