import { useEffect, useMemo, useState } from 'react'
import { riskApi } from '../../services/api'
import { EmptyState } from '../../shared/ui'
import type { ConsoleScreenProps } from '../../shared/types'

// Shapes mirror core/risk/dashboard.py output. View-model only (see mappers note
// in CONTEXT.md): the backend is the source of truth for every value here.
interface Factor { name: string; points: number; reason: string }
interface Clock { label: string; remaining_h: number; status: string; window_h: number }
interface Obligation {
  framework: string; regulator: string; jurisdiction: string; duty: string
  penalty: string; in_force: string; clock: Clock | null
}
interface Compliance {
  breach: boolean; reportable: boolean; pii_exposed: boolean; data_classes: string[]
  notice_required: boolean; penalty_headline: string; summary: string; obligations: Obligation[]
}
interface ChainStep {
  tactic: string; source: string | null; title: string | null
  technique: string | null; alert_id: string | null; at: string | null
}
interface Incident {
  band: string; score: number; n_alerts: number; furthest_tactic: string
  headline_asset: string; n_assets: number; tactics: string[]; why: string[]
  narrative: string; grade: string | null; factors: Factor[]; compliance?: Compliance
  chain?: ChainStep[]
}

function fmtClock(h: number): string {
  if (h < 0) return 'OVERDUE'
  const hh = Math.floor(h), mm = Math.round((h - hh) * 60)
  return `${hh}h ${String(mm).padStart(2, '0')}m left`
}
interface QueueData {
  curated: { alerts: number; sources: string[]; incidents: number; reduction: number; queue: Incident[] }
  guide?: {
    incidents?: number; alerts?: number; reduction?: number
    ndcg_vs_analyst?: number; spearman_vs_analyst?: number
    held_out_incidents?: number; top?: Incident[]; unavailable?: string
  }
}

const WMAX = 43.2 // largest single-factor weight, for factor-bar scaling
const band = (b: string) => b.toLowerCase()

