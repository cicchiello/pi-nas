#!/usr/bin/env python3
"""
Nest individual panel SVGs onto two Ponoko-ready sheet SVGs:
  - sheet_3mm.svg  (P3: 790×384mm) — front, back, top panels
  - sheet_5mm.svg  (P3: 790×384mm) — bottom, left/right sides, 2× comb rail, fan bracket

Reads the per-panel SVGs from svg_output/, strips text labels,
computes bounding boxes from actual geometry to determine margins,
and re-emits all geometry at the correct offsets on each sheet.

Ponoko conventions:
  - Stroke colour: red (#ff0000) = cut, blue (#0000ff) = engrave/score
  - Stroke width: 0.01mm
  - Units: mm
  - No fill on any path
"""

import os
import re
import xml.etree.ElementTree as ET

SVG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "svg_output")

# Ponoko P3 sheet
SHEET_W = 790.0
SHEET_H = 384.0

# Spacing between parts on the sheet
GAP = 3.0

# Ponoko stroke width
STROKE_W = "0.01"

# SVG namespace
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)


def _parse_path_coords(d):
    """Extract all (x, y) coordinate pairs from an SVG path d-string."""
    coords = []
    tokens = d.replace(",", " ").split()
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("M", "L"):
            coords.append((float(tokens[i + 1]), float(tokens[i + 2])))
            i += 3
        elif tok == "Z":
            i += 1
        else:
            try:
                x = float(tok)
                y = float(tokens[i + 1])
                coords.append((x, y))
                i += 2
            except (ValueError, IndexError):
                i += 1
    return coords


def _element_bbox(tag, attribs):
    """Return (min_x, min_y, max_x, max_y) for a single SVG element."""
    if tag == "rect":
        x = float(attribs["x"])
        y = float(attribs["y"])
        w = float(attribs["width"])
        h = float(attribs["height"])
        return (x, y, x + w, y + h)
    elif tag == "circle":
        cx = float(attribs["cx"])
        cy = float(attribs["cy"])
        r = float(attribs["r"])
        return (cx - r, cy - r, cx + r, cy + r)
    elif tag == "path":
        coords = _parse_path_coords(attribs["d"])
        if not coords:
            return None
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        return (min(xs), min(ys), max(xs), max(ys))
    return None


def parse_panel_svg(filename, keep_engrave=False):
    """Parse a panel SVG file and return its elements shifted so the bounding box starts at (0,0).

    Args:
        filename: SVG filename in SVG_DIR.
        keep_engrave: If False, strip all blue (engrave) elements. If True, keep them.

    Returns (content_w, content_h, elements) where elements is a list of
    (tag, attribs) tuples with coordinates relative to (0,0).
    """
    path = os.path.join(SVG_DIR, filename)
    tree = ET.parse(path)
    root = tree.getroot()

    # Collect non-text elements and compute bounding box (from CUT elements only)
    raw_elements = []
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    for el in root:
        tag = el.tag.replace(f"{{{NS}}}", "")
        if tag == "text":
            continue
        if not isinstance(el.tag, str):
            continue

        attribs = dict(el.attrib)

        # Optionally strip engrave (blue) elements
        stroke = attribs.get("stroke", "").lower()
        is_engrave = stroke == "#0000ff"
        if is_engrave and not keep_engrave:
            continue

        bbox = _element_bbox(tag, attribs)
        if bbox is None:
            continue

        raw_elements.append((tag, attribs))
        # Bounding box computed from CUT elements only (red) so part size is accurate
        if not is_engrave:
            min_x = min(min_x, bbox[0])
            min_y = min(min_y, bbox[1])
            max_x = max(max_x, bbox[2])
            max_y = max(max_y, bbox[3])

    content_w = max_x - min_x
    content_h = max_y - min_y

    # Shift all elements so bounding box starts at (0, 0)
    elements = []
    for tag, attribs in raw_elements:
        a = dict(attribs)
        if tag == "rect":
            a["x"] = str(float(a["x"]) - min_x)
            a["y"] = str(float(a["y"]) - min_y)
        elif tag == "circle":
            a["cx"] = str(float(a["cx"]) - min_x)
            a["cy"] = str(float(a["cy"]) - min_y)
        elif tag == "path":
            a["d"] = _shift_path_d(a["d"], -min_x, -min_y)

        # Normalize stroke width for Ponoko
        a["stroke-width"] = STROKE_W
        elements.append((tag, a))

    return content_w, content_h, elements


