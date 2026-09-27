const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
p.author = "AegisSOC AI";

// ---- palette ----
const BG="0B0F17", PANEL="141C29", PANEL2="0F1622", INK="EAF0F7", MUT="9AA7B5",
      FAINT="5C6B7A", CY="22D3EE", BL="3B82F6", P1="FF4D5E", P2="F59E0B",
      P3="60A5FA", P4="6B7A8D", GRN="22C55E";
const TITLE="Calibri", BODY="Calibri", MONO="Courier New";
const W=13.3, H=7.5;

function bg(s, c){ s.background = { color: c || BG }; }
function title(s, t, sub){
  s.addText(t, {isTextBox:true, x:0.6, y:0.42, w:12.1, h:0.7, fontFace:TITLE, bold:true,
    fontSize:32, color:INK, margin:0, align:"left"});
  if(sub) s.addText(sub, {isTextBox:true, x:0.62, y:1.06, w:12.1, h:0.4, fontFace:BODY,
    fontSize:14, color:CY, margin:0});
}
function kicker(s, t){
  s.addText(t, {isTextBox:true, x:0.62, y:0.2, w:8, h:0.3, fontFace:BODY, bold:true,
    fontSize:11, color:CY, charSpacing:2, margin:0});
}
function card(s, x, y, w, h, fill){ s.addShape(p.ShapeType.roundRect, {x,y,w,h,
  rectRadius:0.09, fill:{color:fill||PANEL}, line:{type:"none"}}); }

// ============ SLIDE 1 — TITLE ============
let s = p.addSlide(); bg(s);
// shield mark (simple)
s.addShape(p.ShapeType.pentagon, {x:0.62, y:0.55, w:0.62, h:0.62, rotate:90,
  fill:{color:PANEL}, line:{color:CY, width:1.5}});
s.addText("⬡", {isTextBox:true, x:0.62, y:0.55, w:0.62, h:0.62, align:"center", valign:"middle",
  fontSize:24, color:CY, margin:0});
s.addText([
  {text:"Aegis", options:{color:INK}},
  {text:"SOC", options:{color:CY}},
  {text:" AI", options:{color:INK}},
], {isTextBox:true, x:1.35, y:0.6, w:8, h:0.55, fontFace:TITLE, bold:true, fontSize:26, margin:0, valign:"middle"});

s.addText("Explainable, Risk-Based\nSOC Incident Triage", {isTextBox:true, x:0.6, y:2.5, w:9.3, h:1.9,
  fontFace:TITLE, bold:true, fontSize:48, color:INK, margin:0, lineSpacingMultiple:0.95});
s.addText("Cut through alert fatigue — correlate alerts, rank by real-world impact, and explain every decision in plain English. Benchmarked against real Microsoft SOC analysts.",
  {isTextBox:true, x:0.62, y:4.5, w:8.6, h:1.1, fontFace:BODY, fontSize:16, color:MUT, margin:0});
s.addText("Problem E1  ·  CyberKawach — BSides Ahmedabad", {isTextBox:true, x:0.62, y:6.6, w:9, h:0.4,
  fontFace:MONO, fontSize:12, color:CY, margin:0});
// right accent stat strip
[["131,954","alerts ingested"],["9,980","incidents"],["0.896","NDCG vs analysts"]].forEach((d,i)=>{
  card(s, 10.05, 2.5+i*1.15, 2.65, 0.95, PANEL);
  s.addText(d[0], {isTextBox:true, x:10.2, y:2.6+i*1.15, w:2.4, h:0.55, fontFace:MONO, bold:true, fontSize:24, color:CY, margin:0});
  s.addText(d[1], {isTextBox:true, x:10.2, y:3.12+i*1.15, w:2.4, h:0.3, fontFace:BODY, fontSize:11, color:MUT, margin:0});
});
s.addNotes("AegisSOC AI — explainable risk-based SOC triage for problem E1. Headline: 13x alert reduction, NDCG 0.896 vs real analysts, fully explainable, zero LLM in the scoring path.");

