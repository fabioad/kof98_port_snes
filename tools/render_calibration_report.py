#!/usr/bin/env python3
"""Render a frozen calibration snapshot into a self-contained HTML report
and/or a Codex .canvas.tsx.  Presentation only: reads the snapshot JSON as
captured, never recomputes metrics, catalogs, or ROM state.

Usage:
    render_calibration_report.py --snapshot SNAPSHOT.json
                                 [--html index.html] [--canvas out.canvas.tsx]
"""
import argparse
import json
import os

STATUS_LABELS = {
    "needs_repair": "Ainda não é release",
    "applied": "Calibração aplicada",
    "current": "Perfis atuais",
}

DISCLAIMERS = [
    "native slots ≠ distinct Arcade moves",
    "source elements ≠ unique images ≠ actual VBlanks",
    "cold upload bounds are hypothetical lower bounds",
]


def project(snapshot):
    """Trim the snapshot to display fields only."""
    chars = []
    rows = []
    for ci, c in enumerate(snapshot["characters"]):
        chars.append({
            "name": c["name"],
            "display": c.get("display", c["name"]),
            "storage": c.get("storage"),
            "profile": c.get("profile_status"),
            "normal": len(c.get("normal_sids") or []),
            "special": len(c.get("special_sids") or []),
            "super": len(c.get("super_sids") or []),
            "errors": c.get("errors", 0),
            "warnings": c.get("warnings_or_review", 0),
            "diagnostics": [
                {"level": d.get("level"), "issue": d.get("issue"),
                 "sid": d.get("sid")}
                for d in (c.get("diagnostics") or [])
            ],
        })
        for r in c["rows"]:
            proj = None
            if r.get("projectile"):
                proj = "projectile"
            elif r.get("projectile_config"):
                proj = "projectile_config"
            elif r.get("projectile_source") is not None:
                proj = "projectile_source"
            combat = r.get("combat") or {}
            rows.append({
                "c": ci,
                "sid": r.get("sid"),
                "state": r.get("state"),
                "action": r.get("action"),
                "cat": r.get("category"),
                "wired": 1 if r.get("wired") else 0,
                "cmds": ",".join(r.get("commands") or []),
                "se": r.get("source_elements"),
                "si": r.get("source_images"),
                "st": r.get("source_ticks"),
                "ge": r.get("generated_elements"),
                "gt": r.get("generated_ticks"),
                "dmg": combat.get("damage"),
                "proj": proj,
                "sf": [[f.get("group"), f.get("number"), f.get("ticks")]
                       for f in (r.get("source_frames") or [])],
                "gf": [[f.get("sprite_id"), f.get("ticks"),
                        f.get("upload_bytes"),
                        f.get("upload_vblanks_lower_bound"),
                        1 if f.get("upload_exceeds_frame_ticks") else 0]
                       for f in (r.get("frames") or [])],
            })
    return {
        "status": snapshot.get("status"),
        "captured_at": snapshot.get("captured_at"),
        "scope": snapshot.get("scope"),
        "counts": snapshot.get("counts") or {},
        "limits": snapshot.get("limits") or [],
        "artifacts": snapshot.get("artifacts") or {},
        "evidence": snapshot.get("evidence") or {},
        "chars": chars,
        "rows": rows,
    }


CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--muted:#666;--line:#d8d8d8;--accent:#005fcc;
--err:#b3261e;--warn:#8a5a00;--ok:#1a7f37;}
@media(prefers-color-scheme:dark){:root{--bg:#141414;--fg:#e6e6e6;
--muted:#999;--line:#3a3a3a;--accent:#5ea0ff;--err:#ff7b72;--warn:#e0a33c;
--ok:#5ad07e;}}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font-family:system-ui,sans-serif;
margin:0;padding:16px 20px;max-width:1400px}
h1{font-size:1.25rem;margin:0 0 4px}h2{font-size:1rem;margin:24px 0 8px}
.meta{color:var(--muted);font-size:.8rem;margin-bottom:4px}
.num,td.n{font-family:ui-monospace,Consolas,monospace;font-variant-numeric:
tabular-nums}
table{border-collapse:collapse;width:100%;font-size:.8rem}
th,td{border:1px solid var(--line);padding:3px 8px;text-align:left;
white-space:nowrap}
th{background:color-mix(in srgb,var(--fg) 6%,var(--bg));position:sticky;top:0}
.wrap{overflow-x:auto}
tr:hover td{background:color-mix(in srgb,var(--fg) 4%,var(--bg))}
.pill{display:inline-block;border:1px solid var(--accent);color:var(--accent);
padding:0 8px;border-radius:999px;font-size:.72rem;cursor:pointer;
background:none;margin:0 4px 4px 0}
.pill.on{background:var(--accent);color:var(--bg)}
.err{color:var(--err)}.warn{color:var(--warn)}.ok{color:var(--ok)}
input,select{background:var(--bg);color:var(--fg);border:1px solid var(--line);
padding:4px 8px;font-size:.85rem;margin:0 8px 8px 0}
.status{font-size:1rem;border:1px solid var(--err);color:var(--err);
padding:6px 12px;display:inline-block;margin:8px 0}
.stats{display:flex;gap:24px;flex-wrap:wrap;margin:8px 0}
.stats div b{display:block;font-family:ui-monospace,Consolas,monospace;
font-size:1.1rem}
.stats div span{font-size:.72rem;color:var(--muted)}
.disc{color:var(--muted);font-size:.75rem;font-style:italic}
tr.sel td{outline:2px solid var(--accent);outline-offset:-2px}
.diag{font-size:.72rem;color:var(--muted)}
"""


JS = """
const CH = DATA.chars, ROWS = DATA.rows;
const CATS = [...new Set(ROWS.map(r=>r.cat))];
let q='', cat='', ci=-1, sel=null;
function fmt(v){return v==null?'—':v}
function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function overview(){
  let h='<div class="wrap"><table><tr><th>Char</th><th>Storage</th><th>Profile</th><th>Normal</th><th>Special</th><th>Super</th><th>Errors</th><th>Warn/Review</th><th>Diagnostics</th></tr>';
  CH.forEach((c,i)=>{
    const dg=(c.diagnostics||[]).map(d=>`<span class="${d.level==='error'?'err':'warn'}">${esc(d.issue)}${d.sid!=null?' sid'+d.sid:''}</span>`).join(' · ');
    h+=`<tr><td>${esc(c.display)}</td><td>${esc(c.storage)}</td><td>${esc(c.profile)}</td>`+
       `<td class="n">${c.normal}</td><td class="n">${c.special}</td><td class="n">${c.super}</td>`+
       `<td class="n ${c.errors?'err':''}">${c.errors}</td><td class="n ${c.warnings?'warn':''}">${c.warnings}</td>`+
       `<td class="diag">${dg}</td></tr>`;
  });
  document.getElementById('ov').innerHTML=h+'</table></div>';
}
function filters(){
  let h=`<input id="q" placeholder="search move/state/command" value="${esc(q)}">`;
  h+=CATS.map(c=>`<button class="pill ${cat===c?'on':''}" data-cat="${esc(c)}">${esc(c)}</button>`).join('');
  h+='<button class="pill" data-cat="">all</button>';
  h+=`<select id="cf"><option value="-1">all characters</option>`+CH.map((c,i)=>`<option value="${i}" ${i===ci?'selected':''}>${esc(c.display)}</option>`).join('')+'</select>';
  document.getElementById('flt').innerHTML=h;
  document.getElementById('q').oninput=e=>{q=e.target.value;moves()};
  document.getElementById('cf').onchange=e=>{ci=+e.target.value;moves()};
  document.querySelectorAll('#flt .pill').forEach(b=>b.onclick=()=>{cat=b.dataset.cat;filters();moves()});
}
function moves(){
  const lq=q.toLowerCase();
  const vis=ROWS.map((r,i)=>[r,i]).filter(([r])=>
    (ci<0||r.c===ci)&&(!cat||r.cat===cat)&&
    (!lq||String(r.sid).includes(lq)||String(r.state).includes(lq)||
     String(r.action).includes(lq)||(r.cmds||'').toLowerCase().includes(lq)||
     CH[r.c].display.toLowerCase().includes(lq)));
  let h=`<p class="meta">${vis.length} of ${ROWS.length} rows</p><div class="wrap"><table>`+
    '<tr><th>Char</th><th>SID</th><th>State</th><th>Action</th><th>Category</th><th>Wired</th><th>Cmds</th><th>SrcEl</th><th>SrcImg</th><th>SrcTick</th><th>GenEl</th><th>GenTicks</th><th>Dmg</th><th>Proj</th></tr>';
  vis.forEach(([r,i])=>{
    h+=`<tr data-i="${i}" class="${sel===i?'sel':''}" style="cursor:pointer">`+
      `<td>${esc(CH[r.c].display)}</td><td class="n">${fmt(r.sid)}</td><td class="n">${fmt(r.state)}</td><td class="n">${fmt(r.action)}</td>`+
      `<td>${esc(r.cat)}</td><td class="${r.wired?'ok':'err'}">${r.wired?'yes':'no'}</td><td>${esc(r.cmds)}</td>`+
      `<td class="n">${fmt(r.se)}</td><td class="n">${fmt(r.si)}</td><td class="n">${fmt(r.st)}</td>`+
      `<td class="n">${fmt(r.ge)}</td><td class="n">${fmt((r.gt||[]).join(','))}</td>`+
      `<td class="n">${fmt(r.dmg)}</td><td>${fmt(r.proj)}</td></tr>`;
  });
  document.getElementById('mv').innerHTML=h+'</table></div>';
  document.querySelectorAll('#mv tr[data-i]').forEach(t=>t.onclick=()=>{sel=+t.dataset.i;frames();moves()});
  frames();
}
function frames(){
  const el=document.getElementById('fr');
  if(sel==null){el.innerHTML='<p class="meta">select a move row for per-frame detail</p>';return}
  const r=ROWS[sel];
  let h=`<h2>Frames — ${esc(CH[r.c].display)} sid ${fmt(r.sid)} / state ${fmt(r.state)} / action ${fmt(r.action)}</h2>`;
  h+='<div class="wrap"><table><tr><th>#</th><th>Src grp,num</th><th>Src ticks</th><th>Gen sprite</th><th>Gen ticks</th><th>Upload B</th><th>VBlank LB*</th></tr>';
  const n=Math.max(r.sf.length,r.gf.length);
  for(let i=0;i<n;i++){
    const s=r.sf[i]||[],g=r.gf[i]||[];
    h+=`<tr><td class="n">${i}</td><td class="n">${s.length?s[0]+','+s[1]:'—'}</td><td class="n">${fmt(s[2])}</td>`+
       `<td class="n">${fmt(g[0])}</td><td class="n">${fmt(g[1])}</td><td class="n">${fmt(g[2])}</td>`+
       `<td class="n ${g[4]?'err':''}">${fmt(g[3])}${g[4]?' !':''}</td></tr>`;
  }
  el.innerHTML=h+'</table></div><p class="disc">*cold upload lower bound is hypothetical; ! = upload exceeds frame ticks</p>';
}
function head(){
  const c=DATA.counts;
  document.getElementById('hd').innerHTML=
   `<h1>KOF98 SNES — calibration snapshot</h1>`+
   `<p class="meta">captured ${esc(DATA.captured_at)} · scope: ${esc(DATA.scope)}</p>`+
   `<div class="status">${esc(STATUS[DATA.status]||DATA.status)}</div>`+
   `<div class="stats">`+Object.entries(c).map(([k,v])=>`<div><b>${v}</b><span>${esc(k)}</span></div>`).join('')+`</div>`+
   `<p class="disc">${DISC.join(' · ')}</p>`;
}
function evidence(){
  const ev=DATA.evidence||{};
  const keys=Object.keys(ev);
  if(!keys.length)return;
  let h='<h2>Evidence</h2>';
  for(const k of keys){
    const v=ev[k];
    if(typeof v==='string'||typeof v==='number')h+=`<p class="meta"><b>${esc(k)}:</b> ${esc(v)}</p>`;
    else if(Array.isArray(v))h+=`<p class="meta"><b>${esc(k)}:</b></p><ul>`+v.map(x=>`<li>${esc(typeof x==='object'?JSON.stringify(x):x)}</li>`).join('')+'</ul>';
    else h+=`<p class="meta"><b>${esc(k)}:</b> <span class="num">${esc(JSON.stringify(v))}</span></p>`;
  }
  document.getElementById('ev').innerHTML=h;
}
function limits(){
  if(!DATA.limits.length)return;
  document.getElementById('lm').innerHTML='<h2>Limits</h2><ul>'+DATA.limits.map(l=>`<li>${esc(l)}</li>`).join('')+'</ul>';
}
head();overview();filters();moves();frames();evidence();limits();
"""


def render_html(data, path):
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    doc = (
        "<!doctype html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>KOF98 SNES calibration snapshot</title>"
        f"<style>{CSS}</style></head><body>"
        "<div id=\"hd\"></div><h2>Characters</h2><div id=\"ov\"></div>"
        "<h2>Moves</h2><div id=\"flt\"></div><div id=\"mv\"></div>"
        "<div id=\"fr\"></div><div id=\"ev\"></div><div id=\"lm\"></div>"
        f"<script>const DATA={payload};"
        f"const STATUS={json.dumps(STATUS_LABELS)};"
        f"const DISC={json.dumps(DISCLAIMERS)};"
        f"{JS}</script></body></html>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    return path


TSX_TEMPLATE = """import { useMemo, useState, Grid, H1, H2, Pill, Row, Select, Stat,
    Table, Text, TextInput, useHostTheme } from "cursor/canvas";

const DATA = %s;

type Row_ = {c:number;sid:number|null;state:number|null;action:number|null;
cat:string;wired:number;cmds:string;se:number|null;si:number|null;
st:number|null;ge:number|null;gt:number[]|null;dmg:number|null;
proj:string|null;sf:number[][];gf:number[][]};

const fmt = (v: number | string | null | undefined) => v == null ? "—" : v;

export default function CalibrationSnapshot() {
  const t = useHostTheme();
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("");
  const [charIdx, setCharIdx] = useState(-1);
  const [sel, setSel] = useState(-1);
  const chars = DATA.chars;
  const rows = DATA.rows as Row_[];
  const cats = useMemo(() => [...new Set(rows.map(r => r.cat))], [rows]);
  const lq = q.toLowerCase();
  const vis = rows.map((r, i) => [r, i] as const).filter(([r]) =>
    (charIdx < 0 || r.c === charIdx) && (!cat || r.cat === cat) &&
    (!lq || String(r.sid).includes(lq) || String(r.state).includes(lq) ||
     String(r.action).includes(lq) || (r.cmds || "").toLowerCase().includes(lq) ||
     chars[r.c].display.toLowerCase().includes(lq)));
  const selRow = sel >= 0 ? rows[sel] : null;
  const mono = {fontFamily: "ui-monospace, Consolas, monospace",
                fontVariantNumeric: "tabular-nums"} as const;

  return (
    <div style={{padding: 16}}>
      <H1>KOF98 SNES — calibration snapshot</H1>
      <Text color="secondary">captured {DATA.captured_at} · scope: {DATA.scope}</Text>
      <Row gap={8} style={{margin: "8px 0"}}>
        <Pill active>{DATA.status === "needs_repair" ? "Ainda não é release" : DATA.status}</Pill>
      </Row>
      <Grid columns={5} gap={8}>
        {Object.entries(DATA.counts).map(([k, v]) =>
          <Stat key={k} value={String(v)} label={k}
                tone={k === "static_errors" && v ? "danger" : undefined} />)}
      </Grid>
      <Text color="secondary" style={{fontStyle: "italic", fontSize: 12}}>
        native slots ≠ distinct Arcade moves · source elements ≠ unique images ≠
        actual VBlanks · cold upload bounds are hypothetical
      </Text>

      <H2>Characters</H2>
      <Table striped stickyHeader
        headers={["Char","Storage","Profile","Normal","Special","Super",
                  "Errors","Warn","Diagnostics"]}
        columnAlign={["left","left","left","right","right","right","right","right","left"]}
        rows={chars.map(c => [
          c.display, c.storage, c.profile,
          <span style={mono}>{c.normal}</span>,
          <span style={mono}>{c.special}</span>,
          <span style={mono}>{c.super}</span>,
          <span style={{...mono, color: c.errors ? t.palette?.red : undefined}}>{c.errors}</span>,
          <span style={mono}>{c.warnings}</span>,
          (c.diagnostics || []).map((d, i) => (
            <Text key={i} style={{fontSize: 11}}
              color={d.level === "error" ? "danger" : "secondary"}>
              {d.issue}{d.sid != null ? " sid " + d.sid : ""}
            </Text>)),
        ])} />

      <H2>Moves</H2>
      <Row gap={8} style={{flexWrap: "wrap", marginBottom: 8}}>
        <TextInput value={q} onChange={setQ}
                   placeholder="search move/state/command" />
        <Select value={String(charIdx)}
          onChange={v => setCharIdx(+v)}
          options={[{value: "-1", label: "all characters"},
            ...chars.map((c, i) => ({value: String(i), label: c.display}))]} />
        {cats.map(c =>
          <Pill key={c} active={cat === c} size="sm"
                onClick={() => setCat(cat === c ? "" : c)}>{c}</Pill>)}
      </Row>
      <Text color="secondary" style={{fontSize: 12}}>
        {vis.length} of {rows.length} rows — click a row index below
      </Text>
      <Table striped stickyHeader
        headers={["Char","SID","State","Action","Category","Wired","Cmds",
                  "SrcEl","SrcImg","SrcTick","GenEl","GenTicks","Dmg","Proj"]}
        columnAlign={["left","right","right","right","left","left","left",
                      "right","right","right","right","left","right","left"]}
        rows={vis.map(([r, i]) => [
          chars[r.c].display,
          <span style={mono} onClick={() => setSel(i)}>{fmt(r.sid)}</span>,
          <span style={mono}>{fmt(r.state)}</span>,
          <span style={mono}>{fmt(r.action)}</span>,
          r.cat,
          r.wired ? "yes" : "no",
          r.cmds,
          <span style={mono}>{fmt(r.se)}</span>,
          <span style={mono}>{fmt(r.si)}</span>,
          <span style={mono}>{fmt(r.st)}</span>,
          <span style={mono}>{fmt(r.ge)}</span>,
          <span style={mono}>{fmt((r.gt || []).join(","))}</span>,
          <span style={mono}>{fmt(r.dmg)}</span>,
          fmt(r.proj),
        ])}
        rowTone={vis.map(([, i]) => i === sel ? "info" : undefined)} />

      {selRow && (
        <>
          <H2>Frames — {chars[selRow.c].display} sid {fmt(selRow.sid)} /
            state {fmt(selRow.state)} / action {fmt(selRow.action)}</H2>
          <Table striped
            headers={["#","Src grp,num","Src ticks","Gen sprite","Gen ticks",
                      "Upload B","VBlank LB*"]}
            columnAlign={["right","left","right","right","right","right","right"]}
            rows={Array.from(
              {length: Math.max(selRow.sf.length, selRow.gf.length)},
              (_, i) => {
                const s = selRow.sf[i] || [], g = selRow.gf[i] || [];
                return [
                  <span style={mono}>{i}</span>,
                  <span style={mono}>{s.length ? s[0]+","+s[1] : "—"}</span>,
                  <span style={mono}>{fmt(s[2])}</span>,
                  <span style={mono}>{fmt(g[0])}</span>,
                  <span style={mono}>{fmt(g[1])}</span>,
                  <span style={mono}>{fmt(g[2])}</span>,
                  <span style={mono}>{fmt(g[3])}{g[4] ? " !" : ""}</span>,
                ];
              })} />
          <Text color="secondary" style={{fontSize: 11, fontStyle: "italic"}}>
            *cold upload lower bound is hypothetical; ! = upload exceeds frame ticks
          </Text>
        </>
      )}

      {Object.keys(DATA.evidence || {}).length > 0 && (
        <>
          <H2>Evidence</H2>
          {Object.entries(DATA.evidence).map(([k, v]) => (
            <Text key={k} style={{fontSize: 12}}>
              {k}: {typeof v === "object" ? JSON.stringify(v) : String(v)}
            </Text>
          ))}
        </>
      )}
      {DATA.limits.length > 0 && (
        <>
          <H2>Limits</H2>
          {DATA.limits.map((l, i) => <Text key={i} style={{fontSize: 12}}>· {l}</Text>)}
        </>
      )}
    </div>
  );
}
"""


def render_canvas(data, path):
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    with open(path, "w", encoding="utf-8") as f:
        f.write(TSX_TEMPLATE % payload)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--html")
    ap.add_argument("--canvas")
    args = ap.parse_args()
    with open(args.snapshot, encoding="utf-8") as f:
        data = project(json.load(f))
    out = []
    if args.html:
        out.append(render_html(data, args.html))
    if args.canvas:
        out.append(render_canvas(data, args.canvas))
    if not out:
        ap.error("at least one of --html/--canvas is required")
    for p in out:
        print(f"wrote {p} ({os.path.getsize(p)} bytes)")


if __name__ == "__main__":
    main()
