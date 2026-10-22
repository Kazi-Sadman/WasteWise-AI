"""Design tokens + CSS. build_css('dark' | 'light') returns a <style> block."""

PALETTES = {
    "dark": dict(
        bg="#070a12", surface="#0f1626", surface2="#161f33", line="#222d45", text="#f1f5f9", muted="#94a3b8",
        accent="#34d399", accent_hi="#6ee7b7", on_accent="#04281a", accent_soft="rgba(52,211,153,.13)",
        accent_line="rgba(52,211,153,.38)", glow="rgba(52,211,153,.20)", blue_glow="rgba(59,130,246,.11)",
        shadow="0 14px 34px -16px rgba(0,0,0,.75)", ok_bg="rgba(52,211,153,.14)", ok_fg="#34d399",
        warn_bg="rgba(251,191,36,.14)", warn_fg="#fbbf24", bad_bg="rgba(248,113,113,.14)", bad_fg="#f87171",
        hero="linear-gradient(135deg,#0f1a2e 0%,#0b1220 60%,#0d1f1a 120%)", img_bg="#0b1220",
    ),
    "light": dict(
        bg="#f2f6f4", surface="#ffffff", surface2="#f1f5f9", line="#dfe6ee", text="#0f172a", muted="#64748b",
        accent="#16a34a", accent_hi="#22c55e", on_accent="#ffffff", accent_soft="rgba(22,163,74,.10)",
        accent_line="rgba(22,163,74,.40)", glow="rgba(34,197,94,.20)", blue_glow="rgba(59,130,246,.08)",
        shadow="0 14px 30px -18px rgba(15,23,42,.28)", ok_bg="#dcfce7", ok_fg="#15803d",
        warn_bg="#fef3c7", warn_fg="#92400e", bad_bg="#fee2e2", bad_fg="#991b1b",
        hero="linear-gradient(135deg,#ffffff 0%,#f0fdf4 70%,#dcfce7 130%)", img_bg="#e9efec",
    ),
}


def build_css(theme: str) -> str:
    p = PALETTES.get(theme, PALETTES["dark"])
    root = ":root{" + "".join(f"--{k.replace('_','-')}:{v};" for k, v in p.items()) + \
           f"color-scheme:{'dark' if theme == 'dark' else 'light'};}}"
    return "<style>\n@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');\n" \
           + root + STATIC + "\n</style>"


