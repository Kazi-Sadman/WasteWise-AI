"""WasteWise AI - Streamlit frontend.

Run:  streamlit run app.py        (backend must be running on WASTEWISE_API_URL)
"""
from __future__ import annotations

import io
import json
import os
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
from PIL import Image

import api_client
import components as ui
from content import info, load_report, per_class_rows
from theme import build_css

DEFAULT_API_URL = os.getenv(
    "WASTEWISE_API_URL",
    "https://wastewise-ai-backend-sq58.onrender.com"
)
PAGES = ["Home", "Detect", "History", "Model"]
MAX_HISTORY = 12

st.set_page_config(page_title="WasteWise AI", page_icon="♻️", layout="wide", initial_sidebar_state="collapsed")

ss = st.session_state
ss.setdefault("night", True)
ss.setdefault("page", "Home")
ss.setdefault("history", [])
ss.setdefault("result", None)
theme = "dark" if ss["night"] else "light"
st.markdown(build_css(theme), unsafe_allow_html=True)


# ----------------------------------------------------------------- helpers
def stretch(fn, *args, **kwargs):
    """Full-width widgets across Streamlit versions (width='stretch' is the new spelling)."""
    try:
        return fn(*args, width="stretch", **kwargs)
    except Exception:
        return fn(*args, use_container_width=True, **kwargs)


@st.cache_data(ttl=5, show_spinner=False)
def cached_health(url: str) -> api_client.Health:
    return api_client.get_health(url)


def go(page: str) -> None:
    ss["page"] = page


def open_scan(index: int) -> None:
    e = ss["history"][index]
    ss["result"] = {"key": None, "data": e["data"], "orig": e["orig"], "name": e["name"]}
    ss["page"] = "Detect"


def clear_history() -> None:
    ss["history"] = []


def shrink(data: bytes, max_side: int = 1280) -> bytes:
    """Keep history light: downscale the original before storing it."""
    try:
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=88)
        return buf.getvalue()
    except Exception:
        return data


def remember(name: str, res: dict, orig: bytes) -> None:
    counts = res.get("counts_by_class", {})
    total = len(res.get("detections", []))
    ann = api_client.decode_annotated(res) or orig
    ss["history"].insert(0, {
        "name": name, "time": datetime.now().strftime("%d %b · %H:%M"), "total": total,
        "top": max(counts, key=counts.get) if total else "—",
        "thumb": ui.thumb_uri(ann), "data": res, "orig": shrink(orig),
    })
    del ss["history"][MAX_HISTORY:]


def health_pill(h: api_client.Health) -> str:
    if not h.online:
        return ui.pill("bad", "API offline")
    if not h.model_loaded:
        return ui.pill("warn", "Model not loaded")
    return ui.pill("ok", "Model ready")


# ----------------------------------------------------------------- top bar
with st.container(key="topbar"):
    c_brand, c_nav, c_theme = st.columns([2.3, 5, 2.2], vertical_alignment="center")
    c_brand.markdown(ui.brand(), unsafe_allow_html=True)
    with c_nav:
        st.radio("Navigation", PAGES, horizontal=True, key="page", label_visibility="collapsed")
    with c_theme:
        st.toggle("Night mode", key="night", help="Switch between day and night theme")

report = load_report()
_pc = (report or {}).get("test", {}).get("per_class", [])
class_names = [c["class_name"] for c in _pc] or ["Paper", "Plastic Bottle", "Plastic bag", "Plastic waste"]
map50 = {c["class_name"]: c["mAP50"] for c in (report or {}).get("test", {}).get("per_class", [])}


# ================================================================== HOME
def page_home() -> None:
    st.markdown(ui.hero(class_names), unsafe_allow_html=True)
    b1, b2, _ = st.columns([1.3, 1.3, 5])
    b1.button("Start detecting →", type="primary", on_click=go, args=("Detect",), key="cta1")
    b2.button("Model details", on_click=go, args=("Model",), key="cta2")

    st.write("")
    t = (report or {}).get("test") or {}
    st.markdown(ui.kpi_grid([
        ("Classes", str(len(class_names)), "waste types recognised"),
        ("Model", "YOLO11n", "fine-tuned, loaded once"),
        ("Test mAP50", f"{t['mAP50']:.2f}" if t else "—", "preliminary · see Model page"),
        ("Scans this session", str(len(ss["history"])), "saved in History"),
    ]), unsafe_allow_html=True)

    st.markdown(ui.section("What it detects", "advisory tips, not rules"), unsafe_allow_html=True)
    st.markdown(ui.class_tiles(class_names, map50), unsafe_allow_html=True)

    st.markdown(ui.section("How it works"), unsafe_allow_html=True)
    st.markdown(ui.steps([
        ("1", "Upload", "Send one JPEG, PNG, WEBP or BMP photo. It is checked, auto-rotated and never saved to disk."),
        ("2", "Detect", "A YOLO11n model fine-tuned on waste photos from Bangladesh looks for the four classes."),
        ("3", "Count", "Every object gets a box, a class and a confidence score, plus counts per class."),
        ("4", "Decide", "Use it as a helper. Recycling rules differ by place, so always check locally."),
    ]), unsafe_allow_html=True)


