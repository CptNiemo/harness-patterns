#!/usr/bin/env python3
"""Build the six template plates, tokens.json and slots.json from one layout.

Usage: python3 build_plates.py   (standard library only)
Writes the six plates into plates/ beside this file, and tokens.json and slots.json next to this file,
so the plates and the label positions always describe the same drawing.
No plate contains any text element: labels are placed later from slots.json.
"""
import json
import os

W, H = 1920, 1080
U = 8            # spacing unit
LINE = 2         # line weight
R = 12           # corner radius

LIGHT = dict(bg="#F6F5F2", line="#2B2F36", tree="#8A8F98", chip="#C9CCD1",
             plane=["#E4E3DF", "#EAE9E5", "#F0EFEB"], plane_edge="#C9CCD1",
             node="#FFFFFF", band="#C9CCD1", teal="#0F8B8D", amber="#E8A33D",
             amber_fill="#FDF3E1", teal_fill="#E7F3F3", panel="#FFFFFF",
             shadow="#2B2F36", shadow_op=0.07)
DARK = dict(bg="#14171C", line="#D7DAE0", tree="#8A8F98", chip="#565D69",
            plane=["#1B1F26", "#20252D", "#252B34"], plane_edge="#3A414C",
            node="#2A303A", band="#565D69", teal="#2BB3B5", amber="#E8A33D",
            amber_fill="#3A2F1C", teal_fill="#173436", panel="#2A303A",
            shadow="#000000", shadow_op=0.25)

# ---- layout data (shared by every plate) ---------------------------------
PLANE_X, PLANE_W, PLANE_H, SKEW = 200, 1520, 230, -10
LAYERS = [  # drawn bottom to top; index 0 = shared base
    dict(id="layer-base", name="base", y=670),
    dict(id="layer-group", name="group", y=400),
    dict(id="layer-personal", name="personal", y=130),
]
ROW_Y = {"base": 785, "group": 515, "personal": 245}
COL_X = {1: 480, 2: 820, 3: 1160, 4: 1500}
FOLDER = (160, 72)
FILE = (132, 60)
CHIP = (30, 10)
BAND = dict(x=104, y=130, w=20, h=770)

ITEMS = [  # id, kind, layer, branch, tags
    ("b1", "folder", "base", 1, ["t2", "t3"]),
    ("b2", "folder", "base", 2, ["t3", "t4"]),
    ("b3", "folder", "base", 3, ["t1", "t5"]),
    ("b4", "folder", "base", 4, ["t2", "t4", "t5"]),
    ("g1", "folder", "group", 1, ["t3", "t5"]),
    ("g2", "file", "group", 2, ["t1", "t4"]),
    ("g3", "folder", "group", 3, ["t2", "t3", "t4"]),
    ("g4", "file", "group", 4, ["t1", "t2"]),
    ("u1", "file", "personal", 1, ["t1", "t3"]),
    ("u2", "file", "personal", 2, ["t2", "t5"]),
    ("u3", "file", "personal", 3, ["t4", "t5"]),
    ("u4", "file", "personal", 4, ["t3", "t4"]),
]
ACTIVE_TAG = "t1"
SELECTED = "u3"
OPEN_BRANCH = 3
CHAIN = ["u1", "g2", "b3", "g4"]          # wormhole order
GATE_ON = 1                                 # arc index that carries the gate
STOPS = [(650, 708), (1330, 708), (1330, 438), (650, 438), (650, 168), (1330, 168)]
STOP_R = 13
PATH_D = ("M 330 708 L 1666 708 Q 1690 708 1690 684 L 1690 462 Q 1690 438 1666 438 "
          "L 354 438 Q 330 438 330 414 L 330 192 Q 330 168 354 168 L 1690 168")
TRUNK_Y = 880
FILTER_ROW = dict(y=540, xs=[600, 840, 1080, 1320], panel=(440, 420, 1040, 240))


def item(i):
    iid, kind, layer, branch, tags = i
    w, h = FOLDER if kind == "folder" else FILE
    cx, cy = COL_X[branch], ROW_Y[layer]
    return dict(id=iid, kind=kind, layer=layer, branch=branch, tags=tags,
                cx=cx, cy=cy, w=w, h=h, x=cx - w / 2, y=cy - h / 2)


