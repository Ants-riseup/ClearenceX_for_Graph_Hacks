import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, apiError, uploadShipment } from '../../utils/api';
import { useShipment } from '../../hooks/useShipment';
interface Props { onTriggerToast: (t: { title: string; message: string; type?: 'error' | 'info' | 'success' }) => void }
interface Job { status: string; completed_documents: number; total_documents: number; documents: { document_id: string; original_name: string; status: string; error_message?: string; quality_status?: string; missing_fields?: string[] }[] }
function delay(signal: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    if (signal.aborted) { reject(new DOMException('Monitoring stopped', 'AbortError')); return; }
    const abort = () => { clearTimeout(timer); reject(new DOMException('Monitoring stopped', 'AbortError')); };
    const timer = window.setTimeout(() => { signal.removeEventListener('abort', abort); resolve(); }, 2000);
    signal.addEventListener('abort', abort, { once: true });
  });
}
export function ScreenDossiers({ onTriggerToast }: Props) {
  const { shipmentId, setShipmentId } = useShipment(); const navigate = useNavigate();
  const [files, setFiles] = useState<File[]>([]); const [job, setJob] = useState<Job | null>(null);
  const [busy, setBusy] = useState(false); const [stage, setStage] = useState('Ready to upload'); const [error, setError] = useState('');
  const controller = useRef<AbortController | null>(null);
  const fileInput = useRef<HTMLInputElement | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const monitor = async (id: string, signal: AbortSignal) => {
    const deadline = Date.now() + 10 * 60 * 1000; let failures = 0;
    while (!signal.aborted) {
      if (Date.now() > deadline) throw new Error('Monitoring timed out. The saved dossier continues on the server; resume monitoring below.');
      let data: Job;
      try { data = (await api.get<Job>(`/upload/${id}/status`, { signal })).data; failures = 0; }
      catch (err) { if (signal.aborted || ++failures >= 3) throw err; await delay(signal); continue; }
      if (signal.aborted) return;
      setJob(data); setStage(data.status === 'pending' ? 'Queued for extraction' : data.status === 'processing' ? 'Extracting documents' : data.status);
      if (['error', 'interrupted'].includes(data.status)) throw new Error('Processing needs attention. Review the document errors, then retry the saved dossier.');
      if (['done', 'completed'].includes(data.status)) { setStage('Extraction saved — check graph synchronization in Context Agent'); onTriggerToast({ title: 'Extraction saved', message: 'Human review and export readiness are separate steps.', type: 'success' }); return; }
      await delay(signal);
    }
  };
  const run = async (mode: 'upload' | 'resume' | 'retry') => {
    controller.current?.abort(); const current = new AbortController(); controller.current = current; setBusy(true); setError('');
    try {
      let id = shipmentId;
      if (mode === 'upload') {
        if (!files.length || files.length > 10 || files.some(f => f.size > 20 * 1024 ** 2) || files.reduce((n, f) => n + f.size, 0) > 80 * 1024 ** 2) throw new Error('Choose 1–10 PDFs, at most 20 MB each and 80 MB combined.');
        setStage('Uploading PDFs'); setJob(null); id = (await uploadShipment(files, current.signal)).shipment_id;
        if (current.signal.aborted) return; setShipmentId(id); setFiles([]);
        if (fileInput.current) fileInput.current.value = '';
      }
      if (!id) throw new Error('Select a saved dossier first.');
      if (mode === 'retry') await api.post(`/upload/${id}/retry`, {}, { signal: current.signal });
      await monitor(id, current.signal);
    } catch (err) { if (!current.signal.aborted) setError(apiError(err)); }
    finally { if (!current.signal.aborted) setBusy(false); }
  };
  const choose = (incoming: File[]) => {
    if (!incoming.length) return;
    const invalid = incoming.some(f => !f.name.toLowerCase().endsWith('.pdf')) ? 'Only PDF files are accepted.'
      : incoming.length > 10 || incoming.some(f => f.size > 20 * 1024 ** 2) || incoming.reduce((n, f) => n + f.size, 0) > 80 * 1024 ** 2
        ? 'Choose 1–10 PDFs, at most 20 MB each and 80 MB combined.' : '';
    setError(invalid); setFiles(invalid ? [] : incoming);
    if (invalid && fileInput.current) fileInput.current.value = '';
  };
  return <section className="max-w-5xl mx-auto w-full p-5 sm:p-8 space-y-6">
    <header><h1 className="text-2xl font-bold">Upload a dossier</h1><p className="text-sm mt-2 text-on-surface-variant">Extract document evidence, compare sources, then review the result. This prototype does not verify official customs schedules or file declarations.</p></header>
    {error && <p role="alert" className="border border-error/30 text-error p-4 rounded-xl">{error}</p>}
    <div onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); if (!busy) choose(Array.from(e.dataTransfer.files)); }} className="bg-surface-container-lowest border-2 border-dashed rounded-xl p-7 space-y-4">
      <label className="font-semibold block">1. Choose PDFs<input ref={fileInput} disabled={busy} type="file" multiple accept=".pdf,application/pdf" onChange={e => choose(Array.from(e.target.files ?? []))} className="block mt-3 w-full text-sm file:mr-3 file:rounded-lg file:border file:border-primary/30 file:bg-primary/10 file:px-4 file:py-2 file:text-primary file:font-semibold file:cursor-pointer" /></label>
      <p className="text-sm">1–10 files · 20 MB per file · 80 MB combined · up to 25 pages per file.</p>
      <p className="text-sm text-on-surface-variant">Digital PDFs are extracted locally without a paid service. Scanned PDFs require the optional OCR profile. Missing fields and goods rows remain subject to human review.</p>
      <ul className="text-sm space-y-2">{files.map((f, i) => <li key={`${f.name}-${i}`}>{f.name} · {(f.size / 1024 ** 2).toFixed(2)} MB</li>)}</ul>
      <p className="text-sm" aria-live="polite">{files.length ? `${files.length} PDF${files.length === 1 ? '' : 's'} selected. Click Upload and extract to start.` : 'Select PDFs first, or click Upload and extract to open the file picker.'}</p>
      <button disabled={busy} onClick={() => files.length ? void run('upload') : fileInput.current?.click()} className="bg-primary text-white p-3 rounded-lg disabled:opacity-40">{busy ? 'Processing…' : 'Upload and extract'}</button>
    </div>
    <div className="rounded-xl border p-5 space-y-4 bg-surface-container-lowest"><h2 className="font-semibold">Processing status</h2><p role="status" aria-live="polite">{stage}</p>
      {job && <><p className="text-sm">{job.completed_documents} of {job.total_documents} documents processed. Check extraction quality and review the sources before approval.</p><progress max={Math.max(1, job.total_documents)} value={job.completed_documents} className="w-full" /><ul className="text-sm space-y-2">{job.documents.map(d => <li key={d.document_id}><strong>{d.original_name}</strong> — {d.status}{d.quality_status && <span> · {d.quality_status === 'partial' ? 'Partial extraction — source review required' : 'Extracted — human review required'}</span>}{!!d.missing_fields?.length && <p>Missing: {d.missing_fields.join(', ')}</p>}{d.error_message && <p className="text-error">{d.error_message}</p>}</li>)}</ul></>}
      {shipmentId && <><p className="text-xs font-mono break-all">Saved dossier: {shipmentId}</p><div className="flex flex-wrap gap-3"><button disabled={busy} onClick={() => void run('resume')} className="border rounded-lg p-2 disabled:opacity-40">Resume monitoring</button><button disabled={busy || !job || !['error', 'interrupted'].includes(job.status)} onClick={() => void run('retry')} className="border rounded-lg p-2 disabled:opacity-40">Retry saved dossier</button><button onClick={() => navigate('/context-agent')} className="border rounded-lg p-2">Open Context Agent</button></div></>}
      {busy && <button onClick={() => { controller.current?.abort(); setBusy(false); setStage('Monitoring stopped — the saved server job continues'); }} className="underline text-sm">Stop monitoring</button>}
    </div>
  </section>;
}