# ================================================================== DETECT
def page_detect() -> None:
    api_url = ss.get("_api", DEFAULT_API_URL)
    health = cached_health(api_url)
    st.markdown(ui.page_header("Detection", "Detect waste", "Add a photo, tune the settings and run the model.",
                               health_pill(health)), unsafe_allow_html=True)
    ready = health.online and health.model_loaded

    left, right = st.columns([5, 7], gap="large")
    picked = None
    img_bytes: Optional[bytes] = None
    file_key = None

    with left:
        st.radio("Source", ["Upload", "Camera"], horizontal=True, key="source", label_visibility="collapsed")
        if ss.get("source", "Upload") == "Upload":
            picked = st.file_uploader("Drop an image", type=["jpg", "jpeg", "png", "webp", "bmp"],
                                      label_visibility="collapsed", help="JPEG, PNG, WEBP or BMP · up to 10 MB")
        else:
            picked = st.camera_input("Take a photo", label_visibility="collapsed")

        if picked is not None:
            img_bytes = picked.getvalue()
            file_key = (picked.name, len(img_bytes))
            try:
                preview = Image.open(io.BytesIO(img_bytes))
                st.caption(f"{picked.name} · {preview.size[0]}×{preview.size[1]} px · {len(img_bytes)/1024:.0f} KB")
                if ss.get("source", "Upload") == "Upload":
                    stretch(st.image, preview)
            except Exception:
                st.error("This file could not be opened as an image.")
                img_bytes = None

        with st.expander("Detection settings"):
            confidence = st.slider("Confidence threshold", 0.05, 0.95, float(ss.get("_conf", 0.25)), 0.05,
                                   help="Higher = fewer but more certain detections. Lower = finds more, with more mistakes.")
            iou = st.slider("Overlap (NMS IoU)", 0.1, 0.95, float(ss.get("_iou", 0.70)), 0.05,
                            help="How much two boxes may overlap before one is dropped as a duplicate.")
            new_url = st.text_input("Backend URL", value=api_url)
            ss["_conf"], ss["_iou"] = confidence, iou
            if new_url != api_url:
                ss["_api"] = new_url
                cached_health.clear()
                st.rerun()

        go_btn = stretch(st.button, "Detect waste", type="primary", disabled=(img_bytes is None or not ready), key="run")
        if not ready:
            st.caption(health.detail or "The backend is not ready — check the status above.")
        elif img_bytes is None:
            st.caption("Add a photo first.")

        if go_btn and img_bytes is not None:
            with st.spinner("Running the model…"):
                try:
                    res = api_client.detect(api_url, img_bytes, picked.name, picked.type or "image/jpeg", confidence, iou)
                    ss["result"] = {"key": file_key, "data": res, "orig": img_bytes, "name": picked.name}
                    remember(picked.name, res, img_bytes)
                except api_client.ApiError as err:
                    ss["result"] = None
                    st.error(str(err))

    stored = ss.get("result")
    with right:
        if not stored:
            st.markdown(ui.empty("🌿", "No results yet", "Add a photo and press “Detect waste”."), unsafe_allow_html=True)
        else:
            if file_key is not None and stored["key"] != file_key:
                st.info("Showing results for a previous image. Press “Detect waste” to analyse the new one.")
            res = stored["data"]
            dets = res.get("detections", [])
            counts = res.get("counts_by_class", {})
            total = len(dets)
            avg = sum(d["confidence"] for d in dets) / total if total else 0.0
            top = max(counts, key=counts.get) if total else "—"
            st.markdown(ui.kpi_grid([
                ("Objects", str(total), f"threshold {res['confidence_threshold']:.2f}"),
                ("Most common", top, f"{counts.get(top, 0)} found" if total else "nothing found"),
                ("Avg confidence", f"{avg*100:.0f}%" if total else "—", "across detections"),
                ("Speed", f"{res['inference_ms']:.0f} ms", f"{res['image_width']}×{res['image_height']} px"),
            ], min_px=150), unsafe_allow_html=True)
            st.write("")
            st.radio("View", ["Detected", "Original"], horizontal=True, key="viewmode", label_visibility="collapsed")
            annotated = api_client.decode_annotated(res)
            show = (annotated or stored["orig"]) if ss.get("viewmode", "Detected") == "Detected" else stored["orig"]
            stretch(st.image, show)
            if total == 0:
                st.warning("Nothing was detected. Try lowering the confidence threshold, or use a closer, brighter photo.")

    if stored:
        res = stored["data"]
        dets = res.get("detections", [])
        st.markdown(ui.section("Breakdown by type"), unsafe_allow_html=True)
        st.markdown(ui.count_cards(res.get("counts_by_class", {})), unsafe_allow_html=True)
        if dets:
            st.markdown(ui.section("All detections", f"{len(dets)} objects"), unsafe_allow_html=True)
            st.markdown(ui.detections_table(dets), unsafe_allow_html=True)
            if any(d["confidence"] < 0.5 for d in dets):
                st.write("")
                st.markdown(ui.note("⚠️ <b>Some detections are below 50% confidence</b> — treat them as suggestions and check by eye."),
                            unsafe_allow_html=True)
            st.write("")
            stem = os.path.splitext(stored["name"] or "image")[0]
            df = pd.DataFrame([{"class": d["class_name"], "confidence": d["confidence"], **d["bbox"]} for d in dets])
            d1, d2, d3, _ = st.columns([1.2, 1.2, 1.2, 5])
            d1.download_button("⬇ CSV", df.to_csv(index=False).encode("utf-8"), file_name=f"{stem}_detections.csv", mime="text/csv")
            d2.download_button("⬇ JSON", json.dumps({k: v for k, v in res.items() if k != "annotated_image_base64"}, indent=2).encode("utf-8"),
                               file_name=f"{stem}_detections.json", mime="application/json")
            ann = api_client.decode_annotated(res)
            if ann:
                d3.download_button("⬇ Image", ann, file_name=f"{stem}_annotated.jpg", mime="image/jpeg")