IT = {i[0]: item(i) for i in ITEMS}


def label_box(n):
    return (n["cx"] + 12, n["y"] + n["h"] + 10, 150, 36)


def anchor(n, side):
    """Top-edge anchor for an arc: 'in' on the left half, 'out' on the right."""
    dx = -40 if side == "in" else 40
    y = n["y"] - (10 if n["kind"] == "folder" and side == "in" else 0)
    return (n["cx"] + dx, y)


ARC_CTRL = {  # hand-tuned control points so arcs clear nodes and label areas
    0: ((600, 110), (780, 300)),
    1: ((960, 380), (1120, 560)),
    2: ((1320, 700), (1400, 420)),
}


def arcs():
    out = []
    for k in range(len(CHAIN) - 1):
        u0 = anchor(IT[CHAIN[k]], "out")
        u3 = anchor(IT[CHAIN[k + 1]], "in")
        c1, c2 = ARC_CTRL[k]
        out.append((u0, c1, c2, u3))
    return out


def bez(u0, c1, c2, u3, t):
    m = 1 - t
    return tuple(m ** 3 * a + 3 * m * m * t * b + 3 * m * t * t * c + t ** 3 * d
                 for a, b, c, d in zip(u0, c1, c2, u3))


# ---- drawing helpers ------------------------------------------------------
def rect(x, y, w, h, r=R, **a):
    attrs = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in a.items())
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{r:g}" {attrs}/>'


def plane(P, idx, y, op=1.0):
    cx, cy = PLANE_X + PLANE_W / 2, y + PLANE_H / 2
    t = f'transform="translate({cx:g} {cy:g}) skewX({SKEW}) translate({-cx:g} {-cy:g})"'
    return (f'<g {t} opacity="{op:g}">'
            + rect(PLANE_X, y + 8, PLANE_W, PLANE_H, 18, fill=P["shadow"], opacity=P["shadow_op"])
            + rect(PLANE_X, y, PLANE_W, PLANE_H, 18, fill=P["plane"][idx],
                   stroke=P["plane_edge"], stroke_width=1.5)
            + "</g>")


def node(P, n, state="normal", active_tag=None, at=None):
    """state: normal | selected | active | dimmed. at=(x, y) overrides position."""
    x, y = (n["x"], n["y"]) if at is None else at
    w, h = n["w"], n["h"]
    stroke, sw, fill = P["line"], LINE, P["node"]
    if state == "selected":
        stroke, sw, fill = P["amber"], 3, P["amber_fill"]
    elif state == "active":
        stroke, sw, fill = P["teal"], 2.5, P["teal_fill"]
    g = [f'<g opacity="{0.28 if state == "dimmed" else 1:g}">']
    if n["kind"] == "folder":
        g.append(rect(x, y - 10, 60, 24, 7, fill=fill, stroke=stroke, stroke_width=sw))
    g.append(rect(x, y, w, h, R, fill=fill, stroke=stroke, stroke_width=sw))
    for k, tag in enumerate(n["tags"]):
        col = P["teal"] if (tag == active_tag and state != "dimmed") else P["chip"]
        g.append(rect(x + 14 + k * (CHIP[0] + 6), y + h - 20, CHIP[0], CHIP[1], 5, fill=col))
    g.append("</g>")
    return "".join(g)


def line(P, x1, y1, x2, y2, op=1.0):
    return (f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{P["tree"]}" '
            f'stroke-width="{LINE}" stroke-linecap="round" opacity="{op:g}"/>')


def tree_lines(P, dim_branches=(), op_all=1.0):
    out = []
    xs = [COL_X[b] for b in COL_X]
    out.append(line(P, 260, TRUNK_Y, max(xs), TRUNK_Y, op_all * (0.28 if dim_branches else 1)))
    out.append(f'<circle cx="260" cy="{TRUNK_Y}" r="5" fill="{P["tree"]}" '
               f'opacity="{op_all * (0.28 if dim_branches else 1):g}"/>')
    for b, x in COL_X.items():
        op = op_all * (0.28 if b in dim_branches else 1)
        col = [n for n in IT.values() if n["branch"] == b]
        base = next(n for n in col if n["layer"] == "base")
        grp = next(n for n in col if n["layer"] == "group")
        per = next(n for n in col if n["layer"] == "personal")
        out.append(line(P, x, base["y"] + base["h"], x, TRUNK_Y, op))
        out.append(line(P, x, grp["y"] + grp["h"], x, base["y"], op))
        out.append(line(P, x, per["y"] + per["h"], x, grp["y"], op))
    return "".join(out)