// ============ SLIDE 2 — PROBLEM ============
s = p.addSlide(); bg(s); kicker(s,"THE PROBLEM"); title(s,"Analysts drown in alerts");
const probs=[["1000s","of alerts per day from EDR, network, identity, DNS, DLP"],
  ["~5 min","spent per alert — most are noise or false priorities"],
  ["The one","that matters is buried under the ones that don't"]];
probs.forEach((d,i)=>{ card(s,0.62+i*4.0,1.9,3.75,2.1,PANEL);
  s.addText(d[0],{isTextBox:true,x:0.85+i*4.0,y:2.15,w:3.3,h:0.8,fontFace:MONO,bold:true,fontSize:34,color:CY,margin:0});
  s.addText(d[1],{isTextBox:true,x:0.85+i*4.0,y:3.0,w:3.3,h:0.9,fontFace:BODY,fontSize:14,color:MUT,margin:0}); });
card(s,0.62,4.4,12.08,1.7,PANEL2);
s.addText("E1 asks for risk-based triage with explainable reasoning.",{isTextBox:true,x:0.9,y:4.65,w:11.5,h:0.5,fontFace:TITLE,bold:true,fontSize:22,color:INK,margin:0});
s.addText("Correlate related alerts · assess risk & impact · prioritise the critical incidents · with clear, explainable reasoning.",{isTextBox:true,x:0.9,y:5.25,w:11.5,h:0.7,fontFace:BODY,fontSize:15,color:CY,margin:0});

// ============ SLIDE 3 — PIPELINE / WORKFLOW ============
s = p.addSlide(); bg(s); kicker(s,"HOW IT WORKS"); title(s,"The pipeline — five deterministic stages");
const steps=[["1","INGEST","Multi-source alert stream (EDR, NDR, IDS, identity, DNS, DLP)"],
  ["2","CORRELATE","Union-find on shared entities + time window → incidents"],
  ["3","RISK-SCORE","6 impact factors → 0–100 → priority band P1–P4"],
  ["4","EXPLAIN","Every rank carries its plain-English 'why'"],
  ["5","COMPLY","DPDP / CERT-In / GDPR obligations + statutory clocks"]];
const sw=2.32, sx=0.62, sy=2.1;
steps.forEach((d,i)=>{ const x=sx+i*(sw+0.13);
  card(s,x,sy,sw,3.0,PANEL);
  s.addShape(p.ShapeType.ellipse,{x:x+0.2,y:sy+0.25,w:0.55,h:0.55,fill:{color:PANEL2},line:{color:CY,width:1.25}});
  s.addText(d[0],{isTextBox:true,x:x+0.2,y:sy+0.25,w:0.55,h:0.55,align:"center",valign:"middle",fontFace:MONO,bold:true,fontSize:20,color:CY,margin:0});
  s.addText(d[1],{isTextBox:true,x:x+0.2,y:sy+1.0,w:sw-0.4,h:0.4,fontFace:TITLE,bold:true,fontSize:15,color:INK,margin:0});
  s.addText(d[2],{isTextBox:true,x:x+0.2,y:sy+1.45,w:sw-0.4,h:1.4,fontFace:BODY,fontSize:12,color:MUT,margin:0});
  if(i<4) s.addText("▶",{isTextBox:true,x:x+sw-0.02,y:sy+1.25,w:0.2,h:0.4,align:"center",valign:"middle",fontSize:12,color:CY,margin:0});
});
s.addText("Stages 1–4 are 100% deterministic Python — no LLM, no external calls. Stage 5 is a parallel compliance overlay.",
  {isTextBox:true,x:0.62,y:5.55,w:12.1,h:0.5,fontFace:BODY,italic:true,fontSize:13,color:CY,margin:0});

