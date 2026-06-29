#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_report.py  --  visual HTML report generator for the `drug-intel` skill.

    python scripts/build_report.py <data.json> -o <output.html>

Reads a structured JSON document (schema: templates/report_schema.json) that Claude
fills in AFTER fetch_drug_data.py + web + the pause gates, and renders a single,
self-contained HTML file (inline CSS + inline SVG, NO runtime deps, opens offline,
prints cleanly to PDF).

Rules (match SKILL.md): every value keeps its badge(s); red stays loud; the
"需人工核对清单" block is always rendered; all source links are collected into a
final "参考来源 (Reference list)" section. Pretty never overrides honest.

Badge keys: official(🏛️官方·facts only) | db(✅库) | web(🔍web) | weak(⚠️) | redflag(🔴) | na(❓N/A)
"""

import sys
import json
import html
import argparse
from datetime import datetime, timezone

BADGES = {
    "official": ("\U0001F3DB️官方", "b-official"),
    "db":       ("✅库",  "b-db"),
    "web":      ("\U0001F50Dweb", "b-web"),
    "weak":     ("⚠️存疑", "b-weak"),
    "redflag":  ("\U0001F534必核", "b-red"),
    "na":       ("❓N/A",  "b-na"),
}
ALIASES = {
    "fda": "official", "gov": "official", "company": "official", "regulator": "official",
    "database": "db", "pubchem": "db", "chembl": "db", "ctgov": "db", "openfda": "db",
    "media": "web", "secondary": "weak", "unknown": "na", "notfound": "na", "red": "redflag",
}
BADGE_FILL = {
    "official": "#1d4ed8", "db": "#15803d", "web": "#0e7490",
    "weak": "#b45309", "redflag": "#dc2626", "na": "#6b7280",
}


def _norm(key):
    if not key:
        return None
    k = str(key).strip()
    return k if k in BADGES else ALIASES.get(k.lower(), None)


def chip(key):
    nk = _norm(key)
    if not nk:
        return ""
    label, cls = BADGES[nk]
    return '<span class="chip {}">{}</span>'.format(cls, html.escape(label))


def chips(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "".join(chip(v) for v in value)
    return chip(value)


def esc(x):
    return html.escape("" if x is None else str(x))


def _badge_color(badge):
    if isinstance(badge, (list, tuple)):
        for pref in ("redflag", "official", "db", "web", "weak", "na"):
            if any(_norm(b) == pref for b in badge):
                return BADGE_FILL[pref]
        return "#334155"
    return BADGE_FILL.get(_norm(badge), "#334155")


def date_to_float(d):
    if not d:
        return None
    parts = str(d).split("-")
    try:
        y = int(parts[0])
    except ValueError:
        return None
    m = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
    day = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
    return y + (m - 1) / 12.0 + (day - 1) / 365.0


def _is_us(region):
    r = (region or "")
    return r in ("US", "us", "美国") or r.lower().startswith("us")


# --------------------------------------------------------------------------- #
def render_header(meta, identity):
    inn = esc(meta.get("inn") or meta.get("name") or "未命名药物")
    cn = esc(meta.get("cn_name") or "")
    brand_us = esc(meta.get("brand_us") or "")
    brand_cn = esc(meta.get("brand_cn") or "")
    codes = meta.get("codes") or []
    codes_s = esc(" / ".join(codes)) if codes else ""
    mode = esc(meta.get("mode") or "")
    gen = esc(meta.get("generated") or datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    cmd = esc(meta.get("script_cmd") or "")

    sub_bits = []
    if cn:
        sub_bits.append(cn)
    if brand_us:
        sub_bits.append("\U0001F1FA\U0001F1F8 " + brand_us)
    if brand_cn:
        sub_bits.append("\U0001F1E8\U0001F1F3 " + brand_cn)
    if codes_s:
        sub_bits.append(codes_s)
    sub = "  ·  ".join(sub_bits)

    rows = ""
    for item in (identity or []):
        rows += '<tr><td class="k">{}</td><td class="v">{} {}</td></tr>'.format(
            esc(item.get("field")), esc(item.get("value")), chips(item.get("badge")))
    id_table = '<table class="idtable"><tbody>{}</tbody></table>'.format(rows) if rows else ""

    skip = ""
    if meta.get("skipped_gates"):
        skip = ('<div class="banner red">⚠️ 已按用户要求"一次跑完"，未逐项停下确认；'
                '下面所有标 \U0001F534 的地方都还没经过人工核对。</div>')

    meta_bits = ["生成时间 " + gen]
    if mode:
        meta_bits.append("口径：" + mode)
    if cmd:
        meta_bits.append("数据脚本 <code>" + cmd + "</code>")
    meta_line = "  ·  ".join(meta_bits)

    return """