def band(P, active=False, op=1.0):
    b = BAND
    s = rect(b["x"], b["y"], b["w"], b["h"], 10, fill=P["band"], stroke=P["line"],
             stroke_width=LINE, opacity=op)
    if active:
        s += rect(b["x"] + 5, 215, b["w"] - 10, 170, 5, fill=P["teal"])
    return s


def stop_path(P):
    s = (f'<path d="{PATH_D}" fill="none" stroke="{P["tree"]}" stroke-width="3" '
         f'stroke-linecap="round" stroke-dasharray="0.1 11" opacity="0.75"/>')
    for x, y in STOPS:
        s += (f'<circle cx="{x}" cy="{y}" r="{STOP_R}" fill="{P["bg"]}" stroke="{P["line"]}" '
              f'stroke-width="{LINE}"/>')
    return s


def diamond(P, x, y, s=15, fill=None):
    pts = f"{x:g},{y - s:g} {x + s:g},{y:g} {x:g},{y + s:g} {x - s:g},{y:g}"
    return (f'<polygon points="{pts}" fill="{fill or P["bg"]}" stroke="{P["teal"]}" '
            f'stroke-width="2.5" stroke-linejoin="round"/>'
            f'<line x1="{x - 6:g}" y1="{y:g}" x2="{x + 6:g}" y2="{y:g}" stroke="{P["teal"]}" '
            f'stroke-width="2.5" stroke-linecap="round"/>')


def tube(P, d, start, end):
    """Wormhole drawn as a soft translucent liquid tube: wide pale body, narrower
    inner body, thin bright core, a rounded drop-shaped head where it arrives."""
    t = P["teal"]
    s = (f'<path d="{d}" fill="none" stroke="{t}" stroke-opacity="0.16" stroke-width="18" '
         f'stroke-linecap="round"/>'
         f'<path d="{d}" fill="none" stroke="{t}" stroke-opacity="0.22" stroke-width="10" '
         f'stroke-linecap="round"/>'
         f'<path d="{d}" fill="none" stroke="{t}" stroke-opacity="0.9" stroke-width="2" '
         f'stroke-linecap="round"/>')
    s += (f'<circle cx="{start[0]:g}" cy="{start[1]:g}" r="6" fill="{P["bg"]}" stroke="{t}" '
          f'stroke-width="2"/>')
    s += (f'<circle cx="{end[0]:g}" cy="{end[1]:g}" r="13" fill="{t}" fill-opacity="0.22"/>'
          f'<circle cx="{end[0]:g}" cy="{end[1]:g}" r="5.5" fill="{t}"/>')
    return s


def wormholes(P):
    s = (f'<path d="M 124 300 C 230 300 300 245 {IT["u1"]["x"]:g} 245" fill="none" '
         f'stroke="{P["teal"]}" stroke-width="2.5" stroke-linecap="round"/>')
    for k, (u0, c1, c2, u3) in enumerate(arcs()):
        s += tube(P, f'M {u0[0]:g} {u0[1]:g} C {c1[0]:g} {c1[1]:g} {c2[0]:g} {c2[1]:g} '
                     f'{u3[0]:g} {u3[1]:g}', u0, u3)
        if k == GATE_ON:
            gx, gy = bez(u0, c1, c2, u3, 0.5)
            s += diamond(P, gx, gy)
    return s


def svg(P, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
            f'height="{H}">\n<rect width="{W}" height="{H}" fill="{P["bg"]}"/>\n{body}\n</svg>\n')