# ================================================================== HISTORY
def page_history() -> None:
    st.markdown(ui.page_header("This session", "Scan history", "Every image you analysed, newest first."), unsafe_allow_html=True)
    hist = ss["history"]
    if not hist:
        st.markdown(ui.empty("🗂️", "Nothing here yet", "Your scans will show up here after you run a detection."), unsafe_allow_html=True)
        st.write("")
        st.button("Find waste now", type="primary", on_click=go, args=("Detect",), key="hist_cta")
        return
    for start in range(0, len(hist), 4):
        cols = st.columns(4, gap="medium")
        for off, col in enumerate(cols):
            i = start + off
            if i >= len(hist):
                break
            with col:
                st.markdown(ui.history_card(hist[i]), unsafe_allow_html=True)
                st.button("View result", on_click=open_scan, args=(i,), key=f"open_{i}")
    st.write("")
    st.button("Clear history", on_click=clear_history, key="clear")


# ================================================================== MODEL
def page_model() -> None:
    st.markdown(ui.page_header("Transparency", "Model & limits", "How well it works — and where it does not."), unsafe_allow_html=True)
    st.markdown(ui.note("<b>Preliminary numbers.</b> The first training run mixed two overlapping dataset partitions, so these scores "
                        "are likely optimistic. They update automatically from <code>reports/evaluation.json</code> after retraining."),
                unsafe_allow_html=True)
    st.write("")
    t = (report or {}).get("test")
    if t:
        st.markdown(ui.kpi_grid([("mAP50", f"{t['mAP50']:.2f}", "test split"), ("mAP50-95", f"{t['mAP50-95']:.2f}", "test split"),
                                 ("Precision", f"{t['precision']:.2f}", "test split"), ("Recall", f"{t['recall']:.2f}", "test split")],
                                min_px=170), unsafe_allow_html=True)
        rows = per_class_rows(report, "test")
        if rows:
            st.markdown(ui.section("Per class", "test split"), unsafe_allow_html=True)
            st.markdown(ui.metrics_table(rows), unsafe_allow_html=True)
            st.caption("“Plastic waste” is the weakest class — expect more misses there.")
    else:
        st.info("No evaluation report found at reports/evaluation.json.")

    st.markdown(ui.section("Limitations"), unsafe_allow_html=True)
    st.markdown(ui.steps([
        ("1", "Four classes only", "Other objects can be missed or mislabelled."),
        ("2", "Hard photos", "Small, dirty, blurred, hidden or overlapping items may be missed."),
        ("3", "One region", "Training photos come from south-eastern Bangladesh; accuracy elsewhere is unknown."),
        ("4", "Not a verdict", "Confidence is not a guarantee, and a label does not prove recyclability."),
    ]), unsafe_allow_html=True)

    st.markdown(ui.section("Data credit"), unsafe_allow_html=True)
    st.markdown("*A Curated Recyclable Waste Object Detection Dataset from Public Spaces in Southeastern Bangladesh* — "
                "Mazumder, S. H. · [Zenodo 10.5281/zenodo.22043339](https://doi.org/10.5281/zenodo.22043339) · CC BY 4.0.")


{"Home": page_home, "Detect": page_detect, "History": page_history, "Model": page_model}[ss["page"]]()
st.markdown(ui.footer(), unsafe_allow_html=True)
