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

T_WALL = 3.0        # front/back/top panel acrylic thickness
T_SIDE = 5.0        # left/right side and bottom panel acrylic thickness
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
DRIVE_GAP = 19.0       # 19mm face-to-face between adjacent drives for laminar airflow
DRIVE_EDGE_MARGIN = 11.5  # 11.5mm from outer drive face to side wall
CABLE_ZONE_H = 82.0    # 85-3mm; absorbs 3mm from taller Pi5 standoff
PI5_STANDOFF_H = 10.0  # M2.5 standoff under Pi5 (10mm for off-the-shelf availability)
PI5_ENVELOPE_H = 18.0  # Pi5 PCB bottom to top of tallest connector (RJ45, from STEP)
PI5_TO_HAT_GAP = 3.0   # gap from Pi5 USB top to HAT PCB bottom (GPIO seated)
HAT_ENVELOPE_H = 12.25 # HAT PCB bottom to top of tallest connector (from STEP)

# Comb rail — horizontal bar at top with teeth hanging downward
COMB_BAR_H = 12.0      # height of the horizontal bar at top of comb
COMB_TOOTH_W = 20.0    # tooth width (X direction) — wide enough for M3 holes + margin
SCREW_HEAD_CLR = 4.0   # clearance between comb face and front/back panel for screw heads

# Assembly
SIDE_OVERLAP = 3.0 + T_WALL           # 3mm overhang + 3mm slot (front/back panel thickness)

# Finger joints
FINGER_WIDTH = 12.0
MIN_OVERHANG = 3.0   # material between slot and panel edge

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

EXT_X = INTERIOR_X + 2 * T_SIDE      # side panels are 5mm
EXT_Y = INTERIOR_Y + 2 * T_WALL                   # front/back panels are 3mm

# Z-stack (from bottom of enclosure)
Z_BOT_TOP = T_SIDE                                    # bottom panel is 5mm
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
# Note: top panel is T_WALL=3mm
Z_TOP_PANEL = Z_FAN_TOP + 5                     # 5mm clearance above fan to top panel
TOTAL_H = Z_TOP_PANEL + T_WALL

SIDE_H = Z_TOP_PANEL - T_SIDE  # front/back/side panel height (Z=T_SIDE to Z=Z_TOP_PANEL)

# Comb rail: bar top edge at Z_DRIVE_TOP, bar extends downward, teeth below that
# This keeps the bar within the drive zone, leaving fan zone clear above.
COMB_BAR_Z = Z_DRIVE_TOP - COMB_BAR_H  # bar bottom edge = Z_DRIVE_TOP - 12mm
COMB_TOOTH_LEN = HDD_L - COMB_BAR_H - 10  # tooth hangs below bar, leave 10mm at bottom
COMB_TOTAL_H = COMB_BAR_H + COMB_TOOTH_LEN

ROD_INSET = T_SIDE + 2 * ROD_DIA  # rod hole inset from panel edge (past 5mm side panel)

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

