import { useCallback, useEffect, useState } from 'react';
import { api, apiError, getCusdecReadiness, waitForSyncedRevision } from '../../utils/api';
import type { CusdecReadiness } from '../../types';
interface Candidate { source_reference: string; source_filename: string; page: number; description: string; quantity: string; unit: string; unit_price: string; total_price: string; hs_code?: string; origin?: string; gross_weight?: string; net_weight?: string; package_count?: string; currency?: string; source_document_id: string }
interface Saved { id: string; source_row_id: string; validity_state: string; description: string }
interface Draft { hs_code: string; origin: string; gross_weight: string; net_weight: string; package_count: string }
interface Props { id: string; onChange: (readiness: CusdecReadiness) => void }
const fields: { key: keyof Draft; label: string }[] = [{ key: 'hs_code', label: 'HS code' }, { key: 'origin', label: 'Origin country (2 letters)' }, { key: 'gross_weight', label: 'Gross weight (kg)' }, { key: 'net_weight', label: 'Net weight (kg)' }, { key: 'package_count', label: 'Packages for this item' }];
export function GoodsReviewPanel({ id, onChange }: Props) {
  const [rows, setRows] = useState<Candidate[]>([]); const [saved, setSaved] = useState<Saved[]>([]);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({}); const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const load = useCallback(async (signal?: AbortSignal) => {
    const { data } = await api.get<{ candidates: Candidate[]; saved_rows: Saved[] }>(`/shipments/${id}/goods-candidates`, { signal });
    if (signal?.aborted) return;
    setRows(data.candidates); setSaved(data.saved_rows);
    setDrafts(Object.fromEntries(data.candidates.map(row => [row.source_reference, { hs_code: row.hs_code ?? '', origin: row.origin ?? '', gross_weight: row.gross_weight ?? '', net_weight: row.net_weight ?? '', package_count: row.package_count ?? '' }])));
  }, [id]);
  useEffect(() => { const controller = new AbortController(); void load(controller.signal).catch(err => { if (!controller.signal.aborted) setError(apiError(err)); }); return () => controller.abort(); }, [load]);
  const act = async (work: (revision: number) => Promise<unknown>) => {
    setBusy(true); setError('');
    try { await work(await waitForSyncedRevision(id)); await waitForSyncedRevision(id); await load(); onChange(await getCusdecReadiness(id)); }
    catch (err) { setError(apiError(err)); } finally { setBusy(false); }
  };
  return <section className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest shadow-sm p-5 space-y-4">
    <header><p className="text-xs font-semibold text-primary uppercase tracking-wide">Goods review</p><h2 className="text-lg font-bold mt-1">Verify each invoice item</h2><p className="text-sm text-on-surface-variant mt-2">Check the source PDF, classification and packing allocation for every item. Freight and insurance are apportioned by source value, with totals reconciled before export.</p></header>
    {error && <p role="alert" className="text-error">{error}</p>}
    {!rows.length && <p>No supported invoice rows are available. Correct or replace the source document before preparing an export.</p>}
    {rows.map(row => { const draft = drafts[row.source_reference]; const record = saved.find(s => s.source_row_id === row.source_reference); return <article key={row.source_reference} className="rounded-lg border border-outline-variant/30 p-4 space-y-3">
      <h3 className="font-semibold text-sm">{row.description}</h3><a href={`${api.defaults.baseURL}/documents/${row.source_document_id}/content#page=${row.page}`} target="_blank" rel="noreferrer" className="text-primary underline text-sm">{row.source_filename} · page {row.page}</a>
      <p className="text-sm">{row.quantity} {row.unit} × {row.unit_price} = {row.total_price} {row.currency} · {record?.validity_state === 'current' ? 'Verified against current source' : 'Review required'}</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">{draft && fields.map(field => <label key={field.key} className="text-sm">{field.label}<input disabled={busy} value={draft[field.key]} onChange={event => setDrafts(current => ({ ...current, [row.source_reference]: { ...current[row.source_reference], [field.key]: event.target.value } }))} className="block mt-1 border border-outline-variant rounded-lg p-2 w-full" /></label>)}</div>
      <button disabled={busy || !draft} onClick={() => void act(revision => api.post(`/shipments/${id}/cusdec-line-items`, { ...row, ...draft, expected_revision: revision }))} className="bg-primary text-white rounded-lg p-2 disabled:opacity-40">{busy ? 'Saving review…' : record?.validity_state === 'current' ? 'Save reviewed item' : 'Verify this item'}</button>
    </article>; })}
    {!!saved.length && <details><summary className="cursor-pointer text-sm font-semibold">Saved reviews and source validity</summary><ul className="space-y-2 mt-3 text-sm">{saved.map(row => <li key={row.id} className="flex flex-wrap justify-between gap-2 border-b pb-2"><span>{row.description.slice(0, 80)} · {row.validity_state}</span><button disabled={busy} onClick={() => void act(revision => api.post(`/shipments/${id}/goods/${row.id}/remove`, { expected_revision: revision }))} className="underline text-error disabled:opacity-30">Remove review</button></li>)}</ul></details>}
  </section>;
}