def _shift_path_d(d, dx, dy):
    """Shift all coordinates in an SVG path d-string by (dx, dy).
    Handles M and L commands with absolute coordinates."""
    tokens = d.replace(",", " ").split()
    out = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("M", "L"):
            out.append(tok)
            x = float(tokens[i + 1]) + dx
            y = float(tokens[i + 2]) + dy
            out.append(f"{x:.3f}")
            out.append(f"{y:.3f}")
            i += 3
        elif tok == "Z":
            out.append("Z")
            i += 1
        else:
            try:
                x = float(tok) + dx
                y = float(tokens[i + 1]) + dy
                out.append(f"{x:.3f}")
                out.append(f"{y:.3f}")
                i += 2
            except (ValueError, IndexError):
                out.append(tok)
                i += 1
    return " ".join(out)


def _rotate_elements_90cw(elements, orig_w, orig_h):
    """Rotate elements 90° clockwise around the center of (orig_w × orig_h) bounding box.
    Maps (x, y) -> (orig_h - y, x). New bounding box is (orig_h × orig_w)."""
    rotated = []
    for tag, attribs in elements:
        a = dict(attribs)
        if tag == "rect":
            x = float(a["x"])
            y = float(a["y"])
            w = float(a["width"])
            h = float(a["height"])
            # Top-left (x,y) -> (orig_h - y - h, x)
            a["x"] = str(orig_h - y - h)
            a["y"] = str(x)
            a["width"] = str(h)
            a["height"] = str(w)
        elif tag == "circle":
            cx = float(a["cx"])
            cy = float(a["cy"])
            a["cx"] = str(orig_h - cy)
            a["cy"] = str(cx)
        elif tag == "path":
            a["d"] = _rotate_path_d_90cw(a["d"], orig_h)
        rotated.append((tag, a))
    return rotated


def _rotate_path_d_90cw(d, orig_h):
    """Rotate path coordinates 90° CW: (x,y) -> (orig_h - y, x)."""
    tokens = d.replace(",", " ").split()
    out = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("M", "L"):
            out.append(tok)
            x = float(tokens[i + 1])
            y = float(tokens[i + 2])
            out.append(f"{orig_h - y:.3f}")
            out.append(f"{x:.3f}")
            i += 3
        elif tok == "Z":
            out.append("Z")
            i += 1
        else:
            try:
                x = float(tok)
                y = float(tokens[i + 1])
                out.append(f"{orig_h - y:.3f}")
                out.append(f"{x:.3f}")
                i += 2
            except (ValueError, IndexError):
                out.append(tok)
                i += 1
    return " ".join(out)


def _rotate_elements_180(elements, orig_w, orig_h):
    """Rotate elements 180° around the center of (orig_w × orig_h) bounding box.
    Maps (x, y) -> (orig_w - x, orig_h - y). Bounding box stays (orig_w × orig_h)."""
    rotated = []
    for tag, attribs in elements:
        a = dict(attribs)
        if tag == "rect":
            x = float(a["x"])
            y = float(a["y"])
            w = float(a["width"])
            h = float(a["height"])
            a["x"] = str(orig_w - x - w)
            a["y"] = str(orig_h - y - h)
        elif tag == "circle":
            cx = float(a["cx"])
            cy = float(a["cy"])
            a["cx"] = str(orig_w - cx)
            a["cy"] = str(orig_h - cy)
        elif tag == "path":
            a["d"] = _rotate_path_d_180(a["d"], orig_w, orig_h)
        rotated.append((tag, a))
    return rotated