// ============ SLIDE 4 — DATA SOURCES & SCOPE (Q1/Q2) ============
s = p.addSlide(); bg(s); kicker(s,"QUESTION · DATA SOURCES"); title(s,"What we see — multi-source detections, not just logs");
card(s,0.62,1.85,6.0,3.4,PANEL);
s.addText("Telemetry we ingest",{isTextBox:true,x:0.85,y:2.05,w:5.5,h:0.4,fontFace:TITLE,bold:true,fontSize:16,color:CY,margin:0});
const src=["EDR / endpoint (CrowdStrike)","Network / NDR (Zeek)","IDS (Suricata)","Identity / auth (Entra ID)","DNS (Umbrella)","DLP / data loss (Purview)","Real GUIDE: 33 entity types, MITRE-tagged"];
s.addText(src.map((t,i)=>({text:t,options:{bullet:{code:"2022"},color:INK,breakLine:true,paraSpaceAfter:6}})),
  {isTextBox:true,x:0.9,y:2.5,w:5.4,h:2.6,fontFace:BODY,fontSize:13.5,margin:0});
card(s,6.75,1.85,5.95,3.4,PANEL2);
s.addText("The honest boundary",{isTextBox:true,x:6.98,y:2.05,w:5.5,h:0.4,fontFace:TITLE,bold:true,fontSize:16,color:P2,margin:0});
s.addText("We consume normalized alerts / findings from the detection layer — each carrying its entities and ATT&CK technique.\n\nWe do NOT capture raw packets or run our own sensors. The platform ingests logs, flows and WAF via SIEM, Kafka and MCP connectors; our engine works on the resulting findings.",
  {isTextBox:true,x:6.98,y:2.5,w:5.5,h:2.6,fontFace:BODY,fontSize:14,color:INK,margin:0});
s.addText("E1 is the alert stream, not raw-log parsing — this is the correct SOC-triage scope.",
  {isTextBox:true,x:0.62,y:5.5,w:12.1,h:0.5,fontFace:BODY,italic:true,fontSize:13,color:MUT,margin:0});

// ============ SLIDE 5 — CORRELATION (the process) ============
s = p.addSlide(); bg(s); kicker(s,"QUESTION · HOW WE CORRELATE"); title(s,"Union-find over shared entities + time window");
const cst=[["1","Every alert starts alone"],["2","Index alerts by the entities they touch (host / user / IP)"],
  ["3","Link alerts sharing an entity within a 60-min window"],["4","Each connected group = one incident"]];
cst.forEach((d,i)=>{ const y=1.85+i*0.72;
  s.addShape(p.ShapeType.ellipse,{x:0.62,y:y,w:0.45,h:0.45,fill:{color:PANEL},line:{color:CY,width:1}});
  s.addText(d[0],{isTextBox:true,x:0.62,y:y,w:0.45,h:0.45,align:"center",valign:"middle",fontFace:MONO,bold:true,fontSize:14,color:CY,margin:0});
  s.addText(d[1],{isTextBox:true,x:1.25,y:y,w:5.1,h:0.45,valign:"middle",fontFace:BODY,fontSize:14.5,color:INK,margin:0});
});
// the P1 bridge example on the right
card(s,6.7,1.75,6.0,4.35,PANEL2);
s.addText("The P1 — the lateral-move alert is the bridge",{isTextBox:true,x:6.95,y:1.9,w:5.5,h:0.4,fontFace:TITLE,bold:true,fontSize:14,color:CY,margin:0});
const chain=[["EDR-5521","InitialAccess","ws-042"],["EDR-5522","Execution","ws-042"],
  ["EDR-5530","CredentialAccess","ws-042"],["NET-8801","LateralMovement","ws-042 → db-prod-01"],
  ["DLP-1207","Collection","db-prod-01"],["NET-8899","Exfiltration","db-prod-01 → C2"]];
chain.forEach((d,i)=>{ const y=2.4+i*0.55; const bridge=(i===3);
  s.addText([{text:d[0]+"  ",options:{color:bridge?P1:CY,bold:true}},
    {text:d[1]+"  ",options:{color:INK}},{text:d[2],options:{color:bridge?P1:MUT}}],
    {isTextBox:true,x:6.98,y:y,w:5.55,h:0.5,fontFace:MONO,fontSize:11.5,margin:0,valign:"middle"});
});
s.addText("NET-8801 touches BOTH hosts → union-find merges the workstation cluster and the database cluster into ONE 6-alert incident.",
  {isTextBox:true,x:6.98,y:5.7,w:5.5,h:0.35,fontFace:BODY,italic:true,fontSize:11,color:MUT,margin:0});