def scene(P, states, active_tag=None, dim_branches=(), with_path=False, band_active=False,
          plane_op=1.0, ghost=1.0):
    b = [f'<g opacity="{ghost:g}">']
    for idx, L in enumerate(LAYERS):
        b.append(plane(P, idx, L["y"], plane_op))
    b.append(band(P, band_active))
    b.append(tree_lines(P, dim_branches))
    if with_path:
        b.append(stop_path(P))
    for n in IT.values():
        b.append(node(P, n, states.get(n["id"], "normal"), active_tag))
    b.append("</g>")
    return "\n".join(b)


# ---- plates ---------------------------------------------------------------
def plate_overview(P):
    return svg(P, scene(P, {SELECTED: "selected"}, with_path=True))


def plate_drilldown(P):
    st = {n["id"]: "dimmed" for n in IT.values() if n["branch"] != OPEN_BRANCH}
    st[SELECTED] = "selected"
    dim = tuple(b for b in COL_X if b != OPEN_BRANCH)
    x = COL_X[OPEN_BRANCH]
    halo = rect(x - 128, 150, 316, 760, 20, fill=P["panel"], opacity=0.55,
                stroke=P["plane_edge"], stroke_width=1.5)
    body = scene(P, st, dim_branches=dim, plane_op=0.6)
    # the open-branch panel sits between planes and nodes: rebuild in order
    parts = [f'<g>']
    for idx, L in enumerate(LAYERS):
        parts.append(plane(P, idx, L["y"], 0.6))
    parts.append(halo)
    parts.append(band(P, False, 0.5))
    parts.append(tree_lines(P, dim))
    for n in IT.values():
        parts.append(node(P, n, st.get(n["id"], "normal")))
    parts.append("</g>")
    return svg(P, "\n".join(parts))


def plate_wormhole(P):
    st = {i: "active" for i in CHAIN}
    return svg(P, scene(P, st, active_tag=ACTIVE_TAG, band_active=True) + "\n" + wormholes(P))


def filter_positions():
    out = {}
    for iid, x in zip(CHAIN, FILTER_ROW["xs"]):
        n = IT[iid]
        out[iid] = (x - n["w"] / 2, FILTER_ROW["y"] - n["h"] / 2 - 14)
    return out


def plate_filter(P):
    st = {n["id"]: "dimmed" for n in IT.values()}
    px, py, pw, ph = FILTER_ROW["panel"]
    b = [scene(P, st, ghost=0.5, plane_op=0.7)]
    b.append(rect(px, py + 10, pw, ph, 24, fill=P["shadow"], opacity=P["shadow_op"]))
    b.append(rect(px, py, pw, ph, 24, fill=P["panel"], stroke=P["plane_edge"], stroke_width=1.5))
    b.append(rect(px + 40, py + 28, 46, 14, 7, fill=P["teal"]))
    for iid, at in filter_positions().items():
        b.append(node(P, IT[iid], "active", ACTIVE_TAG, at=at))
    return svg(P, "\n".join(b))


COMP_X = [288, 624, 960, 1296, 1632]
COMP_Y = [330, 700]
COMPONENTS = ["folder-node", "file-node", "layer-plane", "tag-chip", "connector-band",
              "wormhole-arc", "gate-marker", "stop-marker", "selected-state", "dimmed-state"]


