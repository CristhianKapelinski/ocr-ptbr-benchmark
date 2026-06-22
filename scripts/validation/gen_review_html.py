#!/usr/bin/env python3
"""Generate a self-contained HTML page for human validation of the reconstructed
forms gold. Opens in any browser (bypasses the VSCode image preview).

It renders the reproducible random sample of fields drawn by sample_validation_fields.py
(validation_sample.json): for each sampled form the image sits beside only the sampled
fields of that form, and the reviewer marks each field OK or wrong, can type a correction,
and exports the verdicts as JSON. From that export we estimate the field-level accuracy of
the gold with a Wilson confidence interval. Progress autosaves to the browser's localStorage.
"""
import json
import os

HARNESS = os.path.dirname(os.path.abspath(__file__))
SAMPLE_FILE = os.path.join(HARNESS, "validation_sample.json")

with open(SAMPLE_FILE, encoding="utf-8") as fh:
    sample = json.load(fh)

forms = []
for idx_str, fields in sorted(sample["forms"].items(), key=lambda kv: int(kv[0])):
    idx = int(idx_str)
    img = f"gold_rebuilt/images/pt_val_{idx}.jpg"
    if not os.path.exists(os.path.join(HARNESS, img)):
        continue
    forms.append({"idx": idx, "img": img, "fields": fields})

