import { useCallback, useEffect, useState, useRef } from 'react';
import { api, apiError } from '../../utils/api';
import { useShipment } from '../../hooks/useShipment';
import { useAuth } from '../../hooks/useAuth';
import { DossierControls } from '../review/DossierControls';
import { ChangeImpactPanel } from '../review/ChangeImpactPanel';

interface Task { id: string; field_id: string; evidence_ids: string[]; reason: string; status: string }
interface Decision { id: string; field_id: string; value: string | number; reason: string; validity_state: string; status: string }
interface Doc { document_id: string; source_filename: string; document_type: string; fixture: boolean }
interface Context { title: string; source_revision: number; graph_revision: number; status: string; tasks: Task[]; decisions: Decision[]; documents: Doc[]; archived_documents: Doc[] }
interface Field { canonical_field_id: string; label: string; status: string; consensus_value: string | number; unit: string | null }
interface Evidence { assertion_id: string; document_id: string; document_label: string; raw_value: string; normalized_value: string | number; unit?: string; confidence_status?: string; warnings?: string[]; page: number; bbox: number[] }
interface Run { run_id: string; status: string; question: string; result: { answer?: string; error?: string; uncertainties?: string[]; citations?: Evidence[]; tool_events?: { tool: string }[]; model?: string; usage?: { input_tokens: number; output_tokens: number; estimated_usd: number } } }

