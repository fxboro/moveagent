'use client';
import { useState } from 'react';
import { Check, ExternalLink, LockKeyhole, ArrowRight } from 'lucide-react';
import type { Match } from '../types';

export default function UniversityApproval({ matches, status, busy, onApprove, onReject }: { matches: Match[]; status: string; busy: boolean; onApprove: (ids: number[]) => Promise<void>; onReject: () => Promise<void> }) {
  const [approvedIds, setApprovedIds] = useState<number[]>([]);
  const unlocked = status === 'awaiting_approval';
  const count = unlocked ? approvedIds.length : matches.filter(m => m.is_approved_by_human).length;
  const toggle = (id: number) => setApprovedIds(ids => ids.includes(id) ? ids.filter(i => i !== id) : [...ids, id]);
  return <section className="panel" id="universities"><div className="section-head"><div><span className="eyebrow">02 / HUMAN DECISION GATE</span><h2>Academic placement shortlist</h2></div><span className="tag"><LockKeyhole size={12} /> {count} / 10 APPROVED</span></div>
    <p className="section-intro">Ten research choices. Your judgment releases the application drafting phase.</p>
    {!matches.length ? <div className="empty"><GraduationMark /><h3>Your shortlist starts here</h3><p>Ingest a candidate profile to begin specialist research.<br />University choices will appear here for your review.</p></div> : <div className="university-grid">{matches.map((uni, index) => {
      const selected = unlocked ? approvedIds.includes(uni.id) : uni.is_approved_by_human;
      const safeUrl = /^https:\/\//.test(uni.source_url) ? uni.source_url : undefined;
      return <article className={`university ${selected ? 'selected' : ''}`} key={uni.id}><div className="uni-top"><span className="index">{String(index + 1).padStart(2, '0')}</span><label className="selection"><input type="checkbox" aria-label={`Approve ${uni.institution_name}`} checked={selected} disabled={!unlocked || busy} onChange={() => toggle(uni.id)} /><span>{selected && <Check size={12} />}</span></label></div><h3>{uni.institution_name}</h3><p>{uni.program_name}</p><small>{uni.tuition_fee_structure}</small><div className="uni-bottom"><span>FIT & FEES UNVERIFIED</span>{safeUrl && <a href={safeUrl} target="_blank" rel="noreferrer" aria-label={`Visit ${uni.institution_name}`}><ExternalLink size={14} /></a>}</div><details><summary>Matching rationale</summary><p>{uni.matching_rationale}</p></details></article>;
    })}</div>}
    <div className="gate-footer"><span><LockKeyhole size={14} /> {status === 'rejected' ? 'Batch rejected. Retry to research again.' : 'All 10 choices require your approval.'}</span><div><button className="text-button" disabled={!unlocked || busy} onClick={onReject}>Reject all</button><button className="primary" disabled={!unlocked || count !== 10 || busy} onClick={() => onApprove(approvedIds)}>Approve & release <ArrowRight size={15} /></button></div></div>
  </section>;
}
function GraduationMark() { return <div className="empty-mark">◇</div>; }