function IncidentRow({ inc, rank }: { inc: Incident; rank: number }) {
  const [open, setOpen] = useState(false)
  const b = band(inc.band)
  const c = inc.compliance
  const facs = [...inc.factors].filter((f) => f.points >= 0.5).sort((a, x) => x.points - a.points)
  return (
    <div className={`rq-row ${b} ${open ? 'open' : ''}`}>
      <button className="rq-head" aria-expanded={open} onClick={() => setOpen(!open)}>
        <span className="rq-rank">{rank}</span>
        <span className={`rq-pill ${b}`}>{inc.band}</span>
        <span className="rq-who">
          <span className="rq-t">{inc.furthest_tactic}
            {c?.reportable && <span className={`rq-reg${c.breach ? ' breach' : ''}`}>⚖ {c.breach ? 'DPDP breach' : 'CERT-In'}</span>}
          </span>
          <span className="rq-a">
            <b>{inc.headline_asset}</b>
            {inc.n_assets > 1 ? ` +${inc.n_assets - 1}` : ''} · {inc.n_alerts} alert{inc.n_alerts > 1 ? 's' : ''}
          </span>
        </span>
        <span className="rq-score">
          <span className="rq-track"><span className={`rq-fill ${b}`} style={{ width: `${inc.score}%` }} /></span>
          <span className="rq-sc">{inc.score}</span>
          <span className="rq-caret">▸</span>
        </span>
      </button>
      {open && (
        <div className="rq-detail">
          <div className="rq-narr">{inc.narrative}</div>
          <div className="rq-facs">
            <h4>Why this rank — factor breakdown</h4>
            {facs.map((f) => (
              <div className="rq-fac" key={f.name}>
                <span className="rq-fn">{f.name.replace(/_/g, ' ')}</span>
                <span className="rq-ftrack"><span className="rq-ffill" style={{ width: `${Math.min(100, (f.points / WMAX) * 100)}%` }} /></span>
                <span className="rq-fp">+{f.points}</span>
                <span className="rq-reason">{f.reason}</span>
              </div>
            ))}
          </div>
          {inc.chain && inc.chain.length > 1 ? (
            <div className="rq-chain">
              <h4>Reconstructed attack chain — {inc.chain.length} alerts stitched in time order</h4>
              <ol className="rq-steps">
                {inc.chain.map((s, i) => (
                  <li className="rq-step" key={s.alert_id || i}>
                    <span className="rq-stage">{s.tactic}</span>
                    <span className="rq-step-body">
                      {s.title && <span className="rq-step-title">{s.title}</span>}
                      <span className="rq-step-meta">
                        {s.source && <span className="rq-src">{s.source}</span>}
                        {s.technique && <span className="rq-tech">{s.technique}</span>}
                        {s.at && <span className="rq-at">{s.at}</span>}
                      </span>
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          ) : (
            <div className="rq-chips">{inc.tactics.map((t) => <span className="rq-chip" key={t}>{t}</span>)}</div>
          )}
          {c && c.obligations.length > 0 && (
            <div className="rq-comp">
              <h4>⚖ Regulatory exposure — {c.penalty_headline}</h4>
              <div className="rq-comp-sum">{c.summary}</div>
              {c.obligations.map((o) => (
                <div className="rq-ob" key={o.framework}>
                  <div className="rq-ob-top">
                    <b>{o.framework}</b>
                    {o.clock && <span className={`rq-clock ${o.clock.status}`}>{o.clock.label}: {fmtClock(o.clock.remaining_h)}</span>}
                  </div>
                  <div className="rq-ob-duty">{o.duty}</div>
                  <div className="rq-ob-meta">{o.regulator} · {o.jurisdiction} · {o.penalty} · <i>{o.in_force}</i></div>
                </div>
              ))}
            </div>
          )}
          {inc.grade && <div className="rq-grade">Analyst ground truth: <b>{inc.grade}</b> · the engine never sees this</div>}
        </div>
      )}
    </div>
  )
}

export default function RiskQueueScreen(_props: ConsoleScreenProps) {
  const [data, setData] = useState<QueueData | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [tab, setTab] = useState<'curated' | 'guide'>('curated')

  useEffect(() => {
    let live = true
    riskApi.getQueue()
      .then((r) => { if (live) setData(r.data) })
      .catch((e) => { if (live) setErr(e?.message || 'Failed to load risk queue') })
    return () => { live = false }
  }, [])

  const guideReady = !!(data?.guide && data.guide.top && data.guide.top.length)
  const list = useMemo(() => {
    if (!data) return []
    return tab === 'guide' && guideReady ? data.guide!.top! : data.curated.queue
  }, [data, tab, guideReady])

  if (err) return <EmptyState icon="alert" title="Risk queue unavailable" body={err} />
  if (!data) return <EmptyState icon="shield" title="Scoring incidents…" body="Correlating alerts and computing impact-based risk." />

  const g = data.guide || {}
  const kpis: [string, string, boolean][] = [
    [`${g.reduction ?? data.curated.reduction}×`, 'Alert→incident reduction (real GUIDE data)', true],
    [g.ndcg_vs_analyst != null ? String(g.ndcg_vs_analyst) : '—', 'NDCG vs analyst queue order · held-out', true],
    [g.incidents ? `${Math.round((g.alerts || 0) / 1000)}k→${((g.incidents || 0) / 1000).toFixed(1)}k` : '—', 'Alerts triaged → incidents', false],
    ['0', 'LLM calls in the scoring path · fully explainable', false],
  ]

  return (
    <div className="rq">
      <style>{RQ_CSS}</style>
      <div className="rq-kpis">
        {kpis.map(([n, l, hl], i) => (
          <div className={`rq-kpi ${hl ? 'hl' : ''}`} key={i}><div className="rq-n">{n}</div><div className="rq-l">{l}</div></div>
        ))}
      </div>

      <div className="rq-tabs" role="tablist">
        <button role="tab" aria-selected={tab === 'curated'} className="rq-tab" onClick={() => setTab('curated')}>Curated scenario</button>
        <button role="tab" aria-selected={tab === 'guide'} className="rq-tab" onClick={() => setTab('guide')} disabled={!guideReady}>
          Real GUIDE data{!guideReady ? ' (not loaded)' : ''}
        </button>
      </div>

      <p className="rq-ctx">
        {tab === 'curated'
          ? <><b>{data.curated.alerts} alerts</b> from {data.curated.sources.length} sources correlated into <b>{data.curated.incidents} incidents</b> — {data.curated.reduction}× fewer things to look at.</>
          : <><b>{g.incidents?.toLocaleString()} real incidents</b> from {g.alerts?.toLocaleString()} Microsoft SOC alerts; ordering measured on <b>{g.held_out_incidents?.toLocaleString()} held-out incidents</b> (NDCG {g.ndcg_vs_analyst}, Spearman {g.spearman_vs_analyst}).</>}
      </p>

      <div className="rq-queue">
        {list.length
          ? list.map((inc, i) => <IncidentRow inc={inc} rank={i + 1} key={`${tab}-${i}`} />)
          : <EmptyState icon="shield" title="No incidents" body="Nothing in this view." />}
      </div>
    </div>
  )
}

// Scoped styles. Surfaces are currentColor tints so the screen adapts to the
// console's light or dark theme; band colors are explicit semantic status hues.
const RQ_CSS = `
.rq{max-width:1080px;--p1:#FF4D5E;--p2:#FFA733;--p3:#4D9EFF;--p4:#6B7A8D;--acc:#00B4D8;
  --panel:color-mix(in srgb,currentColor 4%,transparent);
  --line:color-mix(in srgb,currentColor 14%,transparent);
  --mut:color-mix(in srgb,currentColor 62%,transparent);
  --faint:color-mix(in srgb,currentColor 42%,transparent);
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
.rq-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:18px}
.rq-kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.rq-kpi.hl{border-color:color-mix(in srgb,var(--acc) 45%,var(--line))}
.rq-n{font-family:var(--mono);font-size:24px;font-weight:600;font-variant-numeric:tabular-nums;letter-spacing:-.5px}
.rq-kpi.hl .rq-n{color:var(--acc)}
.rq-l{font-size:12.5px;color:var(--mut);margin-top:4px}
.rq-tabs{display:flex;gap:6px;border-bottom:1px solid var(--line);margin-bottom:12px}
.rq-tab{appearance:none;background:none;border:0;color:var(--mut);font:inherit;font-weight:500;padding:8px 14px;
  cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px}
.rq-tab[aria-selected=true]{color:inherit;border-bottom-color:var(--acc)}
.rq-tab:disabled{opacity:.4;cursor:not-allowed}
.rq-ctx{color:var(--mut);font-size:13px;margin:0 0 14px}
.rq-queue{display:flex;flex-direction:column;gap:8px}
.rq-row{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.rq-row.p1{box-shadow:inset 3px 0 0 var(--p1)}.rq-row.p2{box-shadow:inset 3px 0 0 var(--p2)}
.rq-row.p3{box-shadow:inset 3px 0 0 var(--p3)}.rq-row.p4{box-shadow:inset 3px 0 0 var(--p4)}
.rq-head{display:grid;grid-template-columns:32px 44px 1fr auto;gap:14px;align-items:center;width:100%;
  text-align:left;background:none;border:0;color:inherit;font:inherit;padding:13px 15px;cursor:pointer}
.rq-rank{font-family:var(--mono);color:var(--faint)}
.rq-pill{font-family:var(--mono);font-size:12px;font-weight:600;text-align:center;padding:3px 0;border-radius:6px;border:1px solid}
.rq-pill.p1{color:var(--p1);border-color:color-mix(in srgb,var(--p1) 50%,transparent);background:color-mix(in srgb,var(--p1) 13%,transparent)}
.rq-pill.p2{color:var(--p2);border-color:color-mix(in srgb,var(--p2) 50%,transparent);background:color-mix(in srgb,var(--p2) 13%,transparent)}
.rq-pill.p3{color:var(--p3);border-color:color-mix(in srgb,var(--p3) 50%,transparent);background:color-mix(in srgb,var(--p3) 13%,transparent)}
.rq-pill.p4{color:var(--p4);border-color:color-mix(in srgb,var(--p4) 50%,transparent);background:color-mix(in srgb,var(--p4) 13%,transparent)}
.rq-who{min-width:0}
.rq-who .rq-t{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rq-who .rq-a{font-family:var(--mono);font-size:12px;color:var(--mut);display:block;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rq-score{display:flex;align-items:center;gap:10px}
.rq-track{width:88px;height:8px;border-radius:99px;background:color-mix(in srgb,currentColor 10%,transparent);overflow:hidden}
.rq-fill{height:100%;border-radius:99px}
.rq-fill.p1{background:var(--p1)}.rq-fill.p2{background:var(--p2)}.rq-fill.p3{background:var(--p3)}.rq-fill.p4{background:var(--p4)}
.rq-sc{font-family:var(--mono);font-weight:600;width:40px;text-align:right;font-variant-numeric:tabular-nums}
.rq-caret{color:var(--faint)}.rq-row.open .rq-caret{transform:rotate(90deg)}
.rq-detail{border-top:1px solid var(--line);padding:14px 15px 16px;display:grid;gap:14px}
.rq-narr{border-left:2px solid var(--acc);padding-left:12px;font-size:14px}
.rq-facs h4{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);margin:0 0 8px}
.rq-fac{display:grid;grid-template-columns:150px 1fr 42px;gap:12px;align-items:center;font-size:13px;margin-bottom:6px}
.rq-fn{color:var(--mut)}
.rq-ftrack{height:6px;background:color-mix(in srgb,currentColor 10%,transparent);border-radius:99px;overflow:hidden}
.rq-ffill{height:100%;background:var(--acc);border-radius:99px}
.rq-fp{font-family:var(--mono);text-align:right;font-variant-numeric:tabular-nums}
.rq-reason{grid-column:1/-1;color:var(--faint);font-size:12px;margin-top:-3px}
.rq-chips{display:flex;flex-wrap:wrap;gap:6px}
.rq-chip{font-family:var(--mono);font-size:11.5px;color:var(--mut);border:1px solid var(--line);border-radius:6px;padding:2px 8px}
.rq-chain h4{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);margin:0 0 10px}
.rq-steps{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:0}
.rq-step{display:grid;grid-template-columns:160px 1fr;gap:12px;padding:0 0 14px 18px;position:relative}
.rq-step:last-child{padding-bottom:0}
.rq-step::before{content:"";position:absolute;left:4px;top:5px;width:8px;height:8px;border-radius:99px;background:var(--acc)}
.rq-step::after{content:"";position:absolute;left:7.5px;top:13px;bottom:-1px;width:1px;background:var(--line)}
.rq-step:last-child::after{display:none}
.rq-stage{font-weight:600;font-size:13px}
.rq-step-body{min-width:0}
.rq-step-title{display:block;font-size:13px}
.rq-step-meta{display:flex;flex-wrap:wrap;gap:6px;margin-top:3px}
.rq-src,.rq-tech,.rq-at{font-family:var(--mono);font-size:11px;color:var(--mut);border:1px solid var(--line);border-radius:5px;padding:1px 7px}
.rq-at{color:var(--faint)}
.rq-grade{font-family:var(--mono);font-size:12px;color:var(--mut)}
.rq-reg{font-family:var(--mono);font-size:10.5px;font-weight:600;margin-left:8px;padding:1px 7px;
  border-radius:5px;vertical-align:middle;color:var(--p3);border:1px solid color-mix(in srgb,var(--p3) 45%,transparent);
  background:color-mix(in srgb,var(--p3) 12%,transparent)}
.rq-reg.breach{color:var(--p1);border-color:color-mix(in srgb,var(--p1) 45%,transparent);
  background:color-mix(in srgb,var(--p1) 12%,transparent)}
.rq-comp{border:1px solid color-mix(in srgb,var(--p2) 35%,var(--line));border-radius:10px;
  padding:12px 14px;background:color-mix(in srgb,var(--p2) 5%,transparent)}
.rq-comp h4{margin:0 0 4px;font-size:12.5px;font-weight:600}
.rq-comp-sum{color:var(--mut);font-size:12.5px;margin-bottom:10px}
.rq-ob{border-top:1px solid var(--line);padding:9px 0 3px}
.rq-ob:first-of-type{border-top:0;padding-top:0}
.rq-ob-top{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;font-size:13px}
.rq-ob-duty{font-size:12.5px;margin-top:3px}
.rq-ob-meta{font-family:var(--mono);font-size:11px;color:var(--faint);margin-top:3px}
.rq-clock{font-family:var(--mono);font-size:11.5px;font-weight:600;padding:2px 9px;border-radius:99px;white-space:nowrap;border:1px solid}
.rq-clock.green{color:#22C55E;border-color:color-mix(in srgb,#22C55E 45%,transparent);background:color-mix(in srgb,#22C55E 12%,transparent)}
.rq-clock.amber{color:var(--p2);border-color:color-mix(in srgb,var(--p2) 45%,transparent);background:color-mix(in srgb,var(--p2) 12%,transparent)}
.rq-clock.red,.rq-clock.overdue{color:var(--p1);border-color:color-mix(in srgb,var(--p1) 45%,transparent);background:color-mix(in srgb,var(--p1) 14%,transparent)}
@media (max-width:560px){.rq-head{grid-template-columns:26px 42px 1fr}.rq-score{grid-column:2/-1;margin-top:4px}
  .rq-fac{grid-template-columns:110px 1fr 38px}
  .rq-step{grid-template-columns:1fr;gap:2px}}
`