def comp_centres():
    return {c: (COMP_X[k % 5], COMP_Y[k // 5]) for k, c in enumerate(COMPONENTS)}


def plate_components(P):
    C = comp_centres()
    b = []

    def scaled(cx, cy, s, inner):
        return f'<g transform="translate({cx:g} {cy:g}) scale({s:g})">{inner}</g>'

    fold = dict(kind="folder", w=FOLDER[0], h=FOLDER[1], tags=["a", "b"])
    fil = dict(kind="file", w=FILE[0], h=FILE[1], tags=["a", "b"])
    cx, cy = C["folder-node"]
    b.append(scaled(cx, cy, 1.4, node(P, fold, at=(-80, -31))))
    cx, cy = C["file-node"]
    b.append(scaled(cx, cy, 1.4, node(P, fil, at=(-66, -30))))
    cx, cy = C["layer-plane"]
    b.append(f'<g transform="translate({cx:g} {cy:g}) skewX({SKEW})">'
             + rect(-120, -42, 240, 100, 16, fill=P["shadow"], opacity=P["shadow_op"])
             + rect(-120, -50, 240, 100, 16, fill=P["plane"][0], stroke=P["plane_edge"],
                    stroke_width=1.5) + "</g>")
    cx, cy = C["tag-chip"]
    b.append(rect(cx - 104, cy - 15, 90, 30, 15, fill=P["chip"]))
    b.append(rect(cx + 14, cy - 15, 90, 30, 15, fill=P["teal"]))
    cx, cy = C["connector-band"]
    b.append(rect(cx - 10, cy - 90, 20, 180, 10, fill=P["band"], stroke=P["line"],
                  stroke_width=LINE))
    cx, cy = C["wormhole-arc"]
    b.append(tube(P, f'M {cx - 110} {cy + 40} C {cx - 50} {cy - 90} {cx + 50} {cy - 90} '
                     f'{cx + 110} {cy + 40}', (cx - 110, cy + 40), (cx + 110, cy + 40)))
    cx, cy = C["gate-marker"]
    b.append(f'<line x1="{cx - 90}" y1="{cy}" x2="{cx + 90}" y2="{cy}" stroke="{P["teal"]}" '
             f'stroke-width="2.5" stroke-linecap="round"/>')
    b.append(scaled(cx, cy, 2.2, diamond(P, 0, 0)))
    cx, cy = C["stop-marker"]
    b.append(f'<line x1="{cx - 90}" y1="{cy}" x2="{cx + 90}" y2="{cy}" stroke="{P["tree"]}" '
             f'stroke-width="3" stroke-linecap="round" stroke-dasharray="0.1 11" opacity="0.75"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="26" fill="{P["bg"]}" stroke="{P["line"]}" '
             f'stroke-width="{LINE}"/>')
    cx, cy = C["selected-state"]
    b.append(scaled(cx, cy, 1.4, node(P, fil, "selected", at=(-66, -30))))
    cx, cy = C["dimmed-state"]
    b.append(scaled(cx, cy, 1.4, node(P, fil, "dimmed", at=(-66, -30))))
    # hairline grid so the sheet reads as a tidy two-row table
    b.append(f'<line x1="120" y1="515" x2="1800" y2="515" stroke="{P["plane_edge"]}" '
             f'stroke-width="1.5"/>')
    return svg(P, "\n".join(b))


# ---- slots (percentages of width and height) ------------------------------
def pct(x, y, w=None, h=None):
    d = dict(x=round(100 * x / W, 2), y=round(100 * y / H, 2))
    if w is not None:
        d.update(w=round(100 * w / W, 2), h=round(100 * h / H, 2))
    return d


def element_slots(positions=None, include=None):
    out = []
    for n in IT.values():
        if include and n["id"] not in include:
            continue
        x, y = (n["x"], n["y"]) if not positions else positions[n["id"]]
        lb = (x + n["w"] / 2 + 12, y + n["h"] + 10, 150, 36) if not positions else \
             (x, y + n["h"] + 12, n["w"], 36)
        out.append(dict(id=n["id"], kind=n["kind"], layer=n["layer"], branch=n["branch"],
                        tags=n["tags"], box=pct(x, y, n["w"], n["h"]), label=pct(*lb)))
    return out


def layer_slots():
    return [dict(id=L["id"], layer=L["name"], box=pct(PLANE_X, L["y"], PLANE_W, PLANE_H),
                 label=pct(PLANE_X + PLANE_W + 28, L["y"] + PLANE_H / 2 - 20, 150, 40))
            for L in LAYERS]


def common_slots():
    b = BAND
    return dict(layers=layer_slots(), elements=element_slots(),
                connector=dict(box=pct(b["x"], b["y"], b["w"], b["h"]),
                               label=pct(40, b["y"] + b["h"] + 16, 150, 36)))


def build_slots():
    stops = [dict(n=k + 1, centre=pct(x, y), radius=round(100 * STOP_R / W, 2),
                  label=pct(x + 22, y - 16, 96, 32)) for k, (x, y) in enumerate(STOPS)]
    A = arcs()
    gx, gy = bez(*A[GATE_ON], 0.5)
    worm = dict(active_tag=ACTIVE_TAG, items=CHAIN,
                arcs=[dict(frm=CHAIN[k], to=CHAIN[k + 1], start=pct(*a[0]), c1=pct(*a[1]),
                           c2=pct(*a[2]), end=pct(*a[3]), gate=(k == GATE_ON))
                      for k, a in enumerate(A)],
                gate=dict(centre=pct(gx, gy), label=pct(gx - 128, gy + 6, 110, 30)))
    px, py, pw, ph = FILTER_ROW["panel"]
    C = comp_centres()
    plates = {
        "plate-1-overview": dict(common_slots(), selected=SELECTED, stops=stops),
        "plate-2-drilldown": dict(common_slots(), selected=SELECTED, open_branch=OPEN_BRANCH,
                                  dimmed=[n["id"] for n in IT.values()
                                          if n["branch"] != OPEN_BRANCH]),
        "plate-3-wormhole": dict(common_slots(), wormhole=worm),
        "plate-4-filter": dict(active_tag=ACTIVE_TAG, panel=pct(px, py, pw, ph),
                               title=pct(px + 100, py + 18, 400, 36),
                               elements=element_slots(filter_positions(), CHAIN),
                               ghosted=common_slots()),
        "plate-5-components": dict(components=[
            dict(id=c, centre=pct(*C[c]), box=pct(C[c][0] - 140, C[c][1] - 110, 280, 220),
                 label=pct(C[c][0] - 120, C[c][1] + 120, 240, 40)) for c in COMPONENTS]),
        "plate-6-overview-dark": dict(common_slots(), selected=SELECTED, stops=stops,
                                      theme="dark"),
    }
    return dict(canvas=dict(width=W, height=H, aspect="16:9", units="percent of width / height"),
                counts=dict(layers=len(LAYERS), branches=len(COL_X), items=len(ITEMS)),
                plates=plates)


def build_tokens():
    def colours(P):
        return dict(background=P["bg"], line=P["line"], tree_line=P["tree"], chip=P["chip"],
                    layer_planes=P["plane"], layer_edge=P["plane_edge"], node_fill=P["node"],
                    connector_band=P["band"], accent_active=P["teal"],
                    accent_active_fill=P["teal_fill"], accent_selected=P["amber"],
                    accent_selected_fill=P["amber_fill"], panel=P["panel"])
    return dict(colour=dict(light=colours(LIGHT), dark=colours(DARK)),
                line_weight_px=LINE, accent_line_weight_px=2.5, selected_line_weight_px=3,
                corner_radius_px=R, spacing_unit_px=U,
                chip=dict(width_px=CHIP[0], height_px=CHIP[1], radius_px=5, gap_px=6),
                node=dict(folder=dict(width_px=FOLDER[0], height_px=FOLDER[1], tab_px=[60, 10]),
                          file=dict(width_px=FILE[0], height_px=FILE[1])),
                layer_plane=dict(width_px=PLANE_W, height_px=PLANE_H, radius_px=18,
                                 skew_deg=SKEW),
                stop_marker_radius_px=STOP_R, gate_marker_half_px=15,
                dimmed_opacity=0.28, shadow=dict(offset_y_px=8, opacity=LIGHT["shadow_op"]),
                canvas=dict(width_px=W, height_px=H))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    plates = {
        "plate-1-overview": plate_overview(LIGHT),
        "plate-2-drilldown": plate_drilldown(LIGHT),
        "plate-3-wormhole": plate_wormhole(LIGHT),
        "plate-4-filter": plate_filter(LIGHT),
        "plate-5-components": plate_components(LIGHT),
        "plate-6-overview-dark": plate_overview(DARK),
    }
    plate_dir = os.path.join(here, "plates")
    os.makedirs(plate_dir, exist_ok=True)
    for name, body in plates.items():
        with open(os.path.join(plate_dir, name + ".svg"), "w", encoding="utf-8") as f:
            f.write(body)
    with open(os.path.join(here, "tokens.json"), "w", encoding="utf-8") as f:
        json.dump(build_tokens(), f, indent=2)
    with open(os.path.join(here, "slots.json"), "w", encoding="utf-8") as f:
        json.dump(build_slots(), f, indent=2)


if __name__ == "__main__":
    main()