def _rotate_path_d_180(d, orig_w, orig_h):
    """Rotate path coordinates 180°: (x,y) -> (orig_w - x, orig_h - y)."""
    tokens = d.replace(",", " ").split()
    out = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("M", "L"):
            out.append(tok)
            x = float(tokens[i + 1])
            y = float(tokens[i + 2])
            out.append(f"{orig_w - x:.3f}")
            out.append(f"{orig_h - y:.3f}")
            i += 3
        elif tok == "Z":
            out.append("Z")
            i += 1
        else:
            try:
                x = float(tok)
                y = float(tokens[i + 1])
                out.append(f"{orig_w - x:.3f}")
                out.append(f"{orig_h - y:.3f}")
                i += 2
            except (ValueError, IndexError):
                out.append(tok)
                i += 1
    return " ".join(out)


def _offset_elements(elements, dx, dy):
    """Return a new list of elements with all coordinates shifted by (dx, dy)."""
    shifted = []
    for tag, attribs in elements:
        a = dict(attribs)
        if tag == "rect":
            a["x"] = str(float(a["x"]) + dx)
            a["y"] = str(float(a["y"]) + dy)
        elif tag == "circle":
            a["cx"] = str(float(a["cx"]) + dx)
            a["cy"] = str(float(a["cy"]) + dy)
        elif tag == "path":
            a["d"] = _shift_path_d(a["d"], dx, dy)
        shifted.append((tag, a))
    return shifted


def _fmt(v):
    """Format a float for SVG output."""
    return f"{v:.3f}".rstrip("0").rstrip(".")