<header class="hero">
  <div class="hero-eyebrow">药物研发竞争情报 · 美国 \U0001F1FA\U0001F1F8 + 中国 \U0001F1E8\U0001F1F3</div>
  <h1>{inn}</h1>
  <div class="hero-sub">{sub}</div>
  <div class="hero-meta">{meta_line}</div>
  <div class="banner amber">⚠️ 仅供研发情报参考，<b>非医疗建议、非投资建议</b>。所有标 \U0001F534 的字段必须人工复核后再使用。</div>
  {skip}
  {id_table}
</header>
""".format(inn=inn, sub=sub, meta_line=meta_line, skip=skip, id_table=id_table)


def render_legend():
    notes = {
        "official": "政府/监管/企业官网的客观事实 · 最高可信",
        "db": "权威数据库可核实", "web": "联网检索（附链接）",
        "weak": "来源存疑/单一弱源", "redflag": "高幻觉 · 必须人工核对",
        "na": "查过但确实没找到",
    }
    items = ""
    for k in ("official", "db", "web", "weak", "redflag", "na"):
        items += '<div class="legend-item">{} <span class="legend-note">{}</span></div>'.format(
            chip(k), esc(notes[k]))
    return '<section class="card"><h2>徽标说明</h2><div class="legend-grid">{}</div></section>'.format(items)


def render_kv_section(title, sub_id, items, accent="#94a3b8"):
    if not items:
        return ""
    lis = ""
    for it in items:
        if isinstance(it, str):
            lis += "<li>{}</li>".format(esc(it))
            continue
        label = it.get("label") or it.get("field")
        text = it.get("text") or it.get("value") or ""
        body = ("<b>{}：</b>".format(esc(label)) if label else "") + esc(text)
        lis += "<li>{} {}</li>".format(body, chips(it.get("badge")))
    return ('<section class="card" id="{}" style="--accent:{}"><h2>{}</h2>'
            '<ul class="bullets">{}</ul></section>').format(sub_id, accent, esc(title), lis)


def render_companies(companies):
    if not companies:
        return ""

    def field(c, key):
        v = c.get(key)
        if isinstance(v, dict):
            return esc(v.get("value")), chips(v.get("badge"))
        return esc(v), chips(c.get(key + "_badge"))

    def block(flag, label, c, accent):
        if not c:
            return ""
        ov, ob = field(c, "originator")
        hv, hb = field(c, "holder")
        return ('<div class="co-card" style="border-top-color:{ac}"><div class="co-head">{flag} {label}</div>'
                '<div class="co-row"><span class="co-k">原研</span><span class="co-v">{ov} {ob}</span></div>'
                '<div class="co-row"><span class="co-k">当前权利人 / 上市持有人</span><span class="co-v">{hv} {hb}</span></div></div>'
                ).format(ac=accent, flag=flag, label=esc(label), ov=ov, ob=ob, hv=hv, hb=hb)
    us = block("\U0001F1FA\U0001F1F8", "美国", companies.get("us"), "#1d4ed8")
    cn = block("\U0001F1E8\U0001F1F3", "中国", companies.get("china"), "#dc2626")
    return ('<section class="card"><h2>厂家（原研 / 权利人 / 上市持有人）</h2>'
            '<div class="co-grid">{}{}</div></section>').format(us, cn)


def render_timeline(events):
    """Clean vertical timeline: 美国 left/blue, 中国 right/red. No horizontal clipping."""
    if not events:
        return ""
    ev = [e for e in events if e.get("date")]
    ev.sort(key=lambda e: (date_to_float(e.get("date")) or 0))
    items = ""
    for e in ev:
        us = _is_us(e.get("region"))
        side = "left" if us else "right"
        flag = "\U0001F1FA\U0001F1F8 美国" if us else "\U0001F1E8\U0001F1F3 中国"
        color = _badge_color(e.get("badge"))
        trial = e.get("trial")
        sub_bits = []
        if trial:
            sub_bits.append(esc(trial))
        sub = " · ".join(sub_bits)
        sub_html = ('<div class="tl-sub">{} {}</div>'.format(sub, chips(e.get("badge")))
                    if (sub or e.get("badge")) else "")
        items += (
            '<div class="tl-item {side}">'
            '<span class="tl-dot" style="background:{color};box-shadow:0 0 0 2px {color}"></span>'
            '<div class="tl-card" style="border-left-color:{color}">'
            '<div class="tl-meta"><span class="tl-date">{date}</span>'
            '<span class="tl-flag">{flag}</span></div>'
            '<div class="tl-title">{label}</div>{sub}</div></div>'
        ).format(side=side, color=color, date=esc(e.get("date")), flag=flag,
                 label=esc(e.get("label", "")), sub=sub_html)
    note = ('<p class="note">左=🇺🇸 美国（蓝），右=🇨🇳 中国（红）。卡片色条 = 来源徽标颜色'
            '（蓝=🏛️官方、绿=✅库、青=🔍web、琥珀=⚠️、红=🔴）。中国侧默认 🔴，请到 NMPA 核对。</p>')
    return ('<section class="card"><h2>研发 / 审批时间线</h2>'
            '<div class="timeline">{}</div>{}</section>').format(items, note)


def _status_class(status):
    s = status or ""
    if "已上市" in s:
        return "st-on"
    if "未" in s or "N/A" in s or "❓" in s or "—" in s:
        return "st-off"
    return "st-mid"


def render_indications(rows):
    if not rows:
        return ""
    trs = ""
    for r in rows:
        def cell(c):
            if not c:
                return '<td class="ind-cell"><span class="status st-off">—</span></td>'
            status = esc(c.get("status"))
            pill = '<span class="status {}">{}</span>'.format(_status_class(c.get("status")), status)
            trial = c.get("trial")
            tline = '<div class="ind-trial">{}</div>'.format(esc(trial)) if trial else ""
            return '<td class="ind-cell">{} {}{}</td>'.format(pill, chips(c.get("badge")), tline)
        trs += "<tr><th class='ind-name'>{}</th>{}{}</tr>".format(
            esc(r.get("indication")), cell(r.get("us")), cell(r.get("china")))
    return ('<section class="card"><h2>适应症矩阵（按地区）</h2>'
            '<table class="matrix"><thead><tr><th>适应症</th>'
            '<th>\U0001F1FA\U0001F1F8 美国</th><th>\U0001F1E8\U0001F1F3 中国</th></tr></thead>'
            '<tbody>{}</tbody></table>'
            '<p class="note">格内：状态 + 徽标 + 关键(pivotal)试验。试验编号是否为"上市依据"属 \U0001F534，'
            '请以官方说明书 / CDE 核对。</p></section>').format(trs)


def render_sales(sales):
    if not sales or not sales.get("points"):
        return ""
    pts = sales["points"]
    unit = esc(sales.get("unit") or "")
    source = sales.get("source") or ""
    vals = [float(p.get("value") or 0) for p in pts]
    vmax = max(vals + [1.0])
    n = len(pts)
    width, height = 880, 300
    pad_l, pad_b, pad_t, pad_r = 52, 50, 30, 18
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    slot = plot_w / max(n, 1)
    bar_w = min(96, slot * 0.5)

    parts = ['<svg viewBox="0 0 {} {}" width="100%" role="img" aria-label="销售趋势">'.format(width, height)]
    parts.append('<defs><pattern id="hatch" width="7" height="7" patternTransform="rotate(45)" '
                 'patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="0" y2="7" stroke="#cbd5e1" stroke-width="3"/></pattern>'
                 '<linearGradient id="barg" x1="0" y1="0" x2="0" y2="1">'
                 '<stop offset="0" stop-color="#ef4444"/><stop offset="1" stop-color="#dc2626"/></linearGradient></defs>')
    for i in range(5):
        gy = pad_t + plot_h * i / 4.0
        val = vmax * (1 - i / 4.0)
        parts.append('<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" stroke="#eef2f7" stroke-width="1"/>'.format(
            pad_l, gy, width - pad_r, gy))
        parts.append('<text x="{:.1f}" y="{:.1f}" class="ax-y">{:.1f}</text>'.format(pad_l - 8, gy + 4, val))
    parts.append('<line x1="{0}" y1="{1:.1f}" x2="{2}" y2="{1:.1f}" stroke="#cbd5e1" stroke-width="1.5"/>'.format(
        pad_l, pad_t + plot_h, width - pad_r))
    for i, p in enumerate(pts):
        v = float(p.get("value") or 0)
        cx = pad_l + slot * (i + 0.5)
        bh = (v / vmax) * plot_h if vmax else 0
        by = pad_t + plot_h - bh
        forecast = bool(p.get("forecast"))
        fill = "url(#hatch)" if forecast else "url(#barg)"
        stroke = "#94a3b8" if forecast else "#b91c1c"
        parts.append('<rect x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" rx="4" fill="{}" stroke="{}" stroke-width="1"/>'.format(
            cx - bar_w / 2, by, bar_w, max(bh, 0), fill, stroke))
        note = esc(p.get("note") or "")
        top = "{}{}".format(p.get("value"), (" " + note) if note else "")
        parts.append('<text x="{:.1f}" y="{:.1f}" class="bar-val">{} <tspan fill="#dc2626">●</tspan></text>'.format(
            cx, by - 8, esc(top)))
        yr = esc(p.get("year")) + ("(预测)" if forecast else "")
        parts.append('<text x="{:.1f}" y="{:.1f}" class="ax-x">{}</text>'.format(cx, pad_t + plot_h + 20, yr))
    parts.append("</svg>")
    src = '<p class="note">来源：{}</p>'.format(esc(source)) if source else ""
    return ('<section class="card" id="sales"><h2>销售趋势 '
            '<span class="forced-red">\U0001F534 财报口径 · 每个数字都须人工复核</span></h2>'
            '<p class="note">单位：{}（斜纹柱 = 预测值/forecast，非实际入账；红点 = 强制人工核对）。</p>'
            '<div class="chart">{}</div>{}</section>').format(unit, "".join(parts), src)


def render_checklist(items):
    items = items or []
    trs = ""
    for i, it in enumerate(items, 1):
        trs += ("<tr><td class='num'>{}</td><td>{}</td><td>{} {}</td><td>{}</td><td>{}</td></tr>".format(
            i, esc(it.get("field")), esc(it.get("value")), chips(it.get("badge")),
            esc(it.get("why")), esc(it.get("where"))))
    return ('<section class="card checklist"><h2>\U0001F534 需人工核对清单 '
            '<span class="ck-tag">本工具最关键产出</span></h2>'
            '<table class="ck-table"><thead><tr><th>#</th><th>字段</th><th>当前值 / 状态</th>'
            '<th>为什么要核</th><th>建议去哪个官方源核</th></tr></thead><tbody>{}</tbody></table></section>').format(trs)


def render_references(refs):
    if not refs:
        return ""
    lis = ""
    for r in refs:
        if isinstance(r, str):
            url, label, badge = r, r, None
        else:
            url = r.get("url") or ""
            label = r.get("label") or url
            badge = r.get("badge")
        href = '<a href="{u}" target="_blank" rel="noopener">{l}</a>'.format(u=esc(url), l=esc(label))
        urlspan = '<div class="ref-url">{}</div>'.format(esc(url)) if url else ""
        lis += "<li>{} {}{}</li>".format(href, chips(badge), urlspan)
    return ('<section class="card refs" id="references"><h2>参考来源（Reference list）</h2>'
            '<p class="note">下列为本报告所有引用链接的汇总；请优先以 🏛️官方 来源核对客观事实。</p>'
            '<ol class="reflist">{}</ol></section>').format(lis)


CSS = """
:root{
  --ink:#1f2937; --muted:#6b7280; --line:#e5e7eb; --soft:#f1f5f9; --bg:#f8fafc;
  --official:#1d4ed8; --db:#15803d; --web:#0e7490; --weak:#b45309; --red:#dc2626; --na:#6b7280;
  --accent:#94a3b8;
}
*{box-sizing:border-box;}
body{font-family:ui-sans-serif,-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",Roboto,Helvetica,Arial,sans-serif;
  color:var(--ink); background:var(--bg); margin:0; padding:28px 18px; line-height:1.6; -webkit-font-smoothing:antialiased;}