s.addText("Transitive: 5521 ↔ ws-042 ↔ 8801 ↔ db-prod-01 ↔ 8899. Validated on GUIDE vs analysts' own IncidentId grouping.",
  {isTextBox:true,x:0.62,y:5.55,w:5.8,h:0.9,fontFace:BODY,fontSize:12.5,color:CY,margin:0});

// ============ SLIDE 6 — RISK SCORING (explainable) ============
s = p.addSlide(); bg(s); kicker(s,"RISK SCORING"); title(s,"Six impact factors — transparent, no black box");
const facs=[["Asset criticality","25","crown-jewel vs test box"],["Kill-chain stage","25","how far the attack got"],
  ["Kill-chain progression","15","multi-stage chain vs isolated"],["Blast radius","15","how many assets affected"],
  ["Detection confidence","15","signature vs heuristic"],["Corroboration","10","alerts agreeing + threat family"]];
facs.forEach((d,i)=>{ const col=i%2, row=Math.floor(i/2); const x=0.62+col*6.15, y=1.9+row*1.1;
  card(s,x,y,5.95,0.95,PANEL);
  s.addText(d[0],{isTextBox:true,x:x+0.25,y:y+0.12,w:4.0,h:0.4,fontFace:TITLE,bold:true,fontSize:15,color:INK,margin:0});
  s.addText(d[2],{isTextBox:true,x:x+0.25,y:y+0.5,w:4.5,h:0.35,fontFace:BODY,fontSize:11.5,color:MUT,margin:0});
  s.addText("+"+d[1],{isTextBox:true,x:x+4.7,y:y+0.12,w:1.0,h:0.7,align:"right",valign:"middle",fontFace:MONO,bold:true,fontSize:22,color:CY,margin:0});
});
s.addText("Score = a readable weighted sum → 0–100 → P1–P4. Every point carries a reason, so an analyst can trust it and an auditor can check it. Weights are calibrated to real analyst rankings (learning-to-rank), never hidden in a model.",
  {isTextBox:true,x:0.62,y:5.5,w:12.1,h:0.9,fontFace:BODY,fontSize:13,color:MUT,margin:0});

// ============ SLIDE 7 — TRIAGE (what is triage) ============
s = p.addSlide(); bg(s); kicker(s,"QUESTION · WHAT IS TRIAGE"); title(s,"Priority band + the action to take");
const bands=[["P1","88.1",P1,"Confirmed multi-stage attack on a crown jewel","Isolate the asset & open an incident now"],
  ["P2","53.2",P2,"Real but contained (RDP brute-force + login)","Assign to an analyst this shift"],
  ["P3","35.9",P3,"Single low-confidence signal","Queue for review; corroborate first"],
  ["P4","<25",P4,"Benign / noise","Auto-close unless corroborated"]];
bands.forEach((d,i)=>{ const y=1.85+i*1.08; card(s,0.62,y,12.08,0.95,PANEL);
  s.addShape(p.ShapeType.roundRect,{x:0.8,y:y+0.22,w:0.95,h:0.5,rectRadius:0.06,fill:{color:PANEL2},line:{color:d[2],width:1.25}});
  s.addText(d[0],{isTextBox:true,x:0.8,y:y+0.22,w:0.95,h:0.5,align:"center",valign:"middle",fontFace:MONO,bold:true,fontSize:16,color:d[2],margin:0});
  s.addText(d[1],{isTextBox:true,x:1.9,y:y+0.22,w:1.0,h:0.5,valign:"middle",fontFace:MONO,bold:true,fontSize:18,color:INK,margin:0});
  s.addText(d[3],{isTextBox:true,x:3.05,y:y+0.12,w:5.0,h:0.7,valign:"middle",fontFace:BODY,fontSize:13,color:MUT,margin:0});
  s.addText(d[4],{isTextBox:true,x:8.1,y:y+0.12,w:4.4,h:0.7,valign:"middle",fontFace:BODY,bold:true,fontSize:13,color:d[2],margin:0});
});
s.addText("Triage = cut the flood to a few incidents, rank by impact, and tell the analyst what to do first.",
  {isTextBox:true,x:0.62,y:6.35,w:12,h:0.4,fontFace:BODY,italic:true,fontSize:13,color:CY,margin:0});