DATA = json.dumps(forms, ensure_ascii=False)
META = json.dumps({"seed": sample["seed"], "n_sampled": sample["n_sampled"],
                   "n_pool": sample["n_pool"], "n_forms": len(forms)}, ensure_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Human validation: reconstructed forms gold</title>
<style>
  :root { --ok:#1a7f37; --bad:#cf222e; --line:#d0d7de; }
  * { box-sizing: border-box; }
  body { font: 15px/1.5 -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; color:#1f2328; }
  header { position: sticky; top: 0; z-index: 20; background:#0d1117; color:#fff;
           padding: 10px 16px; display:flex; gap:16px; align-items:center; flex-wrap:wrap; }
  header b { font-size: 16px; }
  header .stat { font-size: 13px; opacity:.9; }
  button { font: inherit; padding: 6px 12px; border-radius: 6px; border:1px solid #444;
           background:#21262d; color:#fff; cursor:pointer; }
  button.primary { background:#238636; border-color:#238636; }
  .jump { padding:8px 16px; background:#f6f8fa; border-bottom:1px solid var(--line);
          position:sticky; top:46px; z-index:19; font-size:13px; }
  .jump a { margin-right:6px; text-decoration:none; color:#0969da; }
  .jump a.done { color: var(--ok); } .jump a.has-bad { color: var(--bad); font-weight:700; }
  .form { display:grid; grid-template-columns: 1fr 1fr; gap:16px; padding:16px;
          border-bottom:8px solid #eaeef2; scroll-margin-top: 90px; }
  .imgwrap { position: sticky; top: 90px; align-self:start; max-height: calc(100vh - 100px); overflow:auto;
             border:1px solid var(--line); border-radius:8px; background:#fafafa; }
  .imgwrap img { width:100%; display:block; }
  .panel h2 { margin:0 0 4px; font-size:18px; }
  .tag { font-size:11px; padding:2px 7px; border-radius:10px; background:#ddf4ff; color:#0969da; }
  table { width:100%; border-collapse:collapse; }
  td, th { border:1px solid var(--line); padding:6px 8px; vertical-align:top; text-align:left; }
  th { background:#f6f8fa; }
  td.key { width:34%; color:#57606a; font-size:13px; }
  td.val { font-weight:600; }
  .marks { white-space:nowrap; width:1%; }
  .marks label { cursor:pointer; padding:2px 6px; border-radius:5px; border:1px solid var(--line); margin-right:3px; }
  .marks input { display:none; }
  .marks input:checked + span.ok  { background:var(--ok); color:#fff; }
  .marks input:checked + span.bad { background:var(--bad); color:#fff; }
  .marks label:has(input:checked.okR)  { border-color:var(--ok); }
  .marks label:has(input:checked.badR) { border-color:var(--bad); }
  tr.wrong td.val { background:#fff5f5; }
  .fix { width:100%; margin-top:4px; padding:3px 6px; border:1px dashed var(--bad);
         border-radius:4px; display:none; font:inherit; }
  tr.wrong .fix { display:block; }
  textarea.notes { width:100%; min-height:48px; margin-top:8px; padding:6px; }
  .help { padding:10px 16px; background:#fff8c5; font-size:13px; border-bottom:1px solid var(--line); }
</style>
</head>
<body>
<header>
  <b>Human validation (random sample): reconstructed forms gold</b>
  <span class="stat" id="stat"></span>
  <span style="flex:1"></span>
  <button class="primary" onclick="exportJSON()">Export validation JSON</button>
  <button onclick="if(confirm('Clear all marks?')){localStorage.removeItem(KEY);location.reload();}">Clear</button>
</header>
<div class="help">
  This is a <b>reproducible random sample</b> of <b id="hN"></b> reconstructed-gold fields (seed <b id="hSeed"></b>),
  drawn from <b id="hPool"></b> scored fields across the forms and grouped here by form.
  For each field, click <b>OK</b> if the reconstructed value matches the image, or <b>Wrong</b> and
  type the correct value. Marks autosave in this browser. When done, click
  <b>Export validation JSON</b> and send me the file; I compute the gold accuracy (with a confidence interval) and fold it into the paper.
</div>
<div class="jump" id="jump"></div>
<main id="main"></main>
<script>
const FORMS = %%DATA%%;
const META = %%META%%;
const KEY = "ocr_gold_validation_v2_seed" + META.seed;
let state = JSON.parse(localStorage.getItem(KEY) || "{}");
function fid(f,i){ return f.idx + ":" + f.fields[i].pos; }
function mark(f,i,v,el){
  const id = fid(f,i); state[id] = state[id]||{};
  state[id].verdict = v;
  const tr = el.closest("tr"); tr.classList.toggle("wrong", v==="wrong");
  localStorage.setItem(KEY, JSON.stringify(state)); renderStat();
}
function fixVal(f,i,v){ const id=fid(f,i); state[id]=state[id]||{}; state[id].fix=v;
  localStorage.setItem(KEY, JSON.stringify(state)); }
function note(f,v){ state["note:"+f.idx]=v; localStorage.setItem(KEY, JSON.stringify(state)); }
function renderStat(){
  let total=0, marked=0, bad=0;
  FORMS.forEach(f=>f.fields.forEach((_,i)=>{ total++; const s=state[fid(f,i)];
    if(s&&s.verdict){marked++; if(s.verdict==="wrong")bad++;} }));
  document.getElementById("stat").textContent =
    `${marked}/${total} fields marked - ${bad} wrong - ${FORMS.length} forms`;
  document.querySelectorAll(".jump a").forEach(a=>{
    const idx=+a.dataset.idx, f=FORMS.find(x=>x.idx===idx);
    let m=0,b=0; f.fields.forEach((_,i)=>{const s=state[fid(f,i)]; if(s&&s.verdict){m++; if(s.verdict==="wrong")b++;}});
    a.classList.toggle("done", m===f.fields.length && f.fields.length>0);
    a.classList.toggle("has-bad", b>0);
  });
}
function exportJSON(){
  const out={meta:{tool:"gen_review_html", seed:META.seed, n_sampled:META.n_sampled,
                   n_pool:META.n_pool, forms:FORMS.length}, forms:[]};
  FORMS.forEach(f=>{
    const fr={idx:f.idx, note:state["note:"+f.idx]||"", fields:[]};
    f.fields.forEach((fld,i)=>{ const s=state[fid(f,i)]||{};
      fr.fields.push({pos:fld.pos, key:fld.key, gold:fld.value, verdict:s.verdict||"unreviewed",
                      correction:s.fix||""}); });
    out.forms.push(fr);
  });
  const blob=new Blob([JSON.stringify(out,null,2)],{type:"application/json"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob);
  a.download="forms_human_validation.json"; a.click();
}
document.getElementById("hN").textContent = META.n_sampled;
document.getElementById("hSeed").textContent = META.seed;
document.getElementById("hPool").textContent = META.n_pool;
// build jump bar
document.getElementById("jump").innerHTML = "Jump: " + FORMS.map(f=>
  `<a href="#f${f.idx}" data-idx="${f.idx}">${f.idx}</a>`).join("");
// build forms
const main=document.getElementById("main");
FORMS.forEach(f=>{
  const sec=document.createElement("section"); sec.className="form"; sec.id="f"+f.idx;
  let rows = f.fields.map((fld,i)=>{
    const s=state[fid(f,i)]||{};
    return `<tr class="${s.verdict==='wrong'?'wrong':''}">
      <td class="key">${escape_(fld.key)}</td>
      <td class="val">${escape_(fld.value)}
        <input class="fix" placeholder="correct value" value="${escape_(s.fix||'')}"
               oninput="fixVal(FORMS[${FORMS.indexOf(f)}],${i},this.value)"></td>
      <td class="marks">
        <label><input type="radio" class="okR" name="m${f.idx}_${i}" ${s.verdict==='ok'?'checked':''}
          onclick="mark(FORMS[${FORMS.indexOf(f)}],${i},'ok',this)"><span class="ok">OK</span></label>
        <label><input type="radio" class="badR" name="m${f.idx}_${i}" ${s.verdict==='wrong'?'checked':''}
          onclick="mark(FORMS[${FORMS.indexOf(f)}],${i},'wrong',this)"><span class="bad">Wrong</span></label>
      </td></tr>`;
  }).join("");
  sec.innerHTML = `
    <div class="imgwrap"><img loading="lazy" src="${f.img}" alt="pt_val_${f.idx}"></div>
    <div class="panel">
      <h2>pt_val_${f.idx} <span class="tag">${f.fields.length} sampled field${f.fields.length>1?'s':''}</span></h2>
      <table><thead><tr><th>Field</th><th>Reconstructed value</th><th class="marks">Verdict</th></tr></thead>
      <tbody>${rows}</tbody></table>
      <textarea class="notes" placeholder="notes for this form" oninput="note(FORMS[${FORMS.indexOf(f)}],this.value)">${escape_(state['note:'+f.idx]||'')}</textarea>
    </div>`;
  main.appendChild(sec);
});
function escape_(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
renderStat();
</script>
</body>
</html>
"""

out = os.path.join(HARNESS, "review.html")
with open(out, "w", encoding="utf-8") as fh:
    fh.write(HTML.replace("%%DATA%%", DATA).replace("%%META%%", META))
n_fields = sum(len(f["fields"]) for f in forms)
print(f"wrote {out}: {n_fields} sampled fields across {len(forms)} forms (seed {sample['seed']})")
