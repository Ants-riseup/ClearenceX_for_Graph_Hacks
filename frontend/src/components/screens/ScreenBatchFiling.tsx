import { useEffect, useState } from 'react';
import { api, apiError, downloadBlob, listDossiers, type DossierSummary } from '../../utils/api';
import { useAuth } from '../../hooks/useAuth';
interface Props { onTriggerToast: (t: { title: string; message: string }) => void }
interface Batch { batch_id: string; status: string; items: { shipment_id: string; status: string; detail?: unknown; export_id?: string }[] }
function blockerMessages(detail: unknown): string[] {
  if (typeof detail === 'string') return [detail];
  if (!detail || typeof detail !== 'object') return [];
  const value = detail as { message?: unknown; readiness?: { blockers?: { message?: unknown }[] } };
  const blockers = value.readiness?.blockers;
  if (Array.isArray(blockers)) return blockers.flatMap(b => typeof b.message === 'string' ? [b.message] : []);
  return [typeof value.message === 'string' ? value.message : 'Open CUSDEC Export for this dossier to review the required actions.'];
}
export function ScreenBatchFiling(_props: Props) {
  const { user } = useAuth(); const [rows, setRows] = useState<DossierSummary[]>([]); const [selected, setSelected] = useState<string[]>([]); const [batches, setBatches] = useState<Batch[]>([]); const [search, setSearch] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const load = async (signal?: AbortSignal) => { const [d, b] = await Promise.all([listDossiers({ search, limit: 50 }, signal), api.get<{ batches: Batch[] }>('/batch-exports', { signal })]); setRows(d.dossiers); setBatches(b.data.batches); };
  useEffect(() => { const c = new AbortController(); void Promise.all([listDossiers({ limit: 50 }, c.signal), api.get<{ batches: Batch[] }>('/batch-exports', { signal: c.signal })]).then(([d, b]) => { setRows(d.dossiers); setBatches(b.data.batches); }).catch(err => { if (!c.signal.aborted) setError(apiError(err)); }); return () => c.abort(); }, []);
  const prepare = async () => { setBusy(true); setError(''); try { const dossiers = Object.fromEntries(rows.filter(r => selected.includes(r.dossier_id)).map(r => [r.dossier_id, r.revision])); await api.post('/batch-exports', { request_id: crypto.randomUUID(), dossiers }); setSelected([]); await load(); } catch (err) { setError(apiError(err)); } finally { setBusy(false); } };
  const download = async (id: string) => { setError(''); try { const { data } = await api.get(`/batch-exports/${id}/content`, { responseType: 'blob' }); downloadBlob(data, `ClearanceX_batch_${id.slice(0, 8)}.zip`); } catch (err) { setError(apiError(err, 'Batch download failed. A prepared export may be stale; prepare a new batch.')); } };
  return <section className="max-w-6xl w-full mx-auto p-5 sm:p-8 space-y-6"><h1 className="text-2xl font-bold">Batch export preparation</h1><p className="text-sm text-on-surface-variant">Select up to ten real dossiers. Each must pass its own readiness checks. The archive contains prepared XML files and a manifest identifying every success or blocker. This does not transmit declarations.</p>
    {error && <p role="alert" className="text-error border rounded-lg p-4">{error}</p>}
    <form onSubmit={e => { e.preventDefault(); setSelected([]); void load().catch(err => setError(apiError(err))); }} className="flex gap-3"><label className="flex-1 text-sm">Search references<input value={search} onChange={e => setSearch(e.target.value)} className="border rounded-lg p-2 block w-full mt-1" /></label><button className="border rounded-lg p-2 self-end">Search / refresh</button></form>
    <ul className="border rounded-xl divide-y bg-surface-container-lowest">{rows.map(r => <li key={r.dossier_id} className="p-4"><label className="flex items-center gap-3"><input type="checkbox" checked={selected.includes(r.dossier_id)} disabled={busy || user?.role === 'viewer' || (!selected.includes(r.dossier_id) && selected.length >= 10)} onChange={e => setSelected(ids => e.target.checked ? [...ids, r.dossier_id] : ids.filter(id => id !== r.dossier_id))} /><span>{r.title} · {r.dossier_id.slice(0, 8)} · {r.export_allowed ? 'Ready for export' : 'Needs review'} · revision {r.revision} · graph {r.graph_revision === r.revision ? 'synced' : 'pending'}</span></label></li>)}</ul>
    <button disabled={busy || !selected.length || user?.role === 'viewer'} onClick={() => void prepare()} className="bg-primary text-white rounded-lg p-3 disabled:opacity-40">Prepare {selected.length} selected dossiers</button>
    <section className="space-y-4"><h2 className="font-semibold text-lg">Saved batches</h2>{!batches.length && <p className="text-sm">No batch jobs have been created.</p>}{batches.map(b => <article key={b.batch_id} className="border rounded-xl p-4 space-y-3"><h3 className="font-semibold">{b.batch_id.slice(0, 8)} · {b.status}</h3><ul className="text-sm space-y-2">{b.items.map(i => <li key={i.shipment_id}>{i.shipment_id.slice(0, 8)} · {i.status}{i.detail != null && <ul className="list-disc pl-5 mt-2 space-y-1">{blockerMessages(i.detail).map((message, index) => <li key={index}>{message}</li>)}</ul>}</li>)}</ul><button disabled={busy || user?.role === 'viewer' || !b.items.some(i => i.status === 'prepared')} onClick={() => void download(b.batch_id)} className="border rounded-lg p-2 disabled:opacity-40">Download available prepared files and manifest</button></article>)}</section>
  </section>;
}