def finger_outline(w, h, top='flat', bottom='flat', left='flat', right='flat',
                   depth=T_WALL, lr_depth=None, bot_depth=None, top_depth=None,
                   skip_lr_ends=False):
    """
    Build a closed polygon for a rectangular panel with optional finger joints.
    Each edge: 'tab' = notches recede inward, 'outer_tab' = protrudes outward
    (into mating panel slot), 'flat' = straight.
    Traversal: clockwise starting from top-left.

    depth: default depth (used as fallback).
    top_depth: depth for top edge (defaults to depth).
    bot_depth: depth for bottom edge (defaults to depth).
    lr_depth: depth for left/right edges (defaults to depth).
    skip_lr_ends: skip first/last fingers on left/right edges.
    """
    if lr_depth is None:
        lr_depth = depth
    if bot_depth is None:
        bot_depth = depth
    if top_depth is None:
        top_depth = depth

    def nfingers(length):
        n = max(3, round(length / FINGER_WIDTH))
        if n % 2 == 0:
            n += 1
        return n

    n_w = nfingers(w)
    n_h = nfingers(h)
    fw_w = w / n_w
    fw_h = h / n_h

    def signed_depth(mode, d0):
        """Return signed depth: negative for tab (recedes inward), positive for outer_tab."""
        if mode in ('tab',):
            return -d0
        elif mode in ('outer_tab', 'slot'):
            return d0
        return 0

    def is_finger(i, n, mode, skip_ends):
        """Is position i a finger (not flat)?"""
        if mode == 'flat':
            return False
        if i % 2 != 0:
            return False
        if skip_ends and (i == 0 or i == n - 1):
            return False
        return True

    # Build the outline as one continuous clockwise path.
    # At each corner, the depth of the ending finger on one edge determines
    # where the next edge starts — no backtracking.
    pts = []

    # Determine corner depths: the depth at each corner is determined by
    # whether the adjacent edge ends/starts with a finger.
    # Corner order: TL(0,0), TR(w,0), BR(w,h), BL(0,h)
    # Top edge ends at TR: last finger (i=n_w-1) — always even (n_w is odd)
    # Negated because top edge inward is +y (opposite of signed_depth convention)
    top_d = -signed_depth(top, top_depth) if is_finger(n_w - 1, n_w, top, False) else 0
    # Bottom edge starts at BR: first finger (i=0)
    bot_d_start = signed_depth(bottom, bot_depth) if is_finger(0, n_w, bottom, False) else 0
    # Bottom edge ends at BL: last finger (i=n_w-1)
    bot_d_end = signed_depth(bottom, bot_depth) if is_finger(n_w - 1, n_w, bottom, False) else 0
    # Top edge starts at TL: first finger (i=0)
    top_d_start = -signed_depth(top, top_depth) if is_finger(0, n_w, top, False) else 0

    # --- Top edge: left to right, y=0 ---
    # For the top edge, "inward" is +y (into the panel body).
    # tab = notch inward (+y), outer_tab = protrusion outward (-y).
    # This is opposite of signed_depth's convention, so we negate it.
    for i in range(n_w):
        x0 = i * fw_w
        x1 = (i + 1) * fw_w
        if is_finger(i, n_w, top, False):
            d = -signed_depth(top, top_depth)
            if i == 0:
                # Start at notch depth (left edge will connect here)
                pts.append((x0, d))
            else:
                pts.append((x0, 0))
                pts.append((x0, d))
            if i == n_w - 1:
                # End at notch depth (right edge will connect from here)
                pts.append((x1, d))
            else:
                pts.append((x1, d))
                pts.append((x1, 0))
        else:
            if i == 0 and top_d_start != 0:
                pass  # previous corner handles start
            else:
                pts.append((x0, 0))
            pts.append((x1, 0))

    # --- Right edge: top to bottom, x=w ---
    # If top edge ends with a notch at TR corner, right edge starts at notch depth
    right_start_y = top_d if top_d != 0 else 0
    # If bottom edge starts with a notch at BR corner, right edge stops at notch depth
    right_end_y = h + bot_d_start if bot_d_start != 0 else h
    for i in range(n_h):
        y0 = i * fw_h
        y1 = (i + 1) * fw_h
        if i == 0:
            y0_actual = right_start_y  # adjust first segment to meet top edge notch
        else:
            y0_actual = y0
        if i == n_h - 1:
            y1_actual = right_end_y  # adjust last segment to meet bottom edge notch
        else:
            y1_actual = y1
        if is_finger(i, n_h, right, skip_lr_ends):
            d = signed_depth(right, lr_depth)
            pts.append((w, y0_actual))
            pts.append((w + d, y0_actual))
            pts.append((w + d, y1_actual))
            pts.append((w, y1_actual))
        else:
            pts.append((w, y0_actual))
            pts.append((w, y1_actual))

    # --- Bottom edge: right to left, y=h ---
    for i in range(n_w):
        # i=0 is at the right end (x=w), i=n_w-1 is at the left end (x=0)
        x1 = w - i * fw_w       # start x (right side)
        x0 = w - (i + 1) * fw_w  # end x (left side)
        if is_finger(i, n_w, bottom, False):
            d = signed_depth(bottom, bot_depth)
            if i == 0:
                # Right edge already ended at notch depth — start directly
                pts.append((x1, h + d))
            else:
                pts.append((x1, h))
                pts.append((x1, h + d))
            if i == n_w - 1:
                # End at notch depth — left edge will start from here
                pts.append((x0, h + d))
            else:
                pts.append((x0, h + d))
                pts.append((x0, h))
        else:
            pts.append((x1, h))
            pts.append((x0, h))

    # --- Left edge: bottom to top, x=0 ---
    # If bottom edge ends with a notch at BL corner, left edge starts at notch depth
    left_start_y = h + bot_d_end if bot_d_end != 0 else h
    # If top edge starts with a notch at TL corner, left edge ends at notch depth
    left_end_y = top_d_start if top_d_start != 0 else 0
    for i in range(n_h):
        # i=0 is at the bottom (y=h), i=n_h-1 is at the top (y=0)
        y1 = h - i * fw_h       # start y (bottom)
        y0 = h - (i + 1) * fw_h  # end y (top)
        if i == 0:
            y1_actual = left_start_y  # adjust first segment to meet bottom edge notch
        else:
            y1_actual = y1
        if i == n_h - 1:
            y0_actual = left_end_y  # adjust last segment to meet top edge notch
        else:
            y0_actual = y0
        if is_finger(i, n_h, left, skip_lr_ends):
            d = signed_depth(left, lr_depth)
            pts.append((0, y1_actual))
            pts.append((-d, y1_actual))
            pts.append((-d, y0_actual))
            pts.append((0, y0_actual))
        else:
            pts.append((0, y1_actual))
            pts.append((0, y0_actual))

    # Remove consecutive duplicate points
    clean = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - clean[-1][0]) > 0.001 or abs(p[1] - clean[-1][1]) > 0.001:
            clean.append(p)
    # Remove closing duplicate if first == last
    if len(clean) > 1 and abs(clean[0][0] - clean[-1][0]) < 0.001 and abs(clean[0][1] - clean[-1][1]) < 0.001:
        clean.pop()
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
    Custom outline for top/bottom panels (w=EXT_X, h=INTERIOR_Y).
    - Top/bottom edges: finger protrusions spanning EXT_X (mate with front/back panel notches).
    - Left/right edges: straight (through-slots added separately as rects).
    """
    pts = []
    depth = T_WALL  # protrusions mate with 3mm front/back panels

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
    n_lr = max(3, round(INTERIOR_Y / FINGER_WIDTH))
    if n_lr % 2 == 0:
        n_lr += 1
    fw_lr = INTERIOR_Y / n_lr
    slot_w = T_SIDE  # slot width = side panel thickness (5mm)
    for edge_side in ['left', 'right']:
        if edge_side == 'left':
            slot_x = MIN_OVERHANG
        else:
            slot_x = w - MIN_OVERHANG - slot_w
        for i in range(n_lr):
            if i % 2 == 0:  # tabs are at even indices on side panels
                slot_y = i * fw_lr  # Y=0 = front panel inner face
                svg.rect(slot_x, slot_y, slot_w, fw_lr)


# ============================================================
# PANEL: Bottom
# ============================================================

def gen_bottom():
    w = EXT_X
    h = INTERIOR_Y  # body spans front panel inner face to back panel inner face
    s = SVG(w, h, "01_bottom_panel.svg", margin=T_SIDE + 3)
    s.text(0, -3, f"BOTTOM PANEL {w:.0f}x{h:.0f}mm (5mm)")

    # Custom outline: finger protrusions on top/bottom (front/back mating), straight left/right.
    outline = tb_panel_outline(w, h)
    s.path(outline)

    # Through-slots near left/right edges to receive side panel tabs.
    add_tb_side_slots(s, w, h)

    # Corner rod holes — vertical rods through top+bottom only
    add_rod_holes(s, w, h)

    # Pi5 mounting holes — ports face front panel (Y=0)
    # Pi5 long edge (85mm) runs along Y (front-to-back),
    # short edge (56mm) runs along X (left-right), centered.
    pi_w_on_panel = PI5_W   # 56mm along X (left-right)
    pi_h_on_panel = PI5_L   # 85mm along Y (front-to-back)
    pi_ox = (w - pi_w_on_panel) / 2   # centered left-to-right
    pi_oy = 2                          # port edge near front panel inner face + 2mm clearance
    # Mounting holes: Pi5 native coords have origin at GPIO corner.
    # Native X runs along 85mm (long edge), native Y along 56mm (short edge).
    # After rotation with USB/Eth end at front (Y=0):
    #   panel_x = pi_ox + native_y  (short edge maps to panel X)
    #   panel_y = pi_oy + (PI5_L - native_x)  (long edge reversed: USB end -> front)
    for nx, ny in [(PI5_HOLE_OFFSET_X, PI5_HOLE_OFFSET_Y),
                   (PI5_HOLE_OFFSET_X + PI5_HOLE_SPACING_X, PI5_HOLE_OFFSET_Y),
                   (PI5_HOLE_OFFSET_X, PI5_HOLE_OFFSET_Y + PI5_HOLE_SPACING_Y),
                   (PI5_HOLE_OFFSET_X + PI5_HOLE_SPACING_X, PI5_HOLE_OFFSET_Y + PI5_HOLE_SPACING_Y)]:
        hx = ny                  # native Y -> panel X
        hy = PI5_L - nx          # native X -> panel Y (reversed)
        s.circle(pi_ox + hx, pi_oy + hy, PI5_HOLE_DIA / 2)

    # Dense ventilation grid across entire bottom panel for bottom-to-top airflow.
    # Avoid: side panel slots (near left/right edges), rod holes (corners),
    #        Pi5 mounting holes, and SD card access hole.
    vent_slot_w, vent_slot_h = 22, 3.0
    vent_margin_x = MIN_OVERHANG + T_SIDE + 5  # clear of side panel slots + margin
    vent_margin_y = 8                            # clear of front/back edge + margin
    vent_x0 = vent_margin_x
    vent_x1 = w - vent_margin_x
    vent_y0 = vent_margin_y
    vent_y1 = h - vent_margin_y
    vent_pitch_x = vent_slot_w + 5   # 5mm material between slots
    vent_pitch_y = vent_slot_h + 5   # 5mm material between slots
    n_cols = int((vent_x1 - vent_x0) / vent_pitch_x)
    n_rows = int((vent_y1 - vent_y0) / vent_pitch_y)
    # Center the grid
    grid_w = n_cols * vent_pitch_x - 5
    grid_h = n_rows * vent_pitch_y - 5
    vx_start = vent_x0 + (vent_x1 - vent_x0 - grid_w) / 2
    vy_start = vent_y0 + (vent_y1 - vent_y0 - grid_h) / 2

    # Collect exclusion zones: Pi5 mounting holes (with margin), SD card hole
    pi_holes = []
    for nx, ny in [(PI5_HOLE_OFFSET_X, PI5_HOLE_OFFSET_Y),
                   (PI5_HOLE_OFFSET_X + PI5_HOLE_SPACING_X, PI5_HOLE_OFFSET_Y),
                   (PI5_HOLE_OFFSET_X, PI5_HOLE_OFFSET_Y + PI5_HOLE_SPACING_Y),
                   (PI5_HOLE_OFFSET_X + PI5_HOLE_SPACING_X, PI5_HOLE_OFFSET_Y + PI5_HOLE_SPACING_Y)]:
        hx = pi_ox + ny               # native Y -> panel X
        hy = pi_oy + PI5_L - nx       # native X -> panel Y (reversed)
        pi_holes.append((hx, hy))

    # SD card access hole — SD card is on native X- side, which maps to back (high Y).
    # SD card slot runs along native Y (56mm edge), which maps to panel X.
    sd_slot_x0 = 22.05   # offset along native Y (56mm edge) from GPIO corner
    sd_slot_x1 = 34.0
    sd_w = 14.0     # along panel X (was along native Y)
    sd_h = 20.0     # along panel Y, extends past PCB edge for finger reach
    sd_x = pi_ox + sd_slot_x0 + (sd_slot_x1 - sd_slot_x0 - sd_w) / 2  # centered on slot
    sd_y = pi_oy + pi_h_on_panel - sd_h / 4   # skewed past back edge for finger access

    def overlaps_exclusion(vx, vy):
        for hx, hy in pi_holes:
            if vx < hx + 4 and vx + vent_slot_w > hx - 4 and vy < hy + 4 and vy + vent_slot_h > hy - 4:
                return True
        # Also exclude vents that overlap the SD card access hole (with 2mm margin)
        if (vx < sd_x + sd_w + 2 and vx + vent_slot_w > sd_x - 2 and
                vy < sd_y + sd_h + 2 and vy + vent_slot_h > sd_y - 2):
            return True
        return False

    for col in range(n_cols):
        vx = vx_start + col * vent_pitch_x
        for row in range(n_rows):
            vy = vy_start + row * vent_pitch_y
            if not overlaps_exclusion(vx, vy):
                s.slot(vx, vy, vent_slot_w, vent_slot_h)

    # SD card access hole (dimensions computed above for exclusion zone)
    s.rrect(sd_x, sd_y, sd_w, sd_h, r=3)
    s.text(sd_x, sd_y - 1.5, "SD card", size=2)

    # Score: Pi5 outline (rotated)
    s.rect(pi_ox, pi_oy, pi_w_on_panel, pi_h_on_panel, style="engrave")
    s.text(pi_ox + 2, pi_oy + 10, "Pi5 (ports at front)", size=3)

    s.save()


# ============================================================
# PANEL: Top
# ============================================================

def gen_top():
    w = EXT_X
    h = INTERIOR_Y  # body spans front panel inner face to back panel inner face
    s = SVG(w, h, "02_top_panel.svg", margin=T_WALL + 3)
    s.text(0, -3, f"TOP PANEL {w:.0f}x{h:.0f}mm (3mm)")

    # Custom outline: finger protrusions on top/bottom (front/back mating), straight left/right.
    outline = tb_panel_outline(w, h)
    s.path(outline)

    # Through-slots near left/right edges to receive side panel tabs.
    add_tb_side_slots(s, w, h)

    add_rod_holes(s, w, h)

    # Fan mounts to internal bracket, not top panel — no screw holes here

    # Fan grille — concentric rings of arc slots for maximum airflow + finger safety.
    # Slot width 3mm, ring gap ~4mm, spoke gap ~3mm. All openings < 8mm (finger-safe).
    cx, cy = w / 2, h / 2
    fan_r = 37  # outer radius of grille (74mm diameter)
    slot_w = 3.0  # radial width of each arc slot
    ring_gap = 4.0  # radial material between rings
    ring_pitch = slot_w + ring_gap  # 7mm center-to-center
    spoke_gap = 3.0  # circumferential material between arc slots
    rings = []
    r = 6.0  # start radius (leave small hub in center)
    while r + slot_w <= fan_r:
        rings.append(r)
        r += ring_pitch
    for r_inner in rings:
        r_mid = r_inner + slot_w / 2
        circ = 2 * math.pi * r_mid
        n_slots = max(4, int(circ / (slot_w * 3 + spoke_gap)))
        arc_angle = (2 * math.pi - n_slots * (spoke_gap / r_mid)) / n_slots
        for i in range(n_slots):
            a_start = 2 * math.pi * i / n_slots + (spoke_gap / r_mid) / 2
            # Approximate arc with short line segments
            n_seg = max(4, int(arc_angle * r_mid / 2))
            pts = []
            for seg in range(n_seg + 1):
                a = a_start + arc_angle * seg / n_seg
                for r_off in [r_inner, r_inner + slot_w]:
                    pts.append((cx + r_off * math.cos(a), cy + r_off * math.sin(a)))
            # Build closed path: outer arc forward, inner arc backward
            outer = []
            inner = []
            for seg in range(n_seg + 1):
                a = a_start + arc_angle * seg / n_seg
                outer.append((cx + (r_inner + slot_w) * math.cos(a),
                              cy + (r_inner + slot_w) * math.sin(a)))
                inner.append((cx + r_inner * math.cos(a),
                              cy + r_inner * math.sin(a)))
            path_pts = outer + list(reversed(inner))
            path_pts.append(path_pts[0])  # close
            s.path(path_pts)

    s.save()


# ============================================================
# HELPER: front/back panel outline
# ============================================================

def fb_panel_outline(h, top_depth=T_WALL, bot_depth=T_SIDE):
    """
    Custom outline for front/back panels.
    Body width = INTERIOR_X (fits between side panel inner faces).
    Left/right edges have outer_tabs (T_SIDE deep) that slide into side panel through-slots.
    Top/bottom edges have notches matching the top/bottom panel protrusion pattern
    (which spans EXT_X with finger count based on EXT_X). The notch pattern extends
    into the outer_tab zones at the corners.
    """
    # Body width = distance between bottom panel slot inner edges.
    # The side panel sits in a slot starting at MIN_OVERHANG from the bottom panel edge,
    # so the inner face is at MIN_OVERHANG + T_SIDE from each edge.
    body_w = EXT_X - 2 * (MIN_OVERHANG + T_SIDE)
    tab_w = T_SIDE  # outer_tab extension on each side

    # --- Finger parameters for top/bottom edges (must match tb_panel_outline) ---
    n_tb = max(3, round(EXT_X / FINGER_WIDTH))
    if n_tb % 2 == 0:
        n_tb += 1
    fw_tb = EXT_X / n_tb

    # --- Finger parameters for left/right edges ---
    # The L/R finger pattern is based on SIDE_H (the side panel height),
    # NOT the extended panel height h.  The extra top_ext/bot_ext at each
    # end are flat extensions; tabs stay at their original positions.
    top_ext = T_WALL   # flat extension above finger zone (into 3mm top panel)
    bot_ext = T_SIDE   # flat extension below finger zone (into 5mm bottom panel)
    lr_span = h - top_ext - bot_ext  # = SIDE_H
    n_lr = max(3, round(lr_span / FINGER_WIDTH))
    if n_lr % 2 == 0:
        n_lr += 1
    fw_lr = lr_span / n_lr

    pts = []

    # Notch pattern offset: front/back panel x=0 aligns with bottom panel
    # x = MIN_OVERHANG + T_SIDE (inner edge of side panel slot).
    notch_offset = MIN_OVERHANG + T_SIDE

    # --- Top edge: left to right, y=0 ---
    # Notch pattern uses EXT_X finger spacing, offset so panel x=0 aligns
    # with the bottom panel slot inner edge. Clipped to body width.
    for i in range(n_tb):
        px0 = i * fw_tb - notch_offset
        px1 = (i + 1) * fw_tb - notch_offset
        cpx0 = max(px0, 0)
        cpx1 = min(px1, body_w)
        if cpx1 <= cpx0:
            continue
        if i % 2 == 0:  # notch (inward = +y)
            d = top_depth
            if i == 0:
                pts.append((cpx0, d))
                pts.append((cpx1, d))
                pts.append((cpx1, 0))
            elif i == n_tb - 1:
                pts.append((cpx0, 0))
                pts.append((cpx0, d))
                pts.append((cpx1, d))
            else:
                pts.append((cpx0, 0))
                pts.append((cpx0, d))
                pts.append((cpx1, d))
                pts.append((cpx1, 0))
        else:
            pts.append((cpx0, 0))
            pts.append((cpx1, 0))

    # --- Right edge: top to bottom, x=body_w ---
    # Top edge ended at (body_w, top_depth).
    # Flat extension from top_depth down to top_ext, then finger zone, then
    # flat extension from finger zone end down to h - bot_depth.
    pts.append((body_w, top_ext))  # flat from top_depth to top_ext
    for i in range(n_lr):
        y0 = top_ext + i * fw_lr
        y1 = top_ext + (i + 1) * fw_lr
        if i % 2 == 0 and i != 0 and i != n_lr - 1:
            # outer_tab
            pts.append((body_w, y0))
            pts.append((body_w + tab_w, y0))
            pts.append((body_w + tab_w, y1))
            pts.append((body_w, y1))
        else:
            pts.append((body_w, y0))
            pts.append((body_w, y1))
    # Flat extension from finger zone end to h - bot_depth
    pts.append((body_w, h - bot_depth))

    # --- Bottom edge: right to left, y=h ---
    # Right edge ended at (body_w, h - bot_depth). Clipped to body width.
    for i in range(n_tb - 1, -1, -1):
        px0 = i * fw_tb - notch_offset
        px1 = (i + 1) * fw_tb - notch_offset
        cpx0 = max(px0, 0)
        cpx1 = min(px1, body_w)
        if cpx1 <= cpx0:
            continue
        if i % 2 == 0:  # notch (inward = -y)
            d = bot_depth
            if i == n_tb - 1:
                pts.append((cpx0, h - d))
                pts.append((cpx0, h))
            elif i == 0:
                pts.append((cpx1, h))
                pts.append((cpx1, h - d))
                pts.append((cpx0, h - d))
            else:
                pts.append((cpx1, h))
                pts.append((cpx1, h - d))
                pts.append((cpx0, h - d))
                pts.append((cpx0, h))
        else:
            pts.append((cpx1, h))
            pts.append((cpx0, h))

    # --- Left edge: bottom to top, x=0 ---
    # Bottom edge ended at (0, h - bot_depth).
    # Flat extension from h - bot_depth up to finger zone bottom, then
    # finger zone, then flat extension from finger zone top up to top_depth.
    pts.append((0, top_ext + lr_span))  # flat from h-bot_depth to finger zone bottom
    for i in range(n_lr - 1, -1, -1):
        y0 = top_ext + i * fw_lr
        y1 = top_ext + (i + 1) * fw_lr
        if i % 2 == 0 and i != 0 and i != n_lr - 1:
            # outer_tab
            pts.append((0, y1))
            pts.append((-tab_w, y1))
            pts.append((-tab_w, y0))
            pts.append((0, y0))
        else:
            pts.append((0, y1))
            pts.append((0, y0))
    # Flat extension from finger zone top up to top_depth (to close path)
    pts.append((0, top_depth))

    # Remove consecutive duplicate points
    clean = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - clean[-1][0]) > 0.001 or abs(p[1] - clean[-1][1]) > 0.001:
            clean.append(p)
    if len(clean) > 1 and abs(clean[0][0] - clean[-1][0]) < 0.001 and abs(clean[0][1] - clean[-1][1]) < 0.001:
        clean.pop()
    return clean


# ============================================================
# PANEL: Front (Pi5 USB/Ethernet port side)
# ============================================================

def gen_front():
    w = EXT_X - 2 * (MIN_OVERHANG + T_SIDE)
    h = SIDE_H + T_WALL + T_SIDE  # extend T_WALL into top, T_SIDE into bottom
    s = SVG(w, h, "03_front_panel.svg", margin=T_SIDE + 3)
    s.text(0, -3, f"FRONT PANEL {w:.0f}x{h:.1f}mm (3mm)")

    # Custom outline: body width between slot inner edges, outer_tabs on L/R,
    # top/bottom notches matching tb_panel protrusion pattern (EXT_X span).
    outline = fb_panel_outline(h, top_depth=T_WALL, bot_depth=T_SIDE)
    s.path(outline)

    # No rod holes — vertical rods pass through top/bottom panels only

    # Panel Y axis: Y=0 = top, Y=h = bottom.
    # Panel extends T_SIDE above Z_TOP_PANEL and T_SIDE below T_SIDE.
    # Y=T_SIDE corresponds to Z=Z_TOP_PANEL, Y=h-T_SIDE corresponds to Z=T_SIDE.
    def z_to_y(z_enc):
        return (Z_TOP_PANEL - z_enc) + T_SIDE

    # Pi5 port cutouts — ports face front panel.
    # Pi5 is centered left-to-right in enclosure.
    # Front panel X axis maps to enclosure X axis (offset by body edge).
    # Front panel body_w = EXT_X - 2*(MIN_OVERHANG + T_SIDE) = 179mm.
    # Pi5 center on enclosure X = EXT_X/2. On front panel X = body_w/2.
    body_w = w  # = EXT_X - 2*(MIN_OVERHANG + T_SIDE)
    pi_panel_x = (body_w - PI5_W) / 2  # Pi5 short edge (56mm) centered on panel
    pi_pcb_y = z_to_y(Z_PI5_PCB)  # PCB bottom in panel Y coords

    # Port positions along the 56mm short edge (from STEP model).
    # (name, x_offset_from_pi_left, z_offset_from_pcb_bottom, width, height)
    # Facing the front panel from outside, the Pi5 short edge runs left-right.
    # native_Y=0 is at pi_panel_x, native_Y=56 at pi_panel_x + PI5_W.
    ports = [
        ("GbE",   1.25,   0.45, 17.9, 16.5),
        ("USB3", 21.30,   1.45, 15.6, 17.6),
        ("USB2", 39.10,   1.45, 15.8, 17.6),
        ("HAT",  34.60,  21.55, 20.8,  8.1),
    ]
    for name, px, pz, pw, ph in ports:
        cx = pi_panel_x + px
        cy = pi_pcb_y - pz - ph - 1  # +1mm upward for better fit
        s.rrect(cx, cy, pw, ph, r=1.5)
        s.text(cx, cy - 1.5, name, size=2)

    # DC barrel jack — 8mm hole, 17mm to the left of Pi5 ports
    dc_x = pi_panel_x - 17  # 17mm left of Pi5 left edge
    dc_y = z_to_y(T_SIDE + 15)  # 15mm above bottom panel top
    s.circle(dc_x, dc_y, 4.0)
    s.text(dc_x + 6, dc_y + 1, "DC 12V", size=2)

    # (drive zone score line removed — not needed for production)

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
# PANEL: Back (DC jack + vents, no Pi5 port access)
# ============================================================

def gen_back():
    w = EXT_X - 2 * (MIN_OVERHANG + T_SIDE)
    h = SIDE_H + T_WALL + T_SIDE  # extend T_WALL into top, T_SIDE into bottom
    s = SVG(w, h, "04_back_panel.svg", margin=T_SIDE + 3)
    s.text(0, -3, f"BACK PANEL {w:.0f}x{h:.1f}mm (3mm)")

    # Custom outline: body width between slot inner edges, outer_tabs on L/R,
    # top/bottom notches matching tb_panel protrusion pattern (EXT_X span).
    outline = fb_panel_outline(h, top_depth=T_WALL, bot_depth=T_SIDE)
    s.path(outline)

    # No rod holes — vertical rods pass through top/bottom panels only

    # Panel Y axis: Y=0 = top, Y=h = bottom.
    # Panel extends T_SIDE above Z_TOP_PANEL and T_SIDE below T_SIDE.
    def z_to_y(z_enc):
        return (Z_TOP_PANEL - z_enc) + T_SIDE

    body_w = w  # back panel body width

    # ---- "pi-nas" italic logo, engraved, centered at ~1/4 from top ----
    # Each glyph defined as a list of strokes in a 1.0×1.0 unit cell.
    # Italic slant applied via shear: x' = x + slant * (1 - y)
    SLANT = 0.18  # italic shear factor

    # All lowercase glyphs: x-height region 0.25–0.75, descenders go below 0.75.
    # Each glyph is a list of strokes in a 1.0×1.0 unit cell.
    glyphs = {
        'p': [  # stem with descender + bowl
            [(0.25, 0.25), (0.10, 0.95)],          # stem (x-height to descender)
            [(0.25, 0.25), (0.55, 0.25)],           # top bar
            [(0.55, 0.25), (0.78, 0.30)],           # top-right curve
            [(0.78, 0.30), (0.82, 0.42)],           # right side upper
            [(0.82, 0.42), (0.78, 0.55)],           # right side lower
            [(0.78, 0.55), (0.55, 0.60)],           # bottom-right curve
            [(0.55, 0.60), (0.20, 0.60)],           # bottom bar back to stem
        ],
        'i': [  # vertical stroke + dot
            [(0.35, 0.25), (0.25, 0.75)],           # stem
            [(0.42, 0.08), (0.40, 0.15)],           # dot
        ],
        '-': [  # horizontal dash
            [(0.15, 0.45), (0.75, 0.45)],           # dash
        ],
        'n': [  # two verticals + arch
            [(0.25, 0.25), (0.15, 0.75)],           # left stem
            [(0.25, 0.40), (0.45, 0.25)],           # arch up
            [(0.45, 0.25), (0.65, 0.25)],           # arch top
            [(0.65, 0.25), (0.75, 0.40)],           # arch down
            [(0.75, 0.40), (0.65, 0.75)],           # right stem
        ],
        'a': [  # bowl + stem
            [(0.70, 0.25), (0.50, 0.25)],           # top bar
            [(0.50, 0.25), (0.25, 0.35)],           # left curve top
            [(0.25, 0.35), (0.20, 0.50)],           # left side
            [(0.20, 0.50), (0.25, 0.65)],           # left curve bottom
            [(0.25, 0.65), (0.50, 0.75)],           # bottom curve
            [(0.50, 0.75), (0.65, 0.70)],           # bottom right
            [(0.78, 0.25), (0.62, 0.75)],           # right stem
        ],
        's': [  # s-curve
            [(0.75, 0.30), (0.55, 0.25)],           # top-right to top
            [(0.55, 0.25), (0.30, 0.28)],           # top to top-left
            [(0.30, 0.28), (0.22, 0.38)],           # top-left curve
            [(0.22, 0.38), (0.35, 0.48)],           # to middle
            [(0.35, 0.48), (0.60, 0.55)],           # middle cross
            [(0.60, 0.55), (0.68, 0.65)],           # bottom-right curve
            [(0.68, 0.65), (0.55, 0.75)],           # to bottom
            [(0.55, 0.75), (0.30, 0.72)],           # bottom to bottom-left
            [(0.30, 0.72), (0.15, 0.65)],           # bottom-left
        ],
    }

    logo_text = "pi-nas"
    char_h = 30.0       # glyph cell height in mm
    char_w = 18.0       # glyph cell width in mm
    char_gap = 3.0      # gap between glyphs
    logo_w = len(logo_text) * char_w + (len(logo_text) - 1) * char_gap
    logo_x0 = (body_w - logo_w) / 2
    logo_y0 = h * 0.25 - char_h / 2   # centered at 1/4 from top

    # Bold weight: draw each stroke 3 times with small perpendicular offsets
    BOLD_OFFSETS = [-0.6, 0.0, 0.6]  # mm offset from center line

    for ci, ch in enumerate(logo_text):
        if ch not in glyphs:
            continue
        cx = logo_x0 + ci * (char_w + char_gap)
        cy = logo_y0
        for stroke in glyphs[ch]:
            # Compute the base points (with italic shear)
            base_pts = []
            for ux, uy in stroke:
                sx = ux * char_w + SLANT * (1.0 - uy) * char_h
                sy = uy * char_h
                base_pts.append((cx + sx, cy + sy))
            # For each bold offset, shift perpendicular to the overall stroke direction
            if len(base_pts) >= 2:
                dx = base_pts[-1][0] - base_pts[0][0]
                dy = base_pts[-1][1] - base_pts[0][1]
                length = math.hypot(dx, dy)
                if length > 0:
                    # Perpendicular unit vector
                    nx = -dy / length
                    ny = dx / length
                else:
                    nx, ny = 0, 0
            else:
                nx, ny = 0, 0
            for off in BOLD_OFFSETS:
                pts = [(px + nx * off, py + ny * off) for px, py in base_pts]
                s.path(pts, closed=False, style="engrave")

    s.save()


# ============================================================
# PANEL: Side (left and right are mirrors)
# ============================================================

def gen_side(side='left'):
    # Side panel extends SIDE_OVERLAP past front and back panels
    w = INTERIOR_Y + 2 * SIDE_OVERLAP  # central INTERIOR_Y + wings to wrap around front/back
    h = SIDE_H
    idx = "05" if side == 'left' else "06"
    s = SVG(w, h, f"{idx}_{side}_side_panel.svg", margin=T_SIDE + 3)
    s.text(0, -3, f"{side.upper()} SIDE {w:.1f}x{h:.1f}mm (5mm)")

    # Custom outline: top/bottom edges have tabs in the central EXT_Y region
    # (mating with top/bottom panel slots), with flat SIDE_OVERLAP wings on each end.
    # Left/right edges are FLAT — interlocking with front/back is via through-slots in the face.
    def side_outline():
        pts = []
        n_tb = max(3, round(INTERIOR_Y / FINGER_WIDTH))
        if n_tb % 2 == 0:
            n_tb += 1
        fw = INTERIOR_Y / n_tb
        top_depth = T_WALL   # tabs into 3mm top panel
        bot_depth = T_SIDE   # tabs into 5mm bottom panel

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
                pts.append((x0, -top_depth))
                pts.append((x1, -top_depth))
                pts.append((x1, 0))
            else:
                pts.append((x0, 0))
                pts.append((x1, 0))
        # Right wing (flat)
        pts.append((SIDE_OVERLAP + INTERIOR_Y, 0))
        pts.append((w, 0))

        # Right edge: top to bottom (flat)
        pts.append((w, 0))
        pts.append((w, h))

        # Bottom edge: right to left, y=h
        # Right wing (flat)
        pts.append((w, h))
        pts.append((SIDE_OVERLAP + INTERIOR_Y, h))
        # Central tabs
        for i in range(n_tb - 1, -1, -1):
            x0 = SIDE_OVERLAP + i * fw
            x1 = SIDE_OVERLAP + (i + 1) * fw
            if i % 2 == 0:  # tab — protrudes downward (positive y)
                pts.append((x1, h))
                pts.append((x1, h + bot_depth))
                pts.append((x0, h + bot_depth))
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
    tab_depth = T_WALL  # front/back panels are 3mm, so through-slots are 3mm wide
    slot_w = tab_depth
    for edge_side in ['left', 'right']:
        # Place slot so outer edge is exactly MIN_OVERHANG from the panel edge
        if edge_side == 'left':
            slot_x = MIN_OVERHANG
        else:
            slot_x = w - MIN_OVERHANG - slot_w
        for i in range(n_fingers):
            if i % 2 == 0:  # tabs are at even indices on front/back panels
                # Skip first and last finger — too close to top/bottom edges
                # where the top/bottom panel finger joint slots are
                if i == 0 or i == n_fingers - 1:
                    continue
                slot_y = i * fw
                s.rect(slot_x, slot_y, slot_w, fw)

    # Side panel Y axis: Y=0 = top (Z=Z_TOP_PANEL), Y=SIDE_H = bottom (Z=T_SIDE)
    # To convert enclosure Z to side panel Y: panel_y = Z_TOP_PANEL - enclosure_z
    def z_to_y(z_enc):
        return Z_TOP_PANEL - z_enc

    # Pi5 port cutouts are on the front panel (ports face front).
    # No port cutouts on side panels.

    # Comb rail mounting slots — two rails (front + back of drives)
    # X on side panel = SIDE_OVERLAP + (enclosure Y position - T_WALL)
    rail_front_y = T_WALL + SCREW_HEAD_CLR + T_BRACKET / 2
    rail_back_y = EXT_Y - T_WALL - SCREW_HEAD_CLR - T_BRACKET / 2

    tab_slot_w = T_BRACKET  # 5mm rail, snug fit
    tab_slot_h = 10.3  # matches tab_h=10 + clearance
    # Comb bar center Z in enclosure = COMB_BAR_Z + COMB_BAR_H/2
    bar_center_y = z_to_y(COMB_BAR_Z + COMB_BAR_H / 2)
    for rail_y in [rail_front_y, rail_back_y]:
        slot_x = SIDE_OVERLAP + (rail_y - T_WALL) - tab_slot_w / 2
        slot_y = bar_center_y - tab_slot_h / 2
        s.rect(slot_x, slot_y, tab_slot_w, tab_slot_h)

    # Ventilation slots — 3 columns placed between the comb rail bracket slots
    slot_w_v, slot_h_v = 18, 2.5
    # Bracket exclusion zones are near x=8–15 and x=117–124.
    # Place 3 vent columns in the clear zone between brackets.
    bracket_front_x = SIDE_OVERLAP + (rail_front_y - T_WALL) + tab_slot_w / 2 + 2
    bracket_back_x = SIDE_OVERLAP + (rail_back_y - T_WALL) - tab_slot_w / 2 - 2
    vent_zone_w = bracket_back_x - bracket_front_x - slot_w_v
    vent_cols = [bracket_front_x + j * vent_zone_w / 2 for j in range(3)]

    # Cable zone
    cable_z0 = Z_HAT_TOP + 15
    cable_z1 = Z_DRIVE_BOT - 10
    if cable_z1 > cable_z0:
        for i in range(4):
            vz = cable_z0 + i * (cable_z1 - cable_z0) / 3
            for vx in vent_cols:
                s.slot(vx, z_to_y(vz), slot_w_v, slot_h_v)

    # Drive zone
    dz0 = Z_DRIVE_BOT + 20
    dz1 = Z_DRIVE_TOP - 10
    for i in range(6):
        vz = dz0 + i * (dz1 - dz0) / 5
        for vx in vent_cols:
            s.slot(vx, z_to_y(vz), slot_w_v, slot_h_v)

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
    rail_w = EXT_X - 2 * (MIN_OVERHANG + T_SIDE)  # fit between side panel inner faces
    n_teeth = NUM_DRIVES  # 4 teeth, one per drive
    tooth_w = COMB_TOOTH_W  # 20mm wide
    tooth_len = COMB_TOOTH_LEN
    bar_h = COMB_BAR_H
    total_h = COMB_TOTAL_H

    # Tooth pitch: center-to-center distance between adjacent teeth/drives
    tooth_pitch = HDD_T + DRIVE_GAP  # 26.11 + 19 = 45.11mm

    # Position teeth centered in rail. Edge margin derived from rail width.
    edge_margin = (rail_w - DRIVE_GROUP_W) / 2  # ~7.28mm per side
    def tooth_x(i):
        """X position of tooth i (left edge) within the rail."""
        drive_cx = edge_margin + HDD_T / 2 + i * tooth_pitch
        return drive_cx - tooth_w / 2 - 7  # shifted 7mm left (asymmetric rail)

    s = SVG(rail_w + 20, total_h + 20, "07_drive_comb_rail.svg")
    s.text(0, -3, f"DRIVE COMB RAIL (x2) {rail_w:.1f}x{total_h:.1f}mm (5mm acrylic)")

    # Tab dimensions — integrated into the outline path
    tab_len = T_SIDE  # how far tab protrudes into side panel slot (match panel thickness)
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
    drive_y_bottom = total_h - 2 + 11  # shifted 11mm toward tooth tips (drives drop in enclosure)

    for i in range(n_teeth):
        tx = tooth_x(i)
        tooth_cx = tx + tooth_w / 2  # centered in tooth

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
    bw = EXT_X - 2 * (MIN_OVERHANG + T_SIDE) - 2  # fit between side panel inner faces with 2mm clearance
    bh = INTERIOR_Y - 2
    s = SVG(bw + 10, bh + 10, "09_fan_bracket.svg")
    s.text(0, -3, f"FAN BRACKET {bw:.0f}x{bh:.0f}mm (5mm acrylic)")

    s.rect(0, 0, bw, bh)

    # Rod holes — must align with top/bottom panel rod holes.
    # Top/bottom panels: holes at ROD_INSET from panel edges (EXT_X × INTERIOR_Y).
    # Bracket origin in enclosure coords: X = MIN_OVERHANG + T_SIDE + 1, Y = 1.
    bracket_ox = MIN_OVERHANG + T_SIDE + 1  # bracket left edge in enclosure X
    bracket_oy = 1                           # bracket front edge in enclosure Y
    # Top/bottom panel rod positions in enclosure coords
    rod_positions = [(ROD_INSET, ROD_INSET),
                     (EXT_X - ROD_INSET, ROD_INSET),
                     (ROD_INSET, INTERIOR_Y - ROD_INSET),
                     (EXT_X - ROD_INSET, INTERIOR_Y - ROD_INSET)]
    for rx, ry in rod_positions:
        bx = rx - bracket_ox
        by = ry - bracket_oy
        s.circle(bx, by, ROD_HOLE / 2)

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
