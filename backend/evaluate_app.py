from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import httpx
import pdfplumber
from rouge_score import rouge_scorer
from bert_score import score as bert_score
import io
import uvicorn
import json


# ─────────────────────────────────────────────────────────
#  ⚙️  CONFIGURATION
# ─────────────────────────────────────────────────────────
SUMMARIZATION_API_URL = "http://127.0.0.1:8000/api/upload"
PDF_FIELD_NAME        = "file"        # champ form-data de votre API
SUMMARY_RESPONSE_KEY  = "summary"     # clé dans la réponse JSON
EVAL_PORT             = 8001
# ─────────────────────────────────────────────────────────

app = FastAPI(title="Evaluation — Qualité des Résumés")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────
#  HTML FRONTEND
# ──────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Évaluation Résumés</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

:root{
  --navy:   #1a2540;
  --navy2:  #243050;
  --orange: #e8560a;
  --orange2:#f07030;
  --bg:     #f4f6fa;
  --white:  #ffffff;
  --border: #e2e6ef;
  --muted:  #6b7a99;
  --text:   #1a2540;
  --radius: 14px;
}

body{
  background:var(--bg);
  color:var(--text);
  font-family:'Plus Jakarta Sans',sans-serif;
  min-height:100vh;
}

/* ── NAV ── */
nav{
  background:var(--white);
  border-bottom:1px solid var(--border);
  padding:0 40px;
  height:64px;
  display:flex;
  align-items:center;
  justify-content:space-between;
}
.nav-brand{
  display:flex;align-items:center;gap:10px;
  font-weight:800;font-size:18px;color:var(--navy);
  letter-spacing:-.4px;
}
.nav-dot{
  width:10px;height:10px;border-radius:50%;
  background:var(--orange);
}
.nav-tag{
  font-size:12px;font-weight:500;color:var(--muted);
  background:var(--bg);border:1px solid var(--border);
  padding:4px 12px;border-radius:20px;
  font-family:'JetBrains Mono',monospace;
}

/* ── LAYOUT ── */
.page{
  max-width:860px;
  margin:0 auto;
  padding:48px 24px 80px;
}

/* ── HERO ── */
.hero{margin-bottom:40px;}
.hero h1{
  font-size:clamp(28px,4vw,42px);
  font-weight:800;
  line-height:1.1;
  letter-spacing:-.8px;
  margin-bottom:10px;
}
.hero h1 span{color:var(--orange);}
.hero p{
  font-size:15px;color:var(--muted);
  font-family:'JetBrains Mono',monospace;
  font-weight:400;
}

/* ── CARD ── */
.card{
  background:var(--white);
  border:1px solid var(--border);
  border-radius:var(--radius);
  padding:28px 32px;
  margin-bottom:20px;
  box-shadow:0 1px 4px rgba(26,37,64,.05);
}

/* ── UPLOAD ── */
.drop-zone{
  border:2px dashed var(--border);
  border-radius:10px;
  padding:40px 20px;
  text-align:center;
  cursor:pointer;
  position:relative;
  transition:all .2s;
  background:var(--bg);
}
.drop-zone:hover,.drop-zone.over{
  border-color:var(--orange);
  background:#fff8f5;
}
.drop-zone input{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%;}
.drop-icon{font-size:32px;display:block;margin-bottom:10px;}
.drop-zone p{font-size:14px;color:var(--muted);}
.drop-zone strong{color:var(--orange);}
.file-chosen{
  margin-top:10px;font-size:13px;font-weight:600;
  color:var(--navy);font-family:'JetBrains Mono',monospace;
}

/* ── INPUT ROW ── */
.input-row{
  display:flex;gap:10px;margin-top:16px;
}
.input-row input{
  flex:1;
  border:1px solid var(--border);
  border-radius:8px;
  padding:11px 16px;
  font-size:13px;
  font-family:'JetBrains Mono',monospace;
  color:var(--navy);
  background:var(--bg);
  outline:none;
  transition:border-color .2s;
}
.input-row input:focus{border-color:var(--orange);}
.input-row input::placeholder{color:var(--muted);}

