import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, apiError } from '../../utils/api';

interface Impact { id: string; type: string; artifact: { field_id?: string; value?: string | number; validity_state?: string; status?: string; reason?: string } }
interface Doc { document_id: string; source_filename: string }
const names: Record<string, string> = { Decision: 'Source decision', Memory: 'Remembered decision', ReviewTask: 'Review task', GoodsReview: 'Goods review', ExportSnapshot: 'Prepared export' };

/** Read-only preview: every listed record comes from the graph impact tool. */
export function ChangeImpactPanel({ shipmentId, documents, revision, synced }: { shipmentId: string; documents: Doc[]; revision: number; synced: boolean }) {
  const [documentId, setDocumentId] = useState(documents[0]?.document_id ?? '');
  const [result, setResult] = useState<{ documentId: string; impact: Impact[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const inspect = async () => {
    controller.current?.abort();
    const request = new AbortController(); controller.current = request;
    setLoading(true); setError(''); setResult(null);
    try {
      const { data } = await api.get<{ impact: Impact[] }>(`/shipments/${shipmentId}/change-impact`, { params: { document_id: documentId, expected_revision: revision }, signal: request.signal });
      if (!request.signal.aborted) setResult({ documentId, impact: data.impact });
    } catch (err) { if (!request.signal.aborted) setError(apiError(err)); }
    finally { if (!request.signal.aborted) setLoading(false); }
  };
  const visible = synced && result?.documentId === documentId ? result.impact : null;
  return <section className="rounded-2xl border border-primary/20 bg-surface-container-lowest overflow-hidden">
    <header className="bg-[#0d1b3e] p-5 sm:p-6 text-white"><p className="text-xs uppercase tracking-widest text-[#a8c9fa] font-semibold">Follow the evidence</p><h2 className="text-xl font-bold mt-2">What depends on this document?</h2><p className="text-sm text-white/75 mt-2">Inspect the decisions, remembered context and exports connected to a source before replacing it.</p></header>
    <div className="p-5 sm:p-6 space-y-4"><div className="flex flex-wrap gap-3 items-end"><label className="text-sm flex-1 min-w-0">Source document<select disabled={!synced || loading || !documents.length} value={documentId} onChange={event => { controller.current?.abort(); setDocumentId(event.target.value); setLoading(false); setResult(null); setError(''); }} className="block w-full rounded-lg border p-3 mt-2">{documents.map(doc => <option key={doc.document_id} value={doc.document_id}>{doc.source_filename}</option>)}</select></label><button disabled={!synced || loading || !documentId} onClick={() => void inspect()} className="rounded-lg bg-primary px-4 py-3 text-white text-sm disabled:opacity-40">{loading ? 'Tracing dependencies…' : 'Preview source dependencies'}</button></div>
      {!synced && <p role="status" className="text-sm text-on-surface-variant">Wait for graph synchronization before previewing dependencies.</p>}
      {error && <p role="alert" className="rounded-lg border border-error/30 p-3 text-error text-sm">{error} Retry the preview after graph synchronization.</p>}
      {visible && <div className="space-y-4"><p role="status" className="text-sm font-medium">{visible.length} connected {visible.length === 1 ? 'record' : 'records'} · graph revision {revision}</p>{!visible.length ? <p className="rounded-xl bg-surface-container-low p-4 text-sm">No dependent review records were found in this graph snapshot. Other shipment readiness checks still apply.</p> : <><div className="flex flex-wrap gap-2" aria-label="Dependency counts">{Object.entries(names).map(([kind, label]) => { const count = visible.filter(row => row.type === kind).length; return count ? <span key={kind} className="rounded-full bg-primary-fixed/40 px-3 py-1 text-xs font-medium">{label}: {count}</span> : null; })}</div><ol className="space-y-3">{visible.map(record => <li key={record.id} className="rounded-xl border border-outline-variant/30 p-4"><div className="flex flex-wrap justify-between gap-2"><strong className="text-sm">{names[record.type] ?? record.type}{record.artifact.field_id ? ` · ${record.artifact.field_id.split(':').at(-1)?.replaceAll('_', ' ')}` : ''}</strong><span className="text-xs text-on-surface-variant">{record.artifact.validity_state ?? record.artifact.status ?? 'Recorded'}</span></div>{record.artifact.value != null && <p className="text-sm mt-2">Reviewed value: {record.artifact.value}</p>}{record.artifact.reason && <p className="text-sm mt-1 text-on-surface-variant">{record.artifact.reason}</p>}<p className="text-xs font-mono text-outline mt-2 break-all">{record.id}</p></li>)}</ol></>}<Link to="/knowledge-graph" className="inline-block text-sm text-primary underline">Explore this shipment’s graph</Link></div>}
      <p className="text-xs text-on-surface-variant">This preview reads actual graph relationships and does not change a source or approval. Connected records can include historical or stale decisions.</p>
    </div>
  </section>;
}