// ============ SLIDE 8 — ALERT CHAINING vs EXPLOIT PATH (Q) ============
s = p.addSlide(); bg(s); kicker(s,"QUESTION · ATTACK CHAINS"); title(s,"We chain alerts — not vulnerabilities");
card(s,0.62,1.85,6.0,4.1,PANEL);
s.addText("✓  What we DO",{isTextBox:true,x:0.85,y:2.05,w:5.5,h:0.45,fontFace:TITLE,bold:true,fontSize:17,color:GRN,margin:0});
s.addText("Reconstruct the attack chain from correlated alerts. Six individually-minor alerts across three tools stitch into ONE incident — and the progression factor pushes the assembled chain to P1.\n\nA single one of those alerts is a P3 you'd never reach. Chained onto a crown-jewel DB it becomes P1 (88.1).",
  {isTextBox:true,x:0.85,y:2.55,w:5.5,h:3.2,fontFace:BODY,fontSize:14,color:INK,margin:0});
card(s,6.75,1.85,5.95,4.1,PANEL2);
s.addText("✗  What we DON'T (roadmap)",{isTextBox:true,x:6.98,y:2.05,w:5.5,h:0.45,fontFace:TITLE,bold:true,fontSize:17,color:P2,margin:0});
s.addText("We are not a vulnerability scanner or exploitation engine. We don't scan CVEs, execute exploits, or predict attack paths from vulnerabilities + AD topology (BloodHound / attack-graph territory).\n\nThat is offensive attack-graph analysis — on our roadmap, not a claim we make today.",
  {isTextBox:true,x:6.98,y:2.55,w:5.5,h:3.2,fontFace:BODY,fontSize:14,color:INK,margin:0});
s.addText("\"We reconstruct the attack chain from correlated alerts and escalate by impact — here is the six-stage P1.\"",
  {isTextBox:true,x:0.62,y:6.2,w:12.1,h:0.5,fontFace:BODY,italic:true,fontSize:13,color:CY,margin:0});

// ============ SLIDE 9 — PROOF ON REAL DATA ============
s = p.addSlide(); bg(s); kicker(s,"PROOF"); title(s,"Benchmarked on real Microsoft SOC data (GUIDE)");
// reduction chart
s.addChart(p.ChartType.bar, [{name:"count", labels:["Raw alerts","Incidents"], values:[131954,9980]}],
  {x:0.62,y:1.9,w:6.0,h:4.0, barDir:"col", chartColors:[BL,CY], showTitle:true, title:"131,954 alerts → 9,980 incidents  (13.2×)",
   titleColor:INK, titleFontSize:14, titleFontFace:TITLE, showValue:true, dataLabelPosition:"outEnd",
   dataLabelColor:INK, dataLabelFontFace:MONO, dataLabelFontSize:11, showLegend:false,
   catAxisLabelColor:MUT, valAxisLabelColor:FAINT, valAxisHidden:true, catAxisLabelFontSize:12,
   valGridLine:{style:"none"}, catGridLine:{style:"none"}, chartArea:{fill:{color:BG}}, plotArea:{fill:{color:BG}}});
const stats=[["0.896","NDCG vs real analyst QueueRank (held-out)"],["13.2×","alert → incident reduction"],
  ["332 MB","peak memory streaming 4.1M rows in 17s"],["0","LLM calls in the scoring path"]];
stats.forEach((d,i)=>{ const y=1.95+i*1.05; card(s,6.85,y,5.85,0.9,PANEL);
  s.addText(d[0],{isTextBox:true,x:7.05,y:y+0.1,w:2.0,h:0.7,valign:"middle",fontFace:MONO,bold:true,fontSize:26,color:CY,margin:0});
  s.addText(d[1],{isTextBox:true,x:9.1,y:y+0.1,w:3.5,h:0.7,valign:"middle",fontFace:BODY,fontSize:12.5,color:MUT,margin:0}); });