/* ── BUTTON ── */
.btn{
  background:var(--navy);
  color:#fff;
  font-family:'Plus Jakarta Sans',sans-serif;
  font-weight:700;font-size:14px;
  padding:11px 24px;
  border:none;border-radius:8px;
  cursor:pointer;
  transition:background .2s,transform .1s;
  white-space:nowrap;
}
.btn:hover{background:var(--orange);}
.btn:active{transform:scale(.98);}
.btn:disabled{opacity:.4;cursor:not-allowed;transform:none;}

/* ── LOADER ── */
#loader{
  display:none;
  align-items:center;gap:14px;
  padding:20px 28px;
}
.spin{
  width:20px;height:20px;
  border:2px solid var(--border);
  border-top-color:var(--orange);
  border-radius:50%;
  animation:spin .7s linear infinite;
  flex-shrink:0;
}
@keyframes spin{to{transform:rotate(360deg)}}
#loader p{font-size:14px;color:var(--muted);}
#loader strong{color:var(--navy);}

/* ── ERROR ── */
#err{
  display:none;
  background:#fff5f5;border:1px solid #fcc;border-radius:10px;
  padding:14px 18px;margin-bottom:16px;
  font-size:13px;font-family:'JetBrains Mono',monospace;color:#c0392b;
}

/* ── SECTION LABEL ── */
.slabel{
  font-size:11px;font-weight:700;letter-spacing:2px;
  text-transform:uppercase;color:var(--muted);
  margin-bottom:14px;
  font-family:'JetBrains Mono',monospace;
}

/* ── STAT CARDS ── */
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px;}
.stat{
  background:var(--white);border:1px solid var(--border);
  border-radius:10px;padding:18px 20px;
  box-shadow:0 1px 3px rgba(26,37,64,.04);
}
.stat .s-lbl{font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;}
.stat .s-val{font-size:28px;font-weight:800;color:var(--navy);}
.stat .s-unit{font-size:11px;color:var(--muted);font-family:'JetBrains Mono',monospace;margin-top:2px;}

