import { BriefcaseBusiness, GraduationCap, BookOpen, Wrench } from 'lucide-react';
import type { Scores } from '../types';

export default function OpportunityMatrix({ scores, demo }: { scores: Scores | null; demo: boolean }) {
  const paths = [
    { label: 'Direct work', sub: 'Professional placement', value: scores?.direct_work, icon: BriefcaseBusiness },
    { label: 'Master’s degree', sub: 'Postgraduate pathway', value: scores?.masters_score, icon: GraduationCap },
    { label: 'Bachelor’s degree', sub: 'Undergraduate pathway', value: scores?.bachelors_score, icon: BookOpen },
    { label: 'Ausbildung', sub: 'Vocational training', value: scores?.ausbildung_score, icon: Wrench },
  ];
  return <section className="panel" id="opportunities"><div className="section-head"><div><span className="eyebrow">01 / PATHWAY INTELLIGENCE</span><h2>Opportunity matrix</h2></div><span className="tag">{demo ? 'ILLUSTRATIVE' : 'INDICATIVE SCORES'}</span></div>
    <div className="pathways">{paths.map(({ label, sub, value, icon: Icon }) => <div className="pathway" key={label}><Icon size={20} /><p>{label}</p><small>{sub}</small><div className="score">{value ?? '—'}<span>/100</span></div><div className="bar"><i style={{ width: `${value ?? 0}%` }} /></div></div>)}</div>
    <div className="strategy"><span className="gold">CONCIERGE STRATEGY</span><p>{scores?.monetization_strategy || 'Add a candidate profile to assess four placement pathways and prepare a consultancy strategy.'}</p></div>
    <p className="footnote">Scores support review; they are not admission, employment or visa probabilities.</p>
  </section>;
}