// ============ SLIDE 10 — COMPLIANCE / DPDP (novelty) ============
s = p.addSlide(); bg(s); kicker(s,"NOVELTY · SOC MEETS GRC"); title(s,"Regulatory exposure on the same queue");
s.addText("When an incident hits a personal-data asset at a data-loss stage, the same queue attaches the statutory obligations — deterministically, from the incident time. Triage and compliance in one view.",
  {isTextBox:true,x:0.62,y:1.55,w:12.1,h:0.7,fontFace:BODY,fontSize:14,color:MUT,margin:0});
const regs=[["CERT-In 2022","6h","4h 25m left",GRN,"In force · report to CERT-In (Annexure I)"],
  ["DPDP Act §8(6) · Rules 2025","72h","70h left",GRN,"Board + Data Principals · ₹250 Cr / ₹200 Cr"],
  ["GDPR Art. 33/34","72h","70h left",GRN,"EU DPA · €20M or 4% turnover"]];
regs.forEach((d,i)=>{ const y=2.4+i*1.15; card(s,0.62,y,12.08,1.0,PANEL);
  s.addText(d[0],{isTextBox:true,x:0.85,y:y+0.13,w:5.2,h:0.4,fontFace:TITLE,bold:true,fontSize:16,color:INK,margin:0});
  s.addText(d[4],{isTextBox:true,x:0.85,y:y+0.55,w:6.5,h:0.35,fontFace:BODY,fontSize:12,color:MUT,margin:0});
  s.addShape(p.ShapeType.roundRect,{x:9.3,y:y+0.25,w:3.15,h:0.5,rectRadius:0.25,fill:{color:PANEL2},line:{color:d[3],width:1.25}});
  s.addText(d[1]+" window · "+d[2],{isTextBox:true,x:9.3,y:y+0.25,w:3.15,h:0.5,align:"center",valign:"middle",fontFace:MONO,bold:true,fontSize:12,color:d[3],margin:0});
});
s.addText("Deterministic clocks from the incident time — no LLM. DPDP-conscious: this is what a compliance-aware SOC needs.",
  {isTextBox:true,x:0.62,y:6.05,w:12.1,h:0.5,fontFace:BODY,italic:true,fontSize:13,color:CY,margin:0});

// ============ SLIDE 11 — NO EXTERNAL DEPENDENCY / SOVEREIGNTY (Q) ============
s = p.addSlide(); bg(s); kicker(s,"QUESTION · EXTERNAL DEPENDENCY"); title(s,"The triage core runs air-gapped");
card(s,0.62,1.9,6.0,3.6,PANEL);
s.addText("Zero external calls",{isTextBox:true,x:0.85,y:2.1,w:5.5,h:0.4,fontFace:TITLE,bold:true,fontSize:17,color:GRN,margin:0});
s.addText("Correlation, risk scoring and the DPDP/CERT-In clocks are pure deterministic Python. No LLM, no external API, runs fully on-prem / air-gapped. Validated: zero LLM in the scoring path.",
  {isTextBox:true,x:0.85,y:2.6,w:5.5,h:2.7,fontFace:BODY,fontSize:14,color:INK,margin:0});
card(s,6.75,1.9,5.95,3.6,PANEL2);
s.addText("The optional LLM is sovereign",{isTextBox:true,x:6.98,y:2.1,w:5.5,h:0.4,fontFace:TITLE,bold:true,fontSize:17,color:CY,margin:0});
s.addText("The only external touch is the plain-English summary. It falls back to a template (no LLM), and can run on a local on-prem model (Ollama / vLLM) via the Bifrost gateway. Multi-provider — no lock-in.",
  {isTextBox:true,x:6.98,y:2.6,w:5.5,h:2.7,fontFace:BODY,fontSize:14,color:INK,margin:0});