/* ── METRIC GROUP ── */
.mgroup{
  background:var(--white);border:1px solid var(--border);
  border-radius:var(--radius);padding:24px 28px;
  margin-bottom:16px;
  box-shadow:0 1px 4px rgba(26,37,64,.05);
}
.mgroup-head{
  display:flex;align-items:center;gap:10px;margin-bottom:4px;
}
.mgroup-title{font-size:16px;font-weight:800;color:var(--navy);}
.mgroup-desc{font-size:12px;color:var(--muted);font-family:'JetBrains Mono',monospace;margin-bottom:20px;}
.mbars{display:flex;flex-direction:column;gap:12px;}
.mrow{display:flex;align-items:center;gap:12px;}
.mname{
  font-size:11px;font-weight:700;letter-spacing:1px;
  text-transform:uppercase;color:var(--muted);
  font-family:'JetBrains Mono',monospace;
  width:72px;flex-shrink:0;
}
.bwrap{flex:1;height:7px;background:var(--border);border-radius:4px;overflow:hidden;}
.bfill{height:100%;border-radius:4px;transition:width .9s cubic-bezier(.4,0,.2,1);width:0;}
.fill-r{background:linear-gradient(90deg,var(--orange),var(--orange2));}
.fill-b{background:linear-gradient(90deg,var(--navy),#3a5090);}
.mval{
  font-family:'JetBrains Mono',monospace;
  font-size:13px;font-weight:500;color:var(--navy);
  width:46px;text-align:right;flex-shrink:0;
}
/* sub-scores */
.subs{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:16px;}
.sub{
  background:var(--bg);border:1px solid var(--border);
  border-radius:8px;padding:12px;text-align:center;
}
.sub .sl{font-size:10px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;}
.sub .sv{font-size:19px;font-weight:800;}
.c-orange{color:var(--orange);}
.c-navy{color:var(--navy);}

/* tag */
.tag{
  display:inline-block;
  font-size:11px;font-weight:700;font-family:'JetBrains Mono',monospace;
  padding:2px 10px;border-radius:20px;
}
.tag-good{background:#e8f8ef;color:#1a7a4a;}
.tag-avg {background:#fff3e0;color:#c45b00;}
.tag-bad {background:#fde8e8;color:#c0392b;}

/* summary box */
.sumbox{
  background:var(--white);border:1px solid var(--border);
  border-left:4px solid var(--orange);
  border-radius:var(--radius);padding:22px 26px;
  margin-top:0;
  box-shadow:0 1px 4px rgba(26,37,64,.05);
}
.sumbox .st{
  font-size:11px;font-weight:700;letter-spacing:2px;
  text-transform:uppercase;color:var(--orange);
  font-family:'JetBrains Mono',monospace;margin-bottom:12px;
}
.sumbox p{font-size:14px;line-height:1.75;color:#4a5568;}

#results{display:none;}

@media(max-width:600px){
  .stats{grid-template-columns:1fr 1fr;}
  .input-row{flex-direction:column;}
  nav{padding:0 20px;}
}
</style>
</head>
<body>

<nav>
  <div class="nav-brand">
    <div class="nav-dot"></div>
    Data Intelligence
  </div>
  <div class="nav-tag">évaluation · résumés</div>
</nav>

<div class="page">

  <!-- HERO -->
  <div class="hero">
    <h1>Évaluez la qualité<br/>de vos <span>résumés</span></h1>
    <p>// ROUGE · BERTScore · Compression — sans résumé de référence</p>
  </div>

  <!-- UPLOAD CARD -->
  <div class="card">
    <div class="slabel">Document PDF</div>
    <div class="drop-zone" id="dz">
      <input type="file" id="pdfInput" accept=".pdf"/>
      <span class="drop-icon">📄</span>
      <p>Glissez votre PDF ici ou <strong>cliquez pour sélectionner</strong></p>
      <div class="file-chosen" id="fname"></div>
    </div>

    <div class="input-row">
      <input type="text" id="apiUrl"
        value="http://localhost:8001/evaluate"
        placeholder="URL de l'API d'évaluation"/>
      <button class="btn" id="evalBtn" onclick="run()" disabled>▶ Évaluer</button>
    </div>
  </div>

  <!-- LOADER -->
  <div class="card" id="loader">
    <div class="spin"></div>
    <p>Analyse en cours… <strong>résumé + calcul des métriques</strong></p>
  </div>

  <!-- ERROR -->
  <div id="err"></div>

  <!-- RESULTS -->
  <div id="results">

    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 20px;" data-html2pdf-ignore>
      <div class="slabel" style="margin-bottom:0;">Statistiques générales</div>
      <button class="btn" style="padding: 8px 16px; font-size: 12px; background: var(--orange);" onclick="downloadPDF()">⬇ Télécharger PDF</button>
    </div>
    <div class="stats">
      <div class="stat">
        <div class="s-lbl">Mots document</div>
        <div class="s-val" id="docLen">—</div>
        <div class="s-unit">mots</div>
      </div>
      <div class="stat">
        <div class="s-lbl">Mots résumé</div>
        <div class="s-val" id="sumLen">—</div>
        <div class="s-unit">mots</div>
      </div>
      <div class="stat">
        <div class="s-lbl">Compression</div>
        <div class="s-val" id="comp">—</div>
        <div class="s-unit">% du texte original</div>
      </div>
    </div>

    <!-- ROUGE -->
    <div class="slabel">Scores ROUGE</div>
    <div class="mgroup">
      <div class="mgroup-head">
        <span class="mgroup-title">ROUGE</span>
        <span id="rTag"></span>
      </div>
      <div class="mgroup-desc">// Recouvrement lexical entre le résumé et le document source</div>
      <div class="mbars">
        <div class="mrow"><span class="mname">ROUGE-1</span><div class="bwrap"><div class="bfill fill-r" id="br1"></div></div><span class="mval" id="vr1">—</span></div>
        <div class="mrow"><span class="mname">ROUGE-2</span><div class="bwrap"><div class="bfill fill-r" id="br2"></div></div><span class="mval" id="vr2">—</span></div>
        <div class="mrow"><span class="mname">ROUGE-L</span><div class="bwrap"><div class="bfill fill-r" id="brL"></div></div><span class="mval" id="vrL">—</span></div>
      </div>
      <div class="subs">
        <div class="sub"><div class="sl">Précision R1</div><div class="sv c-orange" id="r1p">—</div></div>
        <div class="sub"><div class="sl">Rappel R1</div>   <div class="sv c-orange" id="r1r">—</div></div>
        <div class="sub"><div class="sl">F1 R1</div>       <div class="sv c-orange" id="r1f">—</div></div>
      </div>
    </div>

    <!-- BERT -->
    <div class="slabel">BERTScore</div>
    <div class="mgroup">
      <div class="mgroup-head">
        <span class="mgroup-title">BERTScore</span>
        <span id="bTag"></span>
      </div>
      <div class="mgroup-desc">// Similarité sémantique via embeddings BERT (modèle français)</div>
      <div class="mbars">
        <div class="mrow"><span class="mname">Précision</span><div class="bwrap"><div class="bfill fill-b" id="bbp"></div></div><span class="mval" id="vbp">—</span></div>
        <div class="mrow"><span class="mname">Rappel</span>   <div class="bwrap"><div class="bfill fill-b" id="bbr"></div></div><span class="mval" id="vbr">—</span></div>
        <div class="mrow"><span class="mname">F1</span>       <div class="bwrap"><div class="bfill fill-b" id="bbf"></div></div><span class="mval" id="vbf">—</span></div>
      </div>
    </div>

    <!-- RÉSUMÉ -->
    <div class="slabel">Résumé généré par le LLM</div>
    <div class="sumbox">
      <div class="st">↳ Sortie du modèle</div>
      <p id="sumText">—</p>
    </div>

  </div><!-- /results -->
</div>

<script>
const dz=document.getElementById('dz');
const inp=document.getElementById('pdfInput');
const btn=document.getElementById('evalBtn');
const fname=document.getElementById('fname');

inp.addEventListener('change',()=>{
  if(inp.files[0]){fname.textContent='✓  '+inp.files[0].name;btn.disabled=false;}
});
dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('over');});
dz.addEventListener('dragleave',()=>dz.classList.remove('over'));
dz.addEventListener('drop',e=>{
  e.preventDefault();dz.classList.remove('over');
  const f=e.dataTransfer.files[0];
  if(f&&f.type==='application/pdf'){
    const dt=new DataTransfer();dt.items.add(f);inp.files=dt.files;
    fname.textContent='✓  '+f.name;btn.disabled=false;
  }
});

const bar=(id,v)=>setTimeout(()=>{document.getElementById(id).style.width=(v*100).toFixed(1)+'%';},120);
const pct=v=>(v*100).toFixed(1)+'%';
const tag=f1=>{
  if(f1>=.5)return '<span class="tag tag-good">Très bon</span>';
  if(f1>=.3)return '<span class="tag tag-avg">Acceptable</span>';
  return '<span class="tag tag-bad">À améliorer</span>';
};
const set=(id,v)=>{document.getElementById(id).textContent=v;};

async function run(){
  const file=inp.files[0];
  const url=document.getElementById('apiUrl').value.trim();
  if(!file||!url)return;

  document.getElementById('err').style.display='none';
  document.getElementById('results').style.display='none';
  document.getElementById('loader').style.display='flex';
  btn.disabled=true;

  const fd=new FormData();
  fd.append('file',file);

  try{
    const res=await fetch(url,{method:'POST',body:fd});
    if(!res.ok){const e=await res.json().catch(()=>({}));throw new Error(e.detail||'HTTP '+res.status);}
    const d=await res.json();

    set('docLen',d.document_length.toLocaleString('fr'));
    set('sumLen',d.summary_length.toLocaleString('fr'));
    set('comp',d.compression_ratio+'%');

    bar('br1',d.rouge.rouge1.f1);bar('br2',d.rouge.rouge2.f1);bar('brL',d.rouge.rougeL.f1);
    set('vr1',pct(d.rouge.rouge1.f1));set('vr2',pct(d.rouge.rouge2.f1));set('vrL',pct(d.rouge.rougeL.f1));
    set('r1p',pct(d.rouge.rouge1.precision));set('r1r',pct(d.rouge.rouge1.recall));set('r1f',pct(d.rouge.rouge1.f1));
    document.getElementById('rTag').innerHTML=tag(d.rouge.rouge1.f1);

    bar('bbp',d.bert_score.precision);bar('bbr',d.bert_score.recall);bar('bbf',d.bert_score.f1);
    set('vbp',pct(d.bert_score.precision));set('vbr',pct(d.bert_score.recall));set('vbf',pct(d.bert_score.f1));
    document.getElementById('bTag').innerHTML=tag(d.bert_score.f1);

    document.getElementById('sumText').innerHTML = d.summary
    .replace(/### (.+)/g, '<strong>$1</strong>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>');

    document.getElementById('loader').style.display='none';
    document.getElementById('results').style.display='block';
  }catch(e){
    document.getElementById('loader').style.display='none';
    const eb=document.getElementById('err');
    eb.textContent='⚠  '+e.message;eb.style.display='block';
  }finally{btn.disabled=false;}
}

function downloadPDF() {
  const element = document.getElementById('results');
  const opt = {
    margin:       10,
    filename:     'evaluation_resume.pdf',
    image:        { type: 'jpeg', quality: 0.98 },
    html2canvas:  { scale: 2, useCORS: true },
    jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
  };
  html2pdf().set(opt).from(element).save();
}
</script>
</body>
</html>"""


# ──────────────────────────────────────────────────────────
#  ROUTES
# ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML


def extract_text(pdf_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return " ".join(p.extract_text() or "" for p in pdf.pages).strip()


def compute_rouge(ref: str, hyp: str) -> dict:
    sc = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    s  = sc.score(ref, hyp)
    return {
        k: {"precision": round(s[k].precision, 4),
            "recall":    round(s[k].recall,    4),
            "f1":        round(s[k].fmeasure,  4)}
        for k in ["rouge1", "rouge2", "rougeL"]
    }


def compute_bert(ref: str, hyp: str) -> dict:
    P, R, F1 = bert_score([hyp], [ref], lang="fr", verbose=False)
    return {
        "precision": round(P.mean().item(), 4),
        "recall":    round(R.mean().item(), 4),
        "f1":        round(F1.mean().item(), 4),
    }


@app.post("/evaluate")
async def evaluate(file: UploadFile = File(...)):
    pdf_bytes = await file.read()

    # 1. Extraire le texte (référence non supervisée)
    doc_text = extract_text(pdf_bytes)
    if not doc_text:
        raise HTTPException(400, "Impossible d'extraire le texte du PDF.")

    # 2. Appeler l'API de résumé
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                SUMMARIZATION_API_URL,
                files={PDF_FIELD_NAME: (file.filename, pdf_bytes, "application/pdf")},
            )
        r.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(504, "L'API de résumé n'a pas répondu (timeout).")
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"Erreur API résumé : {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(503, f"Impossible de contacter l'API : {e}")

    summary = None
    try:
        lines = r.text.strip().split("\n")
        for line in lines:
            if not line.strip():
                continue
            line_data = json.loads(line)
            if line_data.get("status") == "error":
                raise HTTPException(502, f"Erreur API résumé : {line_data.get('message')} (Détails: {line_data.get('technical')})")
            if line_data.get("status") == "completed":
                payload = line_data.get("data", {})
                if SUMMARY_RESPONSE_KEY in payload:
                    summary = payload[SUMMARY_RESPONSE_KEY]
                    break
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Erreur lors du décodage de la réponse de l'API : {e}")

    if not summary:
        raise HTTPException(502, f"Clé '{SUMMARY_RESPONSE_KEY}' absente de la réponse finale de l'API de résumé.")

    # 3. Métriques
    rouge  = compute_rouge(doc_text, summary)
    bert   = compute_bert(doc_text, summary)
    n_doc  = len(doc_text.split())
    n_sum  = len(summary.split())

    return {
        "filename":          file.filename,
        "document_length":   n_doc,
        "summary_length":    n_sum,
        "compression_ratio": round(n_sum / n_doc * 100, 2) if n_doc else 0,
        "summary":           summary,
        "rouge":             rouge,
        "bert_score":        bert,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("evaluate_app:app", host="0.0.0.0", port=EVAL_PORT, reload=True)