def write_sheet_svg(filename, sheet_w, sheet_h, all_elements, part_labels):
    """Write a Ponoko-ready sheet SVG."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{_fmt(sheet_w)}mm" height="{_fmt(sheet_h)}mm" '
        f'viewBox="0 0 {_fmt(sheet_w)} {_fmt(sheet_h)}">',
        f'<!-- Ponoko sheet: {_fmt(sheet_w)}x{_fmt(sheet_h)}mm. Red=cut, Blue=engrave. -->',
    ]

    # Part labels as light grey text (won't be cut, just for reference)
    for label, x, y in part_labels:
        lines.append(f'  <text x="{_fmt(x)}" y="{_fmt(y - 2)}" '
                      f'font-size="4" fill="#cccccc" font-family="monospace">{label}</text>')

    for tag, attribs in all_elements:
        attr_str = " ".join(f'{k}="{v}"' for k, v in attribs.items())
        lines.append(f"  <{tag} {attr_str}/>")

    lines.append("</svg>")

    out_path = os.path.join(SVG_DIR, filename)
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  {filename} ({_fmt(sheet_w)}x{_fmt(sheet_h)}mm)")
    return out_path


def nest_3mm_sheet():
    """Nest 3mm parts: front, back, top panels on a P3 sheet.

    Layout: front and back side by side (tall), top panel rotated 90° CW
    and placed to the right. Rotating the top panel (195×126 -> 126×195)
    lets it fit beside the tall panels, reducing total sheet width.
    """
    print("\n=== 3mm Sheet (P3: 790x384mm) ===")

    front_w, front_h, front_els = parse_panel_svg("03_front_panel.svg")
    back_w, back_h, back_els = parse_panel_svg("04_back_panel.svg", keep_engrave=True)
    top_w, top_h, top_els = parse_panel_svg("02_top_panel.svg")

    print(f"  Front: {_fmt(front_w)}x{_fmt(front_h)}mm")
    print(f"  Back:  {_fmt(back_w)}x{_fmt(back_h)}mm")
    print(f"  Top:   {_fmt(top_w)}x{_fmt(top_h)}mm (rotating 90° CW -> {_fmt(top_h)}x{_fmt(top_w)})")

    # Rotate top panel 90° CW: (top_w × top_h) -> (top_h × top_w)
    top_els_rot = _rotate_elements_90cw(top_els, top_w, top_h)
    top_rot_w, top_rot_h = top_h, top_w  # swapped

    # Positions (top-left corner of each part)
    x_front = 0
    x_back = front_w + GAP
    x_top = x_back + back_w + GAP
    y_all = 0

    total_w = x_top + top_rot_w
    total_h = max(front_h, back_h, top_rot_h)

    if total_w > SHEET_W or total_h > SHEET_H:
        print(f"  WARNING: Parts don't fit on P3! Need {_fmt(total_w)}x{_fmt(total_h)}mm")

    all_els = []
    all_els.extend(_offset_elements(front_els, x_front, y_all))
    all_els.extend(_offset_elements(back_els, x_back, y_all))
    all_els.extend(_offset_elements(top_els_rot, x_top, y_all))

    labels = [
        ("FRONT (3mm)", x_front, y_all),
        ("BACK (3mm)", x_back, y_all),
        ("TOP (3mm, rotated)", x_top, y_all),
    ]

    write_sheet_svg("sheet_3mm.svg", total_w, total_h, all_els, labels)


def nest_5mm_sheet():
    """Nest 5mm parts on a P3 sheet.

    Layout (per user's physical arrangement):
      Column 1: left side + right side (side by side, tall)
      Column 2: interleaved comb rails (vertical, teeth down) at top,
                fan bracket below
      Column 3: bottom panel (original orientation) top-aligned,
                right of combs, above fan bracket
    """
    print("\n=== 5mm Sheet (P3: 790x384mm) ===")

    bottom_w, bottom_h, bottom_els = parse_panel_svg("01_bottom_panel.svg")
    left_w, left_h, left_els = parse_panel_svg("05_left_side_panel.svg")
    right_w, right_h, right_els = parse_panel_svg("06_right_side_panel.svg")
    comb_w, comb_h, comb_els = parse_panel_svg("07_drive_comb_rail.svg")
    fan_w, fan_h, fan_els = parse_panel_svg("09_fan_bracket.svg")

    print(f"  Bottom:     {_fmt(bottom_w)}x{_fmt(bottom_h)}mm")
    print(f"  Left side:  {_fmt(left_w)}x{_fmt(left_h)}mm")
    print(f"  Right side: {_fmt(right_w)}x{_fmt(right_h)}mm")
    print(f"  Comb rail:  {_fmt(comb_w)}x{_fmt(comb_h)}mm (x2, interleaved)")
    print(f"  Fan bracket:{_fmt(fan_w)}x{_fmt(fan_h)}mm")

    # Column 1: two side panels side by side
    x_left = 0
    y_left = 0
    x_right = left_w + GAP
    y_right = 0
    col1_w = left_w + GAP + right_w
    col1_h = left_h  # both sides same height

    # --- Build interleaved comb assembly in local coords ---
    # Rail 1: normal (bar at top, teeth down)
    # Rail 2: rotated 180° + shifted in X and Y to interleave
    bar_h = 12.0  # COMB_BAR_H from generate_panels.py
    offset_y2 = bar_h + GAP  # vertical shift for rail 2
    interleaved_h = offset_y2 + comb_h
    comb2_dx = 4.0  # horizontal offset so teeth nest into gaps
    assy_w = comb_w + comb2_dx
    assy_h = interleaved_h

    comb2_els = _rotate_elements_180(comb_els, comb_w, comb_h)

    # Combine both rails into one assembly (local coords)
    assy_els = []
    assy_els.extend(_offset_elements(comb_els, 0, 0))
    assy_els.extend(_offset_elements(comb2_els, comb2_dx + 4.5, offset_y2))

    print(f"  Interleaved combs: {_fmt(assy_w)}x{_fmt(assy_h)}mm "
          f"(saved {_fmt(comb_h + GAP + comb_h - assy_h)}mm vs stacked)")

    # Rotate the entire assembly 90° CW
    assy_rot_els = _rotate_elements_90cw(assy_els, assy_w, assy_h)
    assy_rot_w = assy_h   # old height -> new width
    assy_rot_h = assy_w   # old width -> new height
    print(f"  Combs rotated 90°: {_fmt(assy_rot_w)}x{_fmt(assy_rot_h)}mm")

    # Column 2: rotated comb assembly at top, fan bracket below, bottom panel below
    x_col2 = col1_w + GAP
    y_combs = 0
    y_fan = col1_h - fan_h
    x_fan = x_col2
    bottom_rot_els = _rotate_elements_90cw(bottom_els, bottom_w, bottom_h)
    bottom_rot_w = bottom_h   # 126mm
    bottom_rot_h = bottom_w   # 195mm
    x_bottom = x_fan + fan_w + GAP - 23.0
    y_bottom = 0

    total_w = max(x_col2 + assy_rot_w, x_bottom + bottom_rot_w, x_fan + fan_w)
    total_h = max(col1_h, y_fan + fan_h, y_bottom + bottom_rot_h)

    if total_w > SHEET_W or total_h > SHEET_H:
        print(f"  WARNING: Parts don't fit on P3! Need {_fmt(total_w)}x{_fmt(total_h)}mm")

    print(f"  sheet_5mm.svg ({_fmt(total_w)}x{_fmt(total_h)}mm)")

    all_els = []
    all_els.extend(_offset_elements(left_els, x_left, y_left))
    all_els.extend(_offset_elements(right_els, x_right, y_right))
    all_els.extend(_offset_elements(assy_rot_els, x_col2, y_combs))
    all_els.extend(_offset_elements(fan_els, x_fan, y_fan))
    all_els.extend(_offset_elements(bottom_rot_els, x_bottom, y_bottom))

    labels = [
        ("LEFT SIDE (5mm)", x_left, y_left),
        ("RIGHT SIDE (5mm)", x_right, y_right),
        ("COMB RAILS (5mm, interleaved+90°)", x_col2, y_combs),
        ("FAN BRACKET (5mm)", x_fan, y_fan),
        ("BOTTOM (5mm, 90\u00b0)", x_bottom, y_bottom),
    ]

    write_sheet_svg("sheet_5mm.svg", total_w, total_h, all_els, labels)


def svg_to_dxf(svg_filename):
    """Convert a Ponoko sheet SVG to DXF (R12 format).

    Reads the SVG, extracts geometry, and writes a minimal DXF with:
      - Red elements on layer 'CUT'
      - Blue elements on layer 'ENGRAVE'
    Coordinates are in mm. Y-axis is flipped (SVG Y-down -> DXF Y-up).
    """
    svg_path = os.path.join(SVG_DIR, svg_filename)
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Get sheet height for Y-flip
    vb = root.get("viewBox", "").split()
    if len(vb) == 4:
        sheet_h = float(vb[3])
    else:
        sheet_h = float(root.get("height", "384").replace("mm", ""))

    dxf_filename = svg_filename.replace(".svg", ".dxf")
    dxf_path = os.path.join(SVG_DIR, dxf_filename)

    entities = []  # list of (layer, entity_type, data)

    for el in root:
        tag_raw = el.tag
        if not isinstance(tag_raw, str):
            continue
        tag = tag_raw.replace(f"{{{NS}}}", "")
        if tag == "text":
            continue

        attribs = dict(el.attrib)
        stroke = attribs.get("stroke", "").lower()
        if stroke == "#0000ff":
            layer = "ENGRAVE"
        elif stroke == "#ff0000":
            layer = "CUT"
        else:
            layer = "CUT"

        def flip_y(y):
            return sheet_h - y

        if tag == "rect":
            x = float(attribs["x"])
            y = float(attribs["y"])
            w = float(attribs["width"])
            h = float(attribs["height"])
            rx = float(attribs.get("rx", "0"))
            if rx > 0:
                # Rounded rect as polyline (approximate corners with line segments)
                # For laser cutting, small radii are fine as straight segments
                pts = [
                    (x + rx, y), (x + w - rx, y),
                    (x + w, y + rx), (x + w, y + h - rx),
                    (x + w - rx, y + h), (x + rx, y + h),
                    (x, y + h - rx), (x, y + rx),
                ]
                pts_flipped = [(px, flip_y(py)) for px, py in pts]
                pts_flipped.append(pts_flipped[0])  # close
                entities.append((layer, "LWPOLYLINE", pts_flipped))
            else:
                pts = [(x, flip_y(y)), (x + w, flip_y(y)),
                       (x + w, flip_y(y + h)), (x, flip_y(y + h)),
                       (x, flip_y(y))]  # closed
                entities.append((layer, "LWPOLYLINE", pts))

        elif tag == "circle":
            cx = float(attribs["cx"])
            cy = float(attribs["cy"])
            r = float(attribs["r"])
            entities.append((layer, "CIRCLE", (cx, flip_y(cy), r)))

        elif tag == "path":
            coords = _parse_path_coords(attribs.get("d", ""))
            if len(coords) >= 2:
                pts = [(px, flip_y(py)) for px, py in coords]
                # Check if closed (first ~= last or has Z)
                d_str = attribs.get("d", "")
                if "Z" in d_str or (len(pts) > 2 and
                        abs(pts[0][0] - pts[-1][0]) < 0.01 and
                        abs(pts[0][1] - pts[-1][1]) < 0.01):
                    if abs(pts[0][0] - pts[-1][0]) > 0.01 or abs(pts[0][1] - pts[-1][1]) > 0.01:
                        pts.append(pts[0])
                entities.append((layer, "LWPOLYLINE", pts))

    # Write DXF R12
    with open(dxf_path, "w") as f:
        def w(code, value):
            f.write(f"  {code}\n{value}\n")

        # HEADER
        w(0, "SECTION")
        w(2, "HEADER")
        w(9, "$INSUNITS")
        w(70, 4)  # 4 = millimeters
        w(0, "ENDSEC")

        # TABLES (layers)
        w(0, "SECTION")
        w(2, "TABLES")
        w(0, "TABLE")
        w(2, "LAYER")
        w(70, 2)
        for lname, color in [("CUT", 1), ("ENGRAVE", 5)]:  # 1=red, 5=blue
            w(0, "LAYER")
            w(2, lname)
            w(70, 0)
            w(62, color)
            w(6, "CONTINUOUS")
        w(0, "ENDTAB")
        w(0, "ENDSEC")

        # ENTITIES
        w(0, "SECTION")
        w(2, "ENTITIES")
        for layer, etype, data in entities:
            if etype == "CIRCLE":
                cx, cy, r = data
                w(0, "CIRCLE")
                w(8, layer)
                w(10, f"{cx:.4f}")
                w(20, f"{cy:.4f}")
                w(40, f"{r:.4f}")
            elif etype == "LWPOLYLINE":
                pts = data
                w(0, "LWPOLYLINE")
                w(8, layer)
                w(90, len(pts))
                # Check if closed
                if (len(pts) > 2 and
                        abs(pts[0][0] - pts[-1][0]) < 0.01 and
                        abs(pts[0][1] - pts[-1][1]) < 0.01):
                    w(70, 1)  # closed
                    pts = pts[:-1]  # remove duplicate closing point
                else:
                    w(70, 0)  # open
                for px, py in pts:
                    w(10, f"{px:.4f}")
                    w(20, f"{py:.4f}")
        w(0, "ENDSEC")

        w(0, "EOF")

    print(f"  {dxf_filename}")
    return dxf_path


if __name__ == "__main__":
    # First regenerate individual panels
    print("Regenerating individual panel SVGs...")
    os.system(f"python3 {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generate_panels.py')}")

    print("\n=== Nesting panels onto Ponoko sheets ===")
    nest_3mm_sheet()
    nest_5mm_sheet()

    print("\n=== Converting to DXF ===")
    svg_to_dxf("sheet_3mm.svg")
    svg_to_dxf("sheet_5mm.svg")

    print("\nDone! Upload sheet SVGs or DXFs to Ponoko.")