s.addText("For DPDP-sensitive data, shipping Aadhaar/PAN telemetry to a foreign cloud LLM is itself a compliance risk — so the core is deterministic and any LLM can stay inside the org. That is the point.",
  {isTextBox:true,x:0.62,y:5.75,w:12.1,h:0.7,fontFace:BODY,italic:true,fontSize:13,color:P2,margin:0});

// ============ SLIDE 12 — AGENT ARCHITECTURE (Q) ============
s = p.addSlide(); bg(s); kicker(s,"QUESTION · AGENT ARCHITECTURE"); title(s,"Event-sourced harness — not LangGraph");
s.addText("Our E1 engine uses NO agents — it is deterministic code. The platform's 13 agents run on a purpose-built TypeScript harness, chosen over LangGraph/LangChain for SOC-grade guarantees:",
  {isTextBox:true,x:0.62,y:1.55,w:12.1,h:0.7,fontFace:BODY,fontSize:14,color:MUT,margin:0});
const arch=[["Markdown playbooks","WORKFLOW.md defines ordered phases — one agent each"],
  ["Durable runs","BullMQ / Redis — survive restarts"],
  ["Event-sourced Ledger","append-only log folds to state — deterministic & replayable"],
  ["MCP tools","open Model Context Protocol — integrations not hardcoded"],
  ["Bifrost gateway","multi-provider LLM routing incl. local Ollama"],
  ["Audit trail","tamper-evident: DB-enforced no-update / no-delete"]];
arch.forEach((d,i)=>{ const col=i%2,row=Math.floor(i/2); const x=0.62+col*6.15,y=2.35+row*1.25;
  card(s,x,y,5.95,1.1,PANEL);
  s.addText(d[0],{isTextBox:true,x:x+0.25,y:y+0.13,w:5.4,h:0.4,fontFace:TITLE,bold:true,fontSize:15,color:CY,margin:0});
  s.addText(d[1],{isTextBox:true,x:x+0.25,y:y+0.55,w:5.4,h:0.5,fontFace:BODY,fontSize:12.5,color:MUT,margin:0}); });
s.addText("Determinism, replay and audit — you can rebuild exactly what any decision saw. A general agent framework doesn't give that out of the box.",
  {isTextBox:true,x:0.62,y:6.35,w:12.1,h:0.4,fontFace:BODY,italic:true,fontSize:12.5,color:INK,margin:0});

// ============ SLIDE 13 — CLOSE ============
s = p.addSlide(); bg(s, PANEL2);
s.addText([{text:"Aegis",options:{color:INK}},{text:"SOC",options:{color:CY}},{text:" AI",options:{color:INK}}],
  {isTextBox:true,x:0.62,y:0.6,w:8,h:0.5,fontFace:TITLE,bold:true,fontSize:22,margin:0});
s.addText("130,000 alerts → a ranked, explained queue —\nproven against real Microsoft analysts.",
  {isTextBox:true,x:0.62,y:2.2,w:12.1,h:1.6,fontFace:TITLE,bold:true,fontSize:38,color:INK,margin:0,lineSpacingMultiple:1.0});
const close=["Explainable — every rank shows its reasoning, no black box",
  "Risk-based — impact, not raw severity (asset value + blast radius)",
  "Proven — NDCG 0.896 vs real analyst prioritisation, 13.2× fewer incidents",
  "Sovereign — deterministic core, air-gapped, DPDP/CERT-In aware"];
s.addText(close.map(t=>({text:t,options:{bullet:{code:"2022"},color:INK,breakLine:true,paraSpaceAfter:10}})),
  {isTextBox:true,x:0.7,y:4.2,w:11.5,h:2.2,fontFace:BODY,fontSize:16,margin:0});
s.addText("Explainable · Risk-based · Proven on real data",{isTextBox:true,x:0.62,y:6.7,w:12,h:0.4,fontFace:MONO,fontSize:13,color:CY,margin:0});

p.writeFile({ fileName: "/run/media/ved/B6F06788F0674E25/aegis-work/build/AegisSOC_AI_E1.pptx" }).then(f=>console.log("wrote", f));