STATIC = """
html, body, .stApp, [class*="css"] { font-family:'Inter',system-ui,-apple-system,sans-serif; }
div.stApp { background:
    radial-gradient(900px 520px at 12% -8%, var(--blue-glow), transparent 60%),
    radial-gradient(700px 420px at 100% 0%, var(--glow), transparent 62%), var(--bg);
  color:var(--text); }
#MainMenu, footer, header[data-testid="stHeader"], div[data-testid="stToolbar"],
section[data-testid="stSidebar"], div[data-testid="stSidebarCollapsedControl"], div[data-testid="collapsedControl"],
div[data-testid="stDecoration"] { display:none !important; }
.block-container { max-width:1200px; padding:0 1.2rem 2.5rem !important; }
div.stApp h1,div.stApp h2,div.stApp h3,div.stApp h4 { color:var(--text); letter-spacing:-.02em; }
div.stApp p, div.stApp li, div.stApp label, div.stApp span[data-testid="stWidgetLabel"] { color:var(--text); }
div.stApp [data-testid="stCaptionContainer"], div.stApp small { color:var(--muted) !important; }
div.stApp a { color:var(--accent); }

/* ---------------- Top bar ---------------- */
.st-key-topbar { position:sticky; top:0; z-index:50; margin:0 -1.2rem 26px; padding:12px 1.2rem;
  background:color-mix(in srgb, var(--bg) 82%, transparent); backdrop-filter:blur(14px);
  border-bottom:1px solid var(--line); }
.ww-brand { display:flex; align-items:center; gap:10px; font-weight:800; font-size:1.12rem; color:var(--text); white-space:nowrap; }
.ww-brand b { color:var(--accent); font-weight:800; }
.ww-logo { width:36px; height:36px; border-radius:11px; display:inline-flex; align-items:center; justify-content:center;
  background:linear-gradient(135deg,var(--accent-hi),var(--accent)); color:var(--on-accent);
  box-shadow:0 8px 20px -6px var(--glow); }

/* pill radios: main nav + segmented controls */
.st-key-page div[role="radiogroup"], .st-key-viewmode div[role="radiogroup"], .st-key-source div[role="radiogroup"] { gap:4px; flex-wrap:wrap; }
.st-key-page label, .st-key-viewmode label, .st-key-source label { background:transparent; border-radius:999px; padding:7px 16px !important;
  margin:0 !important; cursor:pointer; transition:background .15s; }
.st-key-page label > div:first-child, .st-key-viewmode label > div:first-child, .st-key-source label > div:first-child { display:none !important; }
.st-key-page label p, .st-key-viewmode label p, .st-key-source label p { color:var(--muted) !important; font-weight:600; font-size:.92rem; }
.st-key-page label:hover p, .st-key-viewmode label:hover p, .st-key-source label:hover p { color:var(--text) !important; }
.st-key-page label:has(input:checked), .st-key-viewmode label:has(input:checked), .st-key-source label:has(input:checked) {
  background:var(--accent-soft); box-shadow:inset 0 0 0 1px var(--accent-line); }
.st-key-page label:has(input:checked) p, .st-key-viewmode label:has(input:checked) p, .st-key-source label:has(input:checked) p { color:var(--accent) !important; }
.st-key-viewmode label, .st-key-source label { background:var(--surface2); }
.st-key-night { display:flex; justify-content:flex-end; }
.st-key-night label p { color:var(--text) !important; font-weight:600; font-size:.88rem; }

/* ---------------- Typography blocks ---------------- */
.ww-eyebrow { font-size:.74rem; letter-spacing:.16em; text-transform:uppercase; font-weight:700; color:var(--accent); }
.ww-title { font-size:2.15rem; font-weight:800; letter-spacing:-.03em; color:var(--text); margin:2px 0 4px; line-height:1.15; }
.ww-sub { color:var(--muted); font-size:.98rem; margin-bottom:18px; }
.ww-h { font-size:1.2rem; font-weight:700; color:var(--text); margin:30px 0 14px; display:flex; align-items:center; justify-content:space-between; }
.ww-h small { font-size:.82rem; font-weight:600; color:var(--muted); }

/* ---------------- Hero ---------------- */
.ww-hero { position:relative; overflow:hidden; background:var(--hero); border:1px solid var(--line); border-radius:24px;
  padding:42px 44px; box-shadow:var(--shadow); }
.ww-hero::after { content:""; position:absolute; right:-80px; top:-90px; width:420px; height:420px; border-radius:50%;
  background:radial-gradient(circle, var(--glow), transparent 68%); pointer-events:none; }
.ww-hero h1 { font-size:3rem; font-weight:800; letter-spacing:-.035em; margin:8px 0 12px; color:var(--text); line-height:1.08; }
.ww-hero h1 em { font-style:normal; color:var(--accent); }
.ww-hero p { color:var(--muted); font-size:1.06rem; max-width:560px; line-height:1.6; margin:0; }
.ww-chips { margin-top:22px; display:flex; flex-wrap:wrap; gap:8px; position:relative; z-index:1; }
.ww-chip { background:var(--surface2); border:1px solid var(--line); padding:6px 13px; border-radius:999px; font-size:.84rem; font-weight:600; color:var(--text); }

/* ---------------- Cards & grids ---------------- */
.ww-grid { display:grid; gap:16px; grid-template-columns:repeat(auto-fit,minmax(var(--min,220px),1fr)); }
.ww-card { background:var(--surface); border:1px solid var(--line); border-radius:18px; padding:18px 20px; box-shadow:var(--shadow); }
.ww-kpi .label { color:var(--muted); font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.09em; }
.ww-kpi .value { color:var(--accent); font-size:1.85rem; font-weight:800; line-height:1.15; margin-top:6px; letter-spacing:-.02em; }
.ww-kpi .sub { color:var(--muted); font-size:.82rem; margin-top:3px; }

.ww-tile { background:var(--surface); border:1px solid var(--line); border-radius:18px; overflow:hidden; box-shadow:var(--shadow);
  display:flex; flex-direction:column; transition:transform .18s, border-color .18s; }
.ww-tile:hover { transform:translateY(-3px); border-color:var(--accent-line); }
.ww-tile .banner { position:relative; height:132px; display:flex; align-items:center; justify-content:center; font-size:3.4rem; }
.ww-badge { position:absolute; left:12px; top:12px; background:rgba(15,23,42,.78); color:#f8fafc; font-size:.74rem; font-weight:700;
  padding:5px 11px; border-radius:999px; backdrop-filter:blur(6px); }
.ww-tile .body { padding:16px 18px 18px; display:flex; flex-direction:column; gap:6px; flex:1; }
.ww-tile .name { font-weight:700; color:var(--text); font-size:1.02rem; }
.ww-tile .tip { color:var(--muted); font-size:.86rem; line-height:1.5; flex:1; }
.ww-tile .meta { display:flex; justify-content:space-between; align-items:flex-end; margin-top:8px; }
.ww-tile .meta .k { color:var(--muted); font-size:.68rem; font-weight:700; letter-spacing:.09em; text-transform:uppercase; }
.ww-tile .meta .v { color:var(--accent); font-size:1.35rem; font-weight:800; }
.ww-tile .thumb { height:170px; background:var(--img-bg) center/cover no-repeat; position:relative; }
.ww-tile .thumb .ww-badge { top:auto; bottom:12px; }

.ww-class { border-left:4px solid var(--c); }
.ww-class .head { display:flex; justify-content:space-between; align-items:center; }
.ww-class .name { font-weight:700; color:var(--text); }
.ww-class .count { font-weight:800; font-size:1.7rem; color:var(--c); }
.ww-class .tip { color:var(--muted); font-size:.84rem; margin-top:6px; line-height:1.5; }

.ww-step .n { width:36px; height:36px; border-radius:12px; background:var(--accent-soft); color:var(--accent); display:flex;
  align-items:center; justify-content:center; font-weight:800; margin-bottom:12px; box-shadow:inset 0 0 0 1px var(--accent-line); }
.ww-step .t { font-weight:700; color:var(--text); }
.ww-step .d { color:var(--muted); font-size:.88rem; margin-top:5px; line-height:1.55; }

/* ---------------- Pills / notes / empty ---------------- */
.ww-pill { display:inline-flex; align-items:center; gap:7px; padding:5px 12px; border-radius:999px; font-size:.74rem; font-weight:700;
  letter-spacing:.05em; text-transform:uppercase; white-space:nowrap; }
.ww-pill i { width:7px; height:7px; border-radius:50%; background:currentColor; display:inline-block; }
.ww-ok { background:var(--ok-bg); color:var(--ok-fg); } .ww-warn { background:var(--warn-bg); color:var(--warn-fg); }
.ww-bad { background:var(--bad-bg); color:var(--bad-fg); } .ww-neutral { background:var(--surface2); color:var(--muted); }
.ww-note { background:var(--warn-bg); border:1px solid color-mix(in srgb, var(--warn-fg) 35%, transparent); color:var(--warn-fg);
  border-radius:14px; padding:13px 17px; font-size:.88rem; line-height:1.55; }
.ww-note b { color:inherit; }
.ww-empty { border:1.5px dashed var(--accent-line); background:var(--accent-soft); border-radius:20px; padding:54px 20px; text-align:center; }
.ww-empty .big { font-size:2.6rem; } .ww-empty .t { font-weight:700; color:var(--text); font-size:1.08rem; margin-top:8px; }
.ww-empty .s { color:var(--muted); font-size:.9rem; margin-top:4px; }

/* ---------------- Table ---------------- */
.ww-tablewrap { background:var(--surface); border:1px solid var(--line); border-radius:18px; overflow:auto; box-shadow:var(--shadow); }
table.ww-table { width:100%; border-collapse:collapse; font-size:.92rem; }
.ww-table th { text-align:left; padding:14px 18px; color:var(--muted); font-size:.7rem; letter-spacing:.1em; text-transform:uppercase;
  font-weight:700; background:var(--surface2); border-bottom:1px solid var(--line); white-space:nowrap; }
.ww-table td { padding:14px 18px; color:var(--text); border-bottom:1px solid var(--line); white-space:nowrap; }
.ww-table tr:last-child td { border-bottom:none; }
.ww-table td.b { font-weight:700; } .ww-table td.m { color:var(--muted); }
.ww-bar { display:inline-block; vertical-align:middle; width:96px; height:7px; background:var(--surface2); border-radius:9px; margin-right:10px; overflow:hidden; }
.ww-bar i { display:block; height:100%; background:linear-gradient(90deg,var(--accent),var(--accent-hi)); border-radius:9px; }
.ww-dot { width:9px; height:9px; border-radius:50%; display:inline-block; margin-right:8px; background:var(--c); }

/* ---------------- Footer ---------------- */
.ww-foot { margin-top:48px; padding-top:22px; border-top:1px solid var(--line); display:flex; justify-content:space-between;
  align-items:center; flex-wrap:wrap; gap:12px; color:var(--muted); font-size:.84rem; }

/* ---------------- Native widgets ---------------- */
div[data-baseweb="input"] > div, div[data-baseweb="base-input"], div[data-baseweb="select"] > div, textarea {
  background:var(--surface2) !important; border-color:var(--line) !important; border-radius:12px !important; }
div[data-baseweb="input"] input, div[data-baseweb="select"] div { color:var(--text) !important; -webkit-text-fill-color:var(--text) !important; }
[data-testid="stFileUploaderDropzone"] { background:var(--accent-soft) !important; border:1.5px dashed var(--accent-line) !important; border-radius:18px !important; padding:26px !important; }
[data-testid="stFileUploaderDropzone"] * { color:var(--muted) !important; }
[data-testid="stFileUploaderDropzone"] button { background:var(--surface2) !important; border:1px solid var(--line) !important; color:var(--text) !important; border-radius:999px !important; }
[data-testid="stFileUploaderFile"] * , [data-testid="stFileUploaderFileName"] { color:var(--text) !important; }
[data-testid="stCameraInput"] > div, [data-testid="stCameraInput"] video { border-radius:16px; }
[data-testid="stExpander"] { background:var(--surface); border:1px solid var(--line) !important; border-radius:16px; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color:var(--text) !important; font-weight:600; }
[data-testid="stAlert"] { background:var(--surface2) !important; border:1px solid var(--line); border-radius:14px; }
[data-testid="stAlert"] * { color:var(--text) !important; }
[data-testid="stSpinner"] * { color:var(--muted) !important; }
div[data-testid="stImage"] img { border-radius:16px; border:1px solid var(--line); background:var(--img-bg); }
[data-testid="stSlider"] [data-testid="stTickBarMin"], [data-testid="stSlider"] [data-testid="stTickBarMax"] { color:var(--muted) !important; }

button[data-testid="stBaseButton-primary"], .stButton button[kind="primary"] {
  background:linear-gradient(135deg,var(--accent-hi),var(--accent)) !important; color:var(--on-accent) !important; border:none !important;
  border-radius:999px !important; font-weight:700 !important; padding:.62rem 1.4rem !important; box-shadow:0 10px 24px -10px var(--glow); }
button[data-testid="stBaseButton-primary"] *, .stButton button[kind="primary"] * { color:var(--on-accent) !important; }
button[data-testid="stBaseButton-primary"]:disabled { opacity:.45; box-shadow:none; }
button[data-testid="stBaseButton-secondary"], .stButton button[kind="secondary"], .stDownloadButton button {
  background:var(--surface2) !important; color:var(--text) !important; border:1px solid var(--line) !important;
  border-radius:999px !important; font-weight:600 !important; padding:.5rem 1.2rem !important; }
button[data-testid="stBaseButton-secondary"] *, .stButton button[kind="secondary"] *, .stDownloadButton button * { color:var(--text) !important; }
button[data-testid="stBaseButton-secondary"]:hover, .stDownloadButton button:hover { border-color:var(--accent-line) !important; }
@media (max-width:760px){ .ww-hero{padding:28px 22px;} .ww-hero h1{font-size:2.2rem;} .ww-title{font-size:1.7rem;} }
"""
