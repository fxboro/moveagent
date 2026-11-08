'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowDownToLine, ArrowRight, Bell, ChevronDown, CircleHelp, FileText, Globe2, LayoutDashboard, Loader2, Plus, Radio, ShieldCheck, Sparkles, Upload, Users, X } from 'lucide-react';
import OpportunityMatrix from './components/OpportunityMatrix';
import UniversityApproval from './components/UniversityApproval';
import { api, type Dashboard, type Detail } from './types';

export default function CommandCenter() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [showIntake, setShowIntake] = useState(false);
  const [name, setName] = useState('');
  const [cv, setCv] = useState('');
  const [language, setLanguage] = useState('None');
  const [checking, setChecking] = useState('');
  const [tab, setTab] = useState('overview');
  const selectedRef = useRef(selectedId);
  selectedRef.current = selectedId;
  const refresh = useCallback(async () => {
    const data = await api<Dashboard>('/dashboard');
    setDashboard(data);
    if (selectedRef.current === null && data.candidates.length) setSelectedId(data.candidates[0].id);
    if (selectedRef.current !== null) {
      const id = selectedRef.current;
      const current = await api<Detail>(`/candidates/${id}`);
      if (selectedRef.current === id) setDetail(current);
    }
  }, []);
  useEffect(() => {
    let mounted = true;
    const load = () => refresh().catch(e => { if (mounted) setError(e.message); });
    load();
    const timer = setInterval(load, 3000);
    return () => { mounted = false; clearInterval(timer); };
  }, [refresh]);
  useEffect(() => { setDetail(null); refresh().catch(e => setError(e.message)); }, [selectedId, refresh]);
  async function action(fn: () => Promise<unknown>) {
    setBusy(true); setError('');
    try { await fn(); await refresh(); } catch (e) { setError(e instanceof Error ? e.message : 'Operation failed'); } finally { setBusy(false); }
  }
  async function ingest(event: React.FormEvent) {
    event.preventDefault();
    await action(async () => {
      const result = await api<{ candidate_id: number }>('/candidates/triage', { method: 'POST', body: JSON.stringify({ name, raw_cv_text: cv, language_level: language }) });
      setSelectedId(result.candidate_id); setShowIntake(false); setName(''); setCv('');
    });
  }
  async function check(source: string) {
    setChecking(source); setError('');
    try { await api('/checks', { method: 'POST', body: JSON.stringify({ source, institution_name: 'General portal check' }) }); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Check failed'); } finally { setChecking(''); }
  }
  async function exportFile(format: string) {
    await action(async () => {
      const response = await fetch(`/api/candidates/${selectedId}/export/${format}`);
      if (!response.ok) throw new Error('Export failed. The dossier must be completed first.');
      const url = URL.createObjectURL(await response.blob());
      const a = document.createElement('a'); a.href = url; a.download = `candidate-${selectedId}-dossier.${format}`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
  }
  const candidates = dashboard?.candidates ?? [];
  const working = candidates.filter(c => ['queued', 'triage', 'matching', 'approved', 'drafting'].includes(c.current_status)).length;
  const navigation = [{ id: 'overview', label: 'Command center', icon: LayoutDashboard }, { id: 'candidates', label: 'Candidate portfolio', icon: Users }, { id: 'dossiers', label: 'Document studio', icon: FileText }];
  return <div className="app-shell"><aside className="sidebar"><a href="#" className="brand"><span className="brand-symbol">E<span>◆</span></span><div>EURO–AFRO<span>ELITE CONSULTANCY</span></div></a><div className="workspace-tag"><span className="green-dot" /> PRIVATE WORKSPACE</div><p className="nav-label">OPERATIONS</p><nav>{navigation.map(({ id, label, icon: Icon }) => <button key={id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}><Icon size={18} />{label}{id === 'candidates' && <span className="nav-count">{candidates.length}</span>}</button>)}</nav><p className="nav-label intelligence">INTELLIGENCE</p><a className="nav-link" href="#market"><Globe2 size={18} /> Market pulse</a><a className="nav-link" href="#activity"><Radio size={18} /> Agent activity{working > 0 && <span className="green-dot" />}</a><div className="sidebar-bottom"><div className="concierge-card"><ShieldCheck size={22} /><p>Human judgment.<br /><span>Machine precision.</span></p><small>Every application begins<br />with your approval.</small></div><a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer" className="nav-link"><CircleHelp size={17} /> API documentation</a><div className="operator"><span>EA</span><div>Principal advocate<small>Single-user workspace</small></div></div></div></aside>
    <div className="main-shell"><header className="topbar"><div><span className="muted">Workspace</span><span className="slash">/</span>Command center</div><div className="topbar-right"><span className="status-dot" />{dashboard ? `${dashboard.mode === 'demo' ? 'Demo' : 'Live'} mode` : 'Connecting'}<a href="#market" aria-label="View market updates"><Bell size={18} /></a><span className="avatar">EA</span></div></header><main>
      <div className="page-heading"><div><span className="eyebrow gold">PRECISION PLACEMENT. EXCEPTIONAL FUTURES.</span><h1>{tab === 'dossiers' ? 'Document studio' : tab === 'candidates' ? 'Candidate portfolio' : 'The command center'}<span className="gold">.</span></h1><p>Your strategic vantage point across talent, opportunity and borders.</p></div><button className="primary" onClick={() => setShowIntake(true)}><Plus size={17} /> New candidate</button></div>
      {error && <div className="error" role="alert">{error}<button onClick={() => { setError(''); refresh().catch(e => setError(e.message)); }} aria-label="Retry connection">Retry</button></div>}
      {dashboard?.mode === 'demo' && <div className="demo-banner"><Sparkles size={15} /> Demonstration workspace — scores and university research are illustrative. Live GPT-4o requires backend configuration.</div>}
      <div className="stats"><Stat label="CANDIDATE PORTFOLIO" value={candidates.length} caption="Profiles under your care" icon={<Users size={18} />} /><Stat label="AWAITING YOUR REVIEW" value={candidates.filter(c => c.current_status === 'awaiting_approval').length} caption="Human decisions that matter" icon={<ShieldCheck size={18} />} /><Stat label="DOSSIERS PREPARED" value={candidates.filter(c => c.current_status === 'completed').length} caption="Ready for final review" icon={<FileText size={18} />} /><Stat label="ACTIVE WORKFLOWS" value={working} caption={working ? 'Specialists are processing' : 'Ready when you are'} icon={<Radio size={18} />} /></div>
      {tab === 'candidates' && <section className="panel portfolio"><div className="section-head"><h2>Your candidate portfolio</h2><span className="tag">{candidates.length} PROFILES</span></div>{!candidates.length ? <p className="section-intro">Add your first candidate to begin.</p> : candidates.map(c => <button key={c.id} onClick={() => { setSelectedId(c.id); setTab('overview'); }}><span>{c.name}<small>German: {c.language_level} · {c.mode}</small></span><span className="tag">{c.current_status.replaceAll('_', ' ')}</span><ArrowRight size={16} /></button>)}</section>}
      <div className="workspace-grid"><div className="workspace-main"><div className="candidate-bar"><div className="candidate-avatar">{detail?.name.slice(0, 2).toUpperCase() || '—'}</div><div><span className="eyebrow">ACTIVE CANDIDATE</span><label className="sr-only" htmlFor="candidate">Select candidate</label><select id="candidate" value={selectedId ?? ''} onChange={e => setSelectedId(Number(e.target.value))}><option value="" disabled>Select a profile</option>{candidates.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div><span className="candidate-state">{detail?.current_status.replaceAll('_', ' ') || 'No profile selected'}</span>{detail && ['failed', 'rejected'].includes(detail.current_status) && <button className="secondary" disabled={busy} onClick={() => action(() => api(`/candidates/${selectedId}/retry`, { method: 'POST' }))}>Retry</button>}</div>
      {detail?.error && <p className="error" role="alert">{detail.error}</p>}
      {tab !== 'dossiers' && <><OpportunityMatrix scores={detail?.triage_matrix ?? null} demo={detail?.mode === 'demo' || dashboard?.mode === 'demo'} /><UniversityApproval key={selectedId + ':' + detail?.matches.map(m => m.id).join(',')} matches={detail?.matches ?? []} status={detail?.current_status ?? ''} busy={busy} onApprove={ids => action(() => api(`/candidates/${selectedId}/approve`, { method: 'POST', body: JSON.stringify({ approved_ids: ids }) }))} onReject={() => action(() => api(`/candidates/${selectedId}/reject`, { method: 'POST' }))} /></>}
      <section className="panel" id="dossiers"><div className="section-head"><div><span className="eyebrow">03 / APPLICATION CRAFT</span><h2>Strategic dossier</h2></div><FileText size={20} className="gold" /></div>{detail?.dossiers.length ? <div className="dossier-list">{detail.dossiers.map(d => <details key={d.id}><summary>{d.document_type.replaceAll('_', ' ')}<ChevronDown size={15} /></summary><pre>{d.content}</pre></details>)}</div> : <p className="section-intro">Motivation letter, cover letter and enquiry email unlock after your ten-match approval.</p>}<div className="document-footer"><span className="muted">Confidential · Editable · Human review required</span><button className="secondary" disabled={detail?.current_status !== 'completed' || busy} onClick={() => exportFile('docx')}><ArrowDownToLine size={14} /> Word</button><button className="primary" disabled={detail?.current_status !== 'completed' || busy} onClick={() => exportFile('pdf')}><ArrowDownToLine size={14} /> PDF dossier</button></div></section>
      </div><aside className="right-column"><section className="panel market" id="market"><div className="section-head"><h2>Market pulse</h2><Radio size={17} className="gold" /></div><p className="eyebrow">OFFICIAL SOURCES · ON DEMAND</p><div className="pulse-intro"><span className="pulse-orbit"><Globe2 size={30} /></span><h3>Intelligence you can verify.</h3><p>Check official portals before making a placement decision.</p></div>{[{ id: 'anabin', title: 'Anabin / KMK', text: 'Institution recognition' }, { id: 'zab', title: 'ZAB', text: 'Qualification evaluation' }, { id: 'migration', title: 'Make it in Germany', text: 'Migration requirements' }].map(s => <div className="source-row" key={s.id}><div><h4>{s.title}</h4><p>{s.text}</p></div><button aria-label={`Check ${s.title}`} disabled={!!checking} onClick={() => check(s.id)}>{checking === s.id ? <Loader2 size={16} className="spin" /> : <ArrowRight size={17} />}</button></div>)}<div className="pulse-results">{dashboard?.checks.slice(0, 3).map(c => <div key={c.id}><span className="tag">{c.status.replaceAll('_', ' ')}</span><a href={c.source_url} target="_blank" rel="noreferrer">{c.source} ↗</a><p>{c.note}</p><small>{new Date(c.checked_at).toLocaleString()}</small></div>)}</div><p className="footnote">Portal availability does not verify an institution or migration eligibility. No unverified regulatory alerts are displayed.</p></section>
      <button className="intake-card" onClick={() => setShowIntake(true)}><span className="upload-circle"><Upload size={23} /></span><h3>A new beginning.</h3><p>Ingest candidate credentials<br />and uncover the next pathway.</p><span className="gold">Add candidate profile <ArrowRight size={14} /></span></button>
      <section className="panel activity" id="activity"><div className="section-head"><h2>Agent activity</h2><span className="green-dot" /></div>{detail?.events.length ? <ol>{detail.events.slice(-7).reverse().map(e => <li key={e.id}><span className="timeline-dot" /><h4>{e.agent}</h4><p>{e.message}</p><small>{new Date(e.created_at).toLocaleTimeString()}</small></li>)}</ol> : <div className="activity-empty"><Radio size={21} /><p>Agents are on standby.</p><small>Your workflow history appears here.</small></div>}</section></aside></div>
      <footer className="page-footer"><span>EURO–AFRO ELITE CONSULTANCY</span><span>Private by design. Guided by you.</span></footer>
    </main></div>
    {showIntake && <div className="modal-backdrop" onClick={e => { if (e.target === e.currentTarget && !busy) setShowIntake(false); }}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="intake-title"><button className="close" aria-label="Close intake" disabled={busy} onClick={() => setShowIntake(false)}><X size={20} /></button><span className="eyebrow gold">CANDIDATE INTAKE</span><h2 id="intake-title">The next chapter starts here.</h2><p>Paste extracted CV or transcript text. Profiles remain in your local database; live mode sends them to OpenAI for assessment.</p><form onSubmit={ingest}><label>Candidate name<input autoFocus required maxLength={120} value={name} onChange={e => setName(e.target.value)} /></label><label>German language level<select value={language} onChange={e => setLanguage(e.target.value)}>{['None', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2'].map(l => <option key={l}>{l}</option>)}</select></label><label>CV / transcript text<textarea required minLength={30} maxLength={30000} rows={8} placeholder="Qualifications, work experience, subject credits, languages and placement goals…" value={cv} onChange={e => setCv(e.target.value)} /></label><label className="file-label">Or load a plain text file<input type="file" accept=".txt,text/plain" onChange={async e => { const file = e.target.files?.[0]; if (file) { if (file.size > 120000) { setError('Text file is too large. Use up to 30,000 characters.'); return; } setCv((await file.text()).slice(0, 30000)); } }} /></label>{error && <p role="alert" className="gold">{error}</p>}<button className="primary" disabled={busy || !name.trim() || cv.trim().length < 30}>{busy ? <Loader2 className="spin" size={16} /> : <Sparkles size={16} />} Begin four-way assessment</button></form></section></div>}
  </div>;
}
function Stat({ label, value, caption, icon }: { label: string; value: number; caption: string; icon: React.ReactNode }) { return <div className="stat"><div><span className="eyebrow">{label}</span>{icon}</div><strong>{String(value).padStart(2, '0')}</strong><p>{caption}</p></div>; }
