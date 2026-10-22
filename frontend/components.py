"""Pure HTML builders (no Streamlit imports) so they can be previewed and tested on their own."""
from __future__ import annotations

import base64
import html
import io
from typing import Dict, Iterable, List, Optional, Sequence

from PIL import Image

from content import info

LOGO = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" '
        'stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>'
        '<path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>')


def esc(x) -> str:
    return html.escape(str(x))


def brand() -> str:
    return f'<div class="ww-brand"><span class="ww-logo">{LOGO}</span><span>WasteWise <b>AI</b></span></div>'


def page_header(eyebrow: str, title: str, sub: str, right_html: str = "") -> str:
    return (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap">'
            f'<div><div class="ww-eyebrow">{esc(eyebrow)}</div><div class="ww-title">{esc(title)}</div>'
            f'<div class="ww-sub">{esc(sub)}</div></div><div style="padding-bottom:18px">{right_html}</div></div>')


def hero(class_names: Iterable[str]) -> str:
    chips = "".join(f'<span class="ww-chip">{info(n)["icon"]} {esc(n)}</span>' for n in class_names)
    return ('<div class="ww-hero"><div class="ww-eyebrow">AI waste detection · YOLO11</div>'
            '<h1>Spot waste in <em>seconds</em>.</h1>'
            '<p>Upload a photo and WasteWise AI finds paper, plastic bottles, plastic bags and mixed plastic waste — '
            'with a box, a label and a confidence score for every object.</p>'
            f'<div class="ww-chips">{chips}</div></div>')


def section(title: str, aside: str = "") -> str:
    return f'<div class="ww-h"><span>{esc(title)}</span><small>{esc(aside)}</small></div>'


def pill(kind: str, text: str) -> str:
    return f'<span class="ww-pill ww-{kind}"><i></i>{esc(text)}</span>'


def kpi_grid(items: Sequence[tuple], min_px: int = 200) -> str:
    cells = "".join(f'<div class="ww-card ww-kpi"><div class="label">{esc(l)}</div><div class="value">{esc(v)}</div>'
                    f'<div class="sub">{esc(s)}</div></div>' for l, v, s in items)
    return f'<div class="ww-grid" style="--min:{min_px}px">{cells}</div>'


def class_tiles(names: Iterable[str], map50: Optional[Dict[str, float]] = None) -> str:
    out = []
    for n in names:
        m = info(n)
        right = ""
        if map50 and n in map50:
            right = f'<div class="meta"><div><div class="k">mAP50 · prelim.</div><div class="v">{map50[n]:.2f}</div></div></div>'
        out.append(
            f'<div class="ww-tile"><div class="banner" style="background:linear-gradient(135deg,{m["color"]}40,{m["color"]}10)">'
            f'<span class="ww-badge">{esc(n)}</span>{m["icon"]}</div>'
            f'<div class="body"><div class="name">{esc(n)}</div><div class="tip">{esc(m["tip"])}</div>{right}</div></div>')
    return f'<div class="ww-grid" style="--min:240px">{"".join(out)}</div>'


def steps(items: Sequence[tuple]) -> str:
    cells = "".join(f'<div class="ww-card ww-step"><div class="n">{n}</div><div class="t">{esc(t)}</div>'
                    f'<div class="d">{esc(d)}</div></div>' for n, t, d in items)
    return f'<div class="ww-grid" style="--min:220px">{cells}</div>'


def count_cards(counts: Dict[str, int]) -> str:
    cells = "".join(
        f'<div class="ww-card ww-class" style="--c:{info(n)["color"]}"><div class="head"><span class="name">{info(n)["icon"]} {esc(n)}</span>'
        f'<span class="count">{c}</span></div><div class="tip">{esc(info(n)["tip"])}</div></div>' for n, c in counts.items())
    return f'<div class="ww-grid" style="--min:230px">{cells}</div>'


def empty(icon: str, title: str, sub: str) -> str:
    return f'<div class="ww-empty"><div class="big">{icon}</div><div class="t">{esc(title)}</div><div class="s">{esc(sub)}</div></div>'


def note(text_html: str) -> str:
    return f'<div class="ww-note">{text_html}</div>'


def table(headers: Sequence[str], rows: Sequence[Sequence[str]], classes: Optional[Sequence[str]] = None) -> str:
    """rows hold ready-made HTML cells (escape before passing)."""
    classes = classes or [""] * len(headers)
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f'<td class="{c}">{cell}</td>' for cell, c in zip(r, classes)) + "</tr>" for r in rows)
    return f'<div class="ww-tablewrap"><table class="ww-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def conf_bar(value: float) -> str:
    return f'<span class="ww-bar"><i style="width:{max(0, min(1, value))*100:.0f}%"></i></span>{value:.2f}'


def class_dot(name: str) -> str:
    return f'<span class="ww-dot" style="--c:{info(name)["color"]}"></span>{esc(name)}'


def detections_table(dets: List[dict]) -> str:
    rows = []
    for i, d in enumerate(dets, 1):
        b = d["bbox"]
        rows.append([str(i), class_dot(d["class_name"]), conf_bar(d["confidence"]),
                     f'{b["x_max"]-b["x_min"]:.0f} × {b["y_max"]-b["y_min"]:.0f} px',
                     f'({b["x_min"]:.0f}, {b["y_min"]:.0f}) → ({b["x_max"]:.0f}, {b["y_max"]:.0f})'])
    return table(["#", "Class", "Confidence", "Size", "Box"], rows, ["m", "b", "", "", "m"])


def metrics_table(rows: List[dict]) -> str:
    cells = [[class_dot(r["Class"]), f'{r["Precision"]:.2f}', f'{r["Recall"]:.2f}', f'{r["mAP50"]:.2f}', f'{r["mAP50-95"]:.2f}'] for r in rows]
    return table(["Class", "Precision", "Recall", "mAP50", "mAP50-95"], cells, ["b", "", "", "", ""])


def thumb_uri(data: bytes, max_side: int = 520) -> str:
    """Small data-URI thumbnail for history cards."""
    try:
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=80)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return ""


def history_card(entry: dict) -> str:
    status = pill("ok", f'{entry["total"]} found') if entry["total"] else pill("neutral", "clean")
    return (f'<div class="ww-tile"><div class="thumb" style="background-image:url({entry["thumb"]})">'
            f'<span class="ww-badge">{esc(entry["time"])}</span></div><div class="body">'
            f'<div class="name">{esc(entry["name"])}</div>'
            f'<div class="meta"><div><div class="k">Top class</div><div class="v" style="font-size:1.02rem">{esc(entry["top"])}</div></div>'
            f'<div>{status}</div></div></div></div>')


def footer() -> str:
    return (f'<div class="ww-foot"><div class="ww-brand" style="font-size:1rem"><span class="ww-logo" style="width:28px;height:28px;border-radius:9px">{LOGO}</span>'
            '<span>WasteWise <b>AI</b></span></div>'
            '<div>© 2026 WasteWise AI · Advisory tool — not a substitute for local waste-sorting rules.</div></div>')