.wrap{max-width:880px; margin:0 auto; display:flex; flex-direction:column; gap:18px;}
.hero{background:#fff; border:1px solid var(--line); border-radius:16px; padding:26px 30px;
  box-shadow:0 1px 2px rgba(16,24,40,.04);}
.hero-eyebrow{font-size:12.5px; font-weight:600; letter-spacing:.04em; color:#475569; text-transform:none;}
h1{font-size:27px; line-height:1.2; margin:6px 0 2px; font-weight:700; color:#0f172a;}
.hero-sub{color:#334155; font-size:14.5px; margin-top:4px;}
.hero-meta{color:var(--muted); font-size:12.5px; margin-top:6px;}
.hero-meta code{background:var(--soft); padding:1px 6px; border-radius:5px; font-size:11.5px;}
.banner{margin-top:14px; padding:10px 14px; border-radius:10px; font-size:13.5px;}
.banner.amber{background:#fffbeb; border:1px solid #fde68a; color:#92400e;}
.banner.red{background:#fef2f2; border:1px solid #fecaca; color:#991b1b; font-weight:600;}
.card{background:#fff; border:1px solid var(--line); border-radius:16px; padding:22px 26px;
  box-shadow:0 1px 2px rgba(16,24,40,.04);}
h2{font-size:17px; font-weight:700; color:#0f172a; margin:0 0 14px; padding-left:11px;
  border-left:4px solid var(--accent); line-height:1.25;}
.idtable{width:100%; border-collapse:collapse; margin-top:16px; font-size:13.5px;}
.idtable td{border:1px solid var(--line); padding:8px 11px; vertical-align:top; overflow-wrap:anywhere;}
.idtable .k{width:180px; background:var(--soft); font-weight:600; color:#374151;}
.chip{display:inline-block; font-size:11px; font-weight:700; color:#fff; padding:2px 8px;
  border-radius:999px; margin:0 2px; vertical-align:middle; white-space:nowrap;}
.b-official{background:var(--official);} .b-db{background:var(--db);} .b-web{background:var(--web);}
.b-weak{background:var(--weak);} .b-red{background:var(--red);} .b-na{background:var(--na);}
.legend-grid{display:grid; grid-template-columns:repeat(2,1fr); gap:9px 20px;}
.legend-item{font-size:13px;} .legend-note{color:var(--muted); margin-left:6px;}
.bullets{margin:2px 0; padding-left:20px;} .bullets li{margin:7px 0; font-size:14px;}
.note{color:var(--muted); font-size:12.5px; margin:12px 0 0;}
.co-grid{display:grid; grid-template-columns:repeat(2,1fr); gap:16px;}
.co-card{border:1px solid var(--line); border-top:3px solid; border-radius:12px; padding:14px 16px;
  background:#fff; overflow-wrap:anywhere;}
.co-head{font-weight:700; margin-bottom:9px; font-size:14.5px;}
.co-row{font-size:13px; margin:7px 0;}
.co-k{display:block; color:var(--muted); font-size:11.5px; margin-bottom:1px;}
.co-v{display:block;}
/* vertical timeline */
.timeline{position:relative; padding:4px 0; margin-top:4px;}
.timeline::before{content:""; position:absolute; left:50%; top:6px; bottom:6px; width:2px;
  background:linear-gradient(#bfdbfe,#e5e7eb,#fecaca); transform:translateX(-1px);}
.tl-item{position:relative; width:50%; padding:7px 0; display:flex;}
.tl-item.left{left:0; justify-content:flex-end; padding-right:30px;}
.tl-item.right{left:50%; justify-content:flex-start; padding-left:30px;}
.tl-dot{position:absolute; top:16px; width:12px; height:12px; border-radius:50%; border:2px solid #fff; z-index:2;}
.tl-item.left .tl-dot{right:-6px;} .tl-item.right .tl-dot{left:-6px;}
.tl-card{border:1px solid var(--line); border-left:4px solid; border-radius:11px; padding:9px 13px;
  background:#fff; max-width:340px; box-shadow:0 1px 2px rgba(16,24,40,.05);}
.tl-meta{display:flex; gap:8px; align-items:baseline; flex-wrap:wrap;}
.tl-date{font-weight:700; font-size:12.5px; color:#0f172a;}
.tl-flag{font-size:11px; color:var(--muted);}
.tl-title{font-size:13.5px; margin:3px 0 2px; font-weight:600;}
.tl-sub{font-size:11.5px; color:var(--muted);}
.matrix{width:100%; border-collapse:collapse; font-size:13.5px;}
.matrix th,.matrix td{border:1px solid var(--line); padding:10px 12px; text-align:left; vertical-align:top; overflow-wrap:anywhere;}
.matrix thead th{background:var(--soft);}
.ind-name{background:var(--soft); font-weight:600; width:34%;}
.status{display:inline-block; font-size:11.5px; font-weight:700; padding:2px 9px; border-radius:999px;}
.st-on{background:#dcfce7; color:#166534;} .st-mid{background:#fef3c7; color:#92400e;} .st-off{background:#f1f5f9; color:#64748b;}
.ind-trial{font-size:11.5px; color:var(--muted); margin-top:5px;}
.chart{border:1px solid var(--line); border-radius:12px; padding:12px; background:#fff;}
.bar-val{font-size:11px; fill:#b91c1c; text-anchor:middle; font-weight:700;}
.ax-y{font-size:11px; fill:#94a3b8; text-anchor:end;}
.ax-x{font-size:12px; fill:#374151; text-anchor:middle;}
.forced-red{font-size:12px; background:#fef2f2; color:#dc2626; border:1px solid #fecaca;
  padding:2px 9px; border-radius:999px; font-weight:700; margin-left:8px; white-space:nowrap;}
.checklist{border:2px solid #fecaca; background:#fffafa;}
.checklist h2{border-left-color:#dc2626; color:#991b1b;}
.ck-tag{font-size:12px; background:#dc2626; color:#fff; padding:2px 10px; border-radius:999px; margin-left:8px; font-weight:600;}
.ck-table{width:100%; border-collapse:collapse; font-size:13px;}
.ck-table th,.ck-table td{border:1px solid #fecaca; padding:9px 11px; text-align:left; vertical-align:top; overflow-wrap:anywhere;}
.ck-table thead th{background:#fee2e2; color:#991b1b;}
.ck-table .num{width:26px; text-align:center; color:#991b1b; font-weight:700;}
.refs .reflist{margin:6px 0 0; padding-left:22px;}
.refs .reflist li{margin:9px 0; font-size:13px;}
.refs a{color:#1d4ed8; text-decoration:none; font-weight:600;}
.refs a:hover{text-decoration:underline;}
.ref-url{font-size:11px; color:var(--muted); word-break:break-all; margin-top:1px;}
footer{color:var(--muted); font-size:12px; text-align:center; padding:4px 0 8px;}
@page{ size:A4; margin:12mm; }
@media print{
  body{background:#fff; padding:0;}
  .wrap{gap:14px; max-width:100%;}
  .hero,.card{box-shadow:none; break-inside:avoid;}
  .co-grid,.legend-grid{grid-template-columns:1fr 1fr;}
  .tl-item{break-inside:avoid;}
  .checklist{break-inside:avoid;}
}
"""


def build_html(data):
    meta = data.get("meta", {})
    title = esc(meta.get("inn") or meta.get("name") or "药物情报报告")
    parts = [
        render_header(meta, data.get("identity")),
        render_legend(),
        render_companies(data.get("companies")),
        render_kv_section("作用机制（MoA）", "moa", data.get("moa"), "#0e7490"),
        render_timeline(data.get("timeline")),
        render_indications(data.get("indications")),
        render_kv_section("简介", "intro", data.get("intro"), "#64748b"),
        render_sales(data.get("sales")),
        render_kv_section("专利 / 独占到期（LOE）\U0001F534", "loe", data.get("loe"), "#dc2626"),
        render_kv_section("仿制药 / 生物类似药上市？", "generics", data.get("generics"), "#15803d"),
        render_kv_section("同类药品", "peers", data.get("peers"), "#0e7490"),
        render_kv_section("核心优势（AI 总结 · \U0001F534 跨试验比较不严谨）", "advantages", data.get("advantages"), "#dc2626"),
        render_checklist(data.get("checklist")),
        render_references(data.get("references")),
    ]
    body = "\n".join(p for p in parts if p)
    foot = esc(meta.get("footer") or
               "drug-intel · 仅供研发情报参考，非医疗/投资建议 · 标 \U0001F534 项请以官方源人工复核为准。")
    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>药物情报报告 · {title}</title>
<style>{css}</style>
</head><body>
<div class="wrap">
{body}
<footer>{foot}</footer>
</div>
</body></html>""".format(title=title, css=CSS, body=body, foot=foot)


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Render a drug-intel visual HTML report from a JSON data file.")
    ap.add_argument("data", help="path to the JSON data file (schema: templates/report_schema.json)")
    ap.add_argument("-o", "--out", default=None, help="output .html path (default: alongside the data file)")
    args = ap.parse_args(argv)
    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)
    html_str = build_html(data)
    out = args.out or (args.data.rsplit(".", 1)[0] + ".html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_str)
    print("Wrote {} ({:.1f} KB)".format(out, len(html_str.encode("utf-8")) / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