export function ScreenContextAgent() {
  const { shipmentId, setShipmentId } = useShipment();
  const { user } = useAuth();
  const [context, setContext] = useState<Context | null>(null);
  const [fields, setFields] = useState<Field[]>([]);
  const [fieldsLoading, setFieldsLoading] = useState(false);
  const [fieldId, setFieldId] = useState('');
  const [evidenceResult, setEvidenceResult] = useState<{ fieldId: string; values: Evidence[] } | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [question, setQuestion] = useState('Why is this shipment blocked? Retrieve the conflicting evidence and propose the next review action.');
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [source, setSource] = useState<Evidence | null>(null);
  const [draftLoaded, setDraftLoaded] = useState(false);
  const [draftStatus, setDraftStatus] = useState('');
  const canWrite = user?.role === 'user' || user?.role === 'reviewer' || user?.role === 'admin';
  const synced = context?.status === 'synced';
  const evidence = evidenceResult?.fieldId === fieldId && synced ? evidenceResult.values : [];
  const base = `/shipments/${shipmentId}`;
  const latestRequest = useRef(0);
  const sourceRevision = context?.source_revision;
  useEffect(() => {
    if (!shipmentId) return;
    const c = new AbortController();
    void api.get(`${base}/review-draft`, { signal: c.signal }).then(({ data }) => {
      if (data.draft) { setReason(data.draft.reason); setFieldId(data.draft.field_id); setDraftStatus(data.draft.expected_revision === data.current_revision ? 'Private draft restored.' : 'Draft restored from older evidence. Verify current sources before approving.'); }
      setDraftLoaded(true);
    }).catch(err => { if (!c.signal.aborted) setError(apiError(err)); });
    return () => c.abort();
  }, [shipmentId, base]);
  useEffect(() => {
    if (!draftLoaded || !canWrite || !sourceRevision || !fieldId) return;
    const c = new AbortController();
    const timer = window.setTimeout(() => { void api.post(`${base}/review-draft`, { reason, field_id: fieldId, expected_revision: sourceRevision }, { signal: c.signal }).then(() => setDraftStatus('Private draft saved.')).catch(err => { if (!c.signal.aborted) setDraftStatus(apiError(err)); }); }, 700);
    return () => { window.clearTimeout(timer); c.abort(); };
  }, [base, canWrite, sourceRevision, draftLoaded, fieldId, reason]);
  const refresh = useCallback(async () => {
    if (!shipmentId) return;
    const ticket = ++latestRequest.current;
    const [{ data: state }, { data: history }] = await Promise.all([api.get<Context>(`${base}/context-status`), api.get<{ runs: Run[] }>(`${base}/agent-runs`)]);
    if (ticket !== latestRequest.current) return;
    setContext(state); setRuns(history.runs);
    if (state.status === 'synced') {
      setFieldsLoading(true);
      try {
        const { data } = await api.get<{ fields: Field[] }>(`${base}/context-issues`);
        if (ticket !== latestRequest.current) return;
        setFields(data.fields);
        setFieldId(current => data.fields.some(f => f.canonical_field_id === current) ? current : data.fields[0]?.canonical_field_id ?? '');
      } finally {
        if (ticket === latestRequest.current) setFieldsLoading(false);
      }
    }
  }, [shipmentId, base]);
  useEffect(() => {
    if (!shipmentId) return;
    let active = true;
    let timer: number | undefined;
    // Wait for the entire refresh before polling again. A fixed interval can
    // invalidate every slow field response before it reaches the dropdown.
    const load = async () => {
      try { await refresh(); }
      catch (err) { if (active) setError(apiError(err)); }
      finally { if (active) timer = window.setTimeout(() => void load(), 3000); }
    };
    void load();
    return () => { active = false; latestRequest.current += 1; window.clearTimeout(timer); };
  }, [shipmentId, refresh]);
  useEffect(() => {
    if (!shipmentId || !fieldId || !synced) return;
    let active = true;
    api.get<{ evidence: Evidence[] }>(`${base}/context-evidence`, { params: { field_id: fieldId } })
      .then(({ data }) => { if (active) setEvidenceResult({ fieldId, values: data.evidence }); })
      .catch(err => { if (active) setError(apiError(err)); });
    return () => { active = false; };
  }, [shipmentId, fieldId, base, synced, context?.graph_revision]);
  const action = async (work: () => Promise<unknown>) => {
    setBusy(true); setError('');
    try { await work(); await refresh(); } catch (err) { setError(apiError(err)); } finally { setBusy(false); }
  };
  const create = async () => {
    setBusy(true); setError('');
    try { const { data } = await api.post('/demo/dossiers'); setShipmentId(data.shipment_id); }
    catch (err) { setError(apiError(err)); } finally { setBusy(false); }
  };
  const propose = () => action(() => api.post(`${base}/review-tasks`, { field_id: fieldId,
    evidence_ids: evidence.map(e => e.assertion_id), reason, expected_revision: context?.source_revision }));
  const approve = (task: Task, assertion: Evidence, reject = false) => action(() => api.post(`${base}/review-tasks/${task.id}/decision`, {
    field_id: fieldId, assertion_id: assertion.assertion_id, reason, expected_revision: context?.source_revision,
    request_id: crypto.randomUUID(), reject,
  }));
  const field = fields.find(f => f.canonical_field_id === fieldId);
  const pending = context?.tasks.filter(t => t.field_id === fieldId && t.status === 'pending') ?? [];
  return <div className="max-w-7xl w-full mx-auto p-4 sm:p-8 flex flex-col gap-6">
    <header className="flex flex-wrap items-start justify-between gap-4">
      <div><p className="text-xs uppercase tracking-widest text-primary font-bold">Evidence · Decisions · Change impact</p><h1 className="text-3xl font-bold mt-2">Context Agent</h1><p className="text-sm text-on-surface-variant mt-2 max-w-2xl">Investigate conflicting shipment evidence. When a source changes, trace which approvals need review again.</p></div>
      {canWrite && <button disabled={busy} onClick={() => void create()} className="rounded-lg bg-primary text-white px-4 py-3 text-sm disabled:opacity-50">Create synthetic example</button>}
    </header>
    {error && <div role="alert" className="border border-error/30 text-error rounded-lg p-4">{error}{shipmentId && <button className="block underline mt-2" onClick={() => setShipmentId(null)}>Clear dossier selection</button>}</div>}
    {!shipmentId ? <p className="p-8 rounded-xl bg-surface-container-lowest">Select a dossier from Overview, or create a synthetic example. Example extraction is precomputed; graph queries and review actions run against real services.</p> : <>
      <div className="flex flex-wrap justify-between gap-3 p-4 bg-surface-container-lowest rounded-xl border border-outline-variant/30">
        <span className="font-mono text-xs">Dossier {shipmentId.slice(0, 8)}</span><span className="text-sm font-semibold" aria-live="polite">{synced ? `Graph synced · revision ${context?.graph_revision}` : 'Graph synchronization pending'}</span>
        {canWrite && !synced && <button onClick={() => void action(() => api.post(`${base}/context-retry`))} disabled={busy} className="text-primary underline text-sm">Retry synchronization</button>}
      </div>
      {context?.documents.some(d => d.fixture) && <p className="rounded-lg bg-amber-100 p-3 text-sm text-amber-900">Synthetic documents with precomputed extraction. This example does not claim live OCR, customs approval, or a real shipment.</p>}
      <div className="grid lg:grid-cols-2 gap-6">
        <section className="p-5 bg-surface-container-lowest rounded-xl border border-outline-variant/30 flex flex-col gap-4">
          <h2 className="font-bold text-lg">Investigate with graph context</h2>
          <label className="text-sm">Question<textarea value={question} onChange={e => setQuestion(e.target.value)} maxLength={2000} rows={3} className="block w-full mt-2 p-3 rounded-lg border" /></label>
          <button disabled={!synced || busy || !canWrite || question.trim().length < 5 || runs.some(r => r.status === 'running')} onClick={() => void action(() => api.post(`${base}/agent-runs`, { question }))} className="bg-primary text-white rounded-lg p-3 text-sm disabled:opacity-40">{runs.some(r => r.status === 'running') ? 'Investigation running…' : 'Run investigation'}</button>
          <p className="text-xs text-on-surface-variant">Requires a configured OpenAI model and usage allowance. Evidence review works independently; an unavailable agent never produces a simulated answer.</p>
          {runs.slice(0, 3).map(run => <article key={run.run_id} className="border rounded-lg p-4 flex flex-col gap-2">
            <p className="text-xs uppercase font-semibold">{run.status} {run.result.model ? `· ${run.result.model}` : ''}</p>
            {run.status === 'running' && canWrite && <button className="text-sm text-error text-left" onClick={() => void action(() => api.post(`${base}/agent-runs/${run.run_id}/cancel`))}>Cancel further model calls</button>}
            <p className="text-sm whitespace-pre-wrap">{run.result.answer ?? run.result.error ?? 'Reading graph context…'}</p>
            {run.result.uncertainties?.map((u, i) => <p key={i} className="text-sm text-on-surface-variant">{u}</p>)}
            {run.result.citations?.map(c => <button key={c.assertion_id} onClick={() => setSource(c)} className="text-sm text-primary underline text-left">{c.document_label} · page {c.page} · {c.raw_value}</button>)}
            {run.result.tool_events?.length ? <details className="text-xs"><summary>Graph tool activity</summary><ol className="list-decimal pl-5 mt-2">{run.result.tool_events.map((t, i) => <li key={i}>{t.tool}</li>)}</ol></details> : null}
            {run.result.usage && <p className="text-xs text-outline">Tokens: {run.result.usage.input_tokens} in / {run.result.usage.output_tokens} out · estimated ${run.result.usage.estimated_usd.toFixed(5)}</p>}
          </article>)}
        </section>
        <section className="p-5 bg-surface-container-lowest rounded-xl border border-outline-variant/30 flex flex-col gap-4">
          <h2 className="text-lg font-bold">Review the source evidence</h2>
          <label className="text-sm">Field<select value={fieldId} onChange={e => setFieldId(e.target.value)} disabled={!synced || !fields.length} aria-busy={fieldsLoading} className="block w-full border p-3 rounded-lg mt-2">{!fields.length && <option value="">{!synced ? 'Waiting for graph synchronization…' : fieldsLoading ? 'Loading review fields…' : 'No review fields available'}</option>}{fields.map(f => <option key={f.canonical_field_id} value={f.canonical_field_id}>{f.label} · {f.status}</option>)}</select></label>
          {field && <p className="text-sm">Proposed field value: <strong>{field.consensus_value} {field.unit}</strong>. Verify the source before approving.</p>}
          <button onClick={() => { const index = fields.findIndex(f => f.canonical_field_id === fieldId); const next = [...fields.slice(index + 1), ...fields.slice(0, index + 1)].find(f => !['resolved', 'match'].includes(f.status)); if (next) setFieldId(next.canonical_field_id); }} className="text-sm text-primary underline self-start">Next unresolved field</button>
          {evidence.map(e => <div key={e.assertion_id} className="border rounded-lg p-3 flex flex-col gap-2">
            <button onClick={() => setSource(e)} className="text-left text-primary underline text-sm">{e.document_label} · page {e.page} · {e.raw_value}</button>
            <p className="text-xs text-on-surface-variant">Normalized: {e.normalized_value} {e.unit} · {e.confidence_status ?? 'confidence not measured'}</p>
            {e.warnings?.map(w => <p key={w} className="text-xs text-on-surface-variant">{w}</p>)}
            {canWrite && pending.filter(t => t.evidence_ids.includes(e.assertion_id)).map(t => <div key={t.id} className="flex gap-3"><button disabled={busy || !synced || !reason.trim()} onClick={() => void approve(t, e)} className="text-sm font-semibold text-primary disabled:opacity-40">Approve this source</button><button disabled={busy || !synced || !reason.trim()} onClick={() => void approve(t, e, true)} className="text-sm text-error disabled:opacity-40">Reject task</button></div>)}
          </div>)}
          <label className="text-sm">Review reason<textarea value={reason} onChange={e => setReason(e.target.value)} maxLength={1000} rows={2} className="w-full block p-3 border rounded-lg mt-2" placeholder="What did you verify, and why?" /></label>
          <p role="status" className="text-xs text-outline">{draftStatus}</p>
          {canWrite && <button disabled={busy || !synced || !evidence.length || !reason.trim()} onClick={() => void propose()} className="border border-primary text-primary rounded-lg p-3 text-sm disabled:opacity-40">Create review task from this evidence</button>}
          {pending.map(t => <p key={t.id} className="text-sm rounded-lg bg-primary-fixed/20 p-3">Pending task: {t.reason}</p>)}
        </section>
      </div>
      {context && <ChangeImpactPanel key={`${shipmentId}:${context.source_revision}:${context.graph_revision}`} shipmentId={shipmentId} documents={context.documents} revision={context.graph_revision} synced={synced} />}
      {context && <DossierControls id={shipmentId} revision={context.source_revision} title={context.title} documents={context.documents} archived={context.archived_documents ?? []} writable={canWrite} synced={synced} onSaved={refresh} />}
      {source && <section className="p-4 bg-surface-container-lowest rounded-xl"><div className="flex justify-between gap-4 mb-3"><h2 className="font-semibold">{source.document_label} · page {source.page}</h2><button className="text-primary" onClick={() => setSource(null)}>Close source</button></div><iframe title={`${source.document_label} page ${source.page}`} src={`${api.defaults.baseURL}/documents/${source.document_id}/content#page=${source.page}`} className="w-full h-[550px] border rounded-lg" /><p className="text-xs text-outline mt-2">Source page shown. A bounding-box highlight is available only when a measured location exists.</p></section>}
      <section className="p-5 bg-surface-container-lowest border rounded-xl flex flex-col gap-3">
        <h2 className="font-bold text-lg">Change a source, trace the consequences</h2>
        <p className="text-sm text-on-surface-variant">Approvals retain their history. The graph marks dependent decisions stale and preserves unrelated decisions. Previously downloaded files cannot be revoked.</p>
        {canWrite && context?.documents.some(d => d.fixture && d.document_type === 'packing_list') && <button disabled={!synced || busy} onClick={() => void action(() => api.post(`${base}/demo-correction`, null, { params: { expected_revision: context?.source_revision } }))} className="text-left text-primary font-semibold disabled:opacity-40">Apply synthetic packing-list correction to 440 kg</button>}
        {context?.decisions.map(d => <div key={d.id} className={`p-3 rounded-lg border ${d.validity_state === 'stale' ? 'border-error/40 bg-error/5' : ''}`}><p className="font-semibold text-sm">{d.field_id.split(':').at(-1)}: {d.value} · {d.status} · {d.validity_state}</p><p className="text-sm mt-1">{d.reason}</p></div>)}
      </section>
    </>}
  </div>;
}
