import { useState } from 'react';
import type { ResolvedKeyField, FieldAssertion } from '../../types';

interface Props {
  fields: ResolvedKeyField[];
  onSelectAssertion: (assertion: FieldAssertion) => void;
  onResolveField: (field: ResolvedKeyField, resolution: { source_assertion_id?: string; manual_value?: string; reason?: string }) => void;
  resolvingFieldId?: string | null;
}

const statusStyle: Record<ResolvedKeyField['status'], string> = {
  match: 'bg-secondary-container/30 text-secondary',
  conflict: 'bg-error-container/30 text-error',
  warning: 'bg-tertiary-fixed/50 text-tertiary',
  pending: 'bg-surface-container text-outline',
  resolved: 'bg-secondary-container/30 text-secondary',
};

export function KeyFieldReconciliationPanel({ fields, onSelectAssertion, onResolveField, resolvingFieldId }: Props) {
  const [expandedChoice, setExpanded] = useState<string | null | undefined>(undefined);
  const expanded = expandedChoice === undefined ? fields.find(f => f.status === 'conflict')?.canonical_field_id : expandedChoice;
  const conflicts = fields.filter(field => field.status === 'conflict').length;


  if (!fields.length) return null;

  return (
    <section className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/20 overflow-hidden">
      <div className="p-4 flex flex-wrap gap-3 items-center justify-between border-b border-outline-variant/20">
        <div>
          <h2 className="text-sm font-bold text-on-surface flex gap-2 items-center">
            <span className="material-symbols-outlined text-primary text-[19px]">rule</span>
            Key Field Reconciliation
          </h2>
          <p className="text-[11px] text-on-surface-variant mt-1">Resolved shipment fields with evidence from every document.</p>
        </div>
        <span className={`text-[11px] font-bold rounded-full px-2.5 py-1 ${conflicts ? 'bg-error-container/30 text-error' : 'bg-secondary-container/30 text-secondary'}`}>
          {conflicts ? `${conflicts} conflict${conflicts === 1 ? '' : 's'}` : fields.some(f => f.status === 'pending' || f.status === 'warning') ? 'Review required' : 'No open conflicts'}
        </span>
      </div>
      <div className="divide-y divide-outline-variant/20">
        {fields.map(field => {
          const isExpanded = expanded === field.canonical_field_id;
          return <div key={field.canonical_field_id}>
            <button onClick={() => setExpanded(isExpanded ? null : field.canonical_field_id)} className="w-full p-3.5 flex items-center gap-3 text-left hover:bg-surface-container-low transition-colors">
              <span className={`material-symbols-outlined text-[18px] ${field.status === 'conflict' ? 'text-error' : field.status === 'match' ? 'text-secondary' : 'text-tertiary'}`}>
                {field.status === 'conflict' ? 'warning' : field.status === 'match' ? 'check_circle' : 'info'}
              </span>
              <span className="font-semibold text-xs text-on-surface flex-1">{field.label}</span>
              <span className="font-mono text-xs text-on-surface">{String(field.consensus_value)} {field.unit ?? ''}</span>
              <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${statusStyle[field.status]}`}>{field.status}</span>
              <span className="material-symbols-outlined text-outline text-[17px]">{isExpanded ? 'expand_less' : 'expand_more'}</span>
            </button>
            {isExpanded && <div className="px-4 pb-4">
              <div className="ml-7 rounded-lg overflow-hidden border border-outline-variant/20">
                {field.assertions.map(assertion => <button key={assertion.assertion_id} onClick={() => onSelectAssertion(assertion)} className={`w-full text-left p-3 flex flex-wrap gap-2 items-center border-b last:border-0 border-outline-variant/15 hover:bg-surface-container-low transition-colors ${assertion.is_outlier ? 'bg-error/10' : ''}`}>
                  <span className="text-[10px] uppercase text-outline min-w-32">{assertion.document_label}</span>
                  <span className={`font-mono text-xs font-semibold flex-1 ${assertion.is_outlier ? 'text-error' : 'text-on-surface'}`}>{assertion.raw_value}</span>
                  {assertion.is_outlier && <span className="text-[10px] text-error font-bold">Δ {assertion.variance} {field.unit ?? ''}</span>}
                  <span className="text-[10px] text-outline">P{assertion.page} · {assertion.extraction_confidence > 0 ? `${(assertion.extraction_confidence * 100).toFixed(0)}% heuristic` : 'not measured'}</span>
                </button>)}
                <div className="p-2.5 bg-primary-fixed/15 text-[10px] text-primary font-semibold">
                  {field.status === 'resolved' ? `Resolved value: ${String(field.consensus_value)} ${field.unit ?? ''}` : `Consensus: ${String(field.consensus_value)} ${field.unit ?? ''}`}
                </div>
              </div>
              {field.status !== 'match' && field.status !== 'resolved' && (
                <div className="ml-7 mt-3 rounded-lg border border-primary/20 bg-primary-fixed/10 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <h3 className="text-xs font-bold text-on-surface">Resolve this field</h3>
                      <p className="text-[11px] text-on-surface-variant mt-0.5">Choose verified source evidence. Replace a source document through the context workflow when its contents need correction.</p>
                    </div>
                    {resolvingFieldId === field.canonical_field_id && <span className="text-[11px] text-primary font-semibold">Saving…</span>}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {field.assertions.map(assertion => (
                      <button key={`use-${assertion.assertion_id}`}
                        disabled={resolvingFieldId === field.canonical_field_id}
                        onClick={() => onResolveField(field, { source_assertion_id: assertion.assertion_id, reason: `Selected ${assertion.document_label} evidence.` })}
                        className="px-2.5 py-1.5 rounded-md bg-white border border-outline-variant/30 text-[11px] font-semibold text-on-surface hover:border-primary hover:text-primary disabled:opacity-60">
                        Use {assertion.raw_value}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>}
          </div>;
        })}
      </div>
    </section>
  );
}

