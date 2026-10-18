import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { api, apiError } from '../../utils/api';
import { Modal } from '../layout/Modal';

interface Customer { id: string; name: string; contact_name: string; status: 'active' | 'suspended' | 'removed'; version: number; shipment_count: number; users: { id: string; email: string; enabled: boolean; requires_password_change?: boolean }[] }
interface CustomerEvent { id: string; action: string; created_at: number; company_name?: string }
interface Summary { total: number; active: number; suspended: number; removed: number }
type Action = (path: string, body: Record<string, unknown>, target?: string) => Promise<void>;
interface PendingAction { path: string; body: Record<string, unknown>; target: string; label: string }

function CustomerCard({ customer, busy, apply }: { customer: Customer; busy: boolean; apply: Action }) {
  const [name, setName] = useState(customer.name);
  const [contact, setContact] = useState(customer.contact_name);
  const prefix = `/platform/companies/${customer.id}`;
  return <article className="rounded-2xl border border-outline-variant/30 bg-surface-container-lowest p-5 space-y-4 shadow-sm">
    <div className="flex flex-wrap justify-between gap-2"><div><h3 className="text-lg font-semibold break-words">{customer.name}</h3><p className="text-sm text-on-surface-variant">{customer.users.length} customer users · {customer.shipment_count} shipments</p></div><span className={`rounded-full px-3 py-1 text-xs font-semibold self-start ${customer.status === 'active' ? 'bg-emerald-50 text-emerald-800' : customer.status === 'suspended' ? 'bg-amber-50 text-amber-900' : 'bg-red-50 text-red-800'}`}>{customer.status === 'removed' ? 'Access removed' : customer.status === 'active' ? 'Active' : 'Disabled'}</span></div>
    {customer.users.map(user => <div key={user.id} className="flex flex-wrap justify-between gap-3 rounded-lg bg-surface-container-low p-3"><div><p className="font-medium break-all">{user.email}</p><p className="text-xs text-on-surface-variant">{customer.status === 'active' && user.enabled ? user.requires_password_change ? 'First sign-in: password change required' : 'Can sign in and process shipments' : 'Sign-in blocked'}</p></div><button disabled={busy} onClick={() => void apply(`${prefix}/users/${user.id}/reset-password`, { expected_version: customer.version }, user.email)} className="text-primary text-sm underline disabled:opacity-40">Reset password for {user.email}</button></div>)}
    {!customer.users.length && <p className="text-sm text-on-surface-variant">No customer login assigned.</p>}
    <details><summary className="cursor-pointer text-sm text-primary">Edit company details for {customer.name}</summary><div className="mt-3 flex flex-wrap gap-3 items-end"><label className="text-sm flex-1">Company name for {customer.name}<input maxLength={200} value={name} onChange={e => setName(e.target.value)} className="block w-full border rounded-lg p-2 mt-1" /></label><label className="text-sm flex-1">Contact name for {customer.name}<input maxLength={120} value={contact} onChange={e => setContact(e.target.value)} className="block w-full border rounded-lg p-2 mt-1" /></label><button disabled={busy || !name.trim()} onClick={() => void apply(`${prefix}/profile`, { name, contact_name: contact, expected_version: customer.version })} className="border rounded-lg px-3 py-2 disabled:opacity-40">Save details for {customer.name}</button></div></details>
    <div className="flex flex-wrap gap-4 text-sm">
      {customer.status === 'active' ? <button disabled={busy} onClick={() => void apply(`${prefix}/status`, { status: 'suspended', expected_version: customer.version }, customer.name)} className="text-primary underline disabled:opacity-40">Disable access for {customer.name}</button> : <button disabled={busy} onClick={() => void apply(`${prefix}/status`, { status: 'active', expected_version: customer.version }, customer.name)} className="text-primary underline disabled:opacity-40">Restore access for {customer.name}</button>}
      {customer.status !== 'removed' && <button disabled={busy} onClick={() => void apply(`${prefix}/status`, { status: 'removed', expected_version: customer.version }, customer.name)} className="text-error underline disabled:opacity-40">Remove access for {customer.name}</button>}
    </div>
  </article>;
}

export function ScreenAdminDashboard() {
  const { user } = useAuth();
  if (user?.role !== 'platform_admin') return <section className="p-8"><h1 className="text-2xl font-bold">Admin dashboard</h1><p role="alert">ClearanceX administrator access is required.</p></section>;
  return <CustomerAdministration />;
}

function CustomerAdministration() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [events, setEvents] = useState<CustomerEvent[]>([]);
  const [summary, setSummary] = useState<Summary>({ total: 0, active: 0, suspended: 0, removed: 0 });
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [query, setQuery] = useState('');
  const [search, setSearch] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [status, setStatus] = useState('active');
  const [loadError, setLoadError] = useState('');
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);
  const submitting = useRef(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [contact, setContact] = useState('');
  const [secret, setSecret] = useState<{ email: string; password: string } | null>(null);
  const [reveal, setReveal] = useState(false);
  const [copyStatus, setCopyStatus] = useState('');
  const load = useCallback(async (signal?: AbortSignal) => {
    const [result, history] = await Promise.all([
      api.get<{ companies: Customer[]; total: number; summary: Summary }>('/platform/companies', { params: { search, offset, limit: 20, status }, signal }),
      api.get<{ events: CustomerEvent[] }>('/platform/events', { signal }),
    ]);
    return { result, history };
  }, [search, offset, status]);
  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal).then(({ result, history }) => {
      if (controller.signal.aborted) return;
      setCustomers(result.data.companies); setTotal(result.data.total); setSummary(result.data.summary); setEvents(history.data.events);
    }).catch(err => { if (!controller.signal.aborted) setLoadError(apiError(err)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [load, refresh]);
  const apply: Action = async (path, body, target) => {
    setAdminPassword(''); setError('');
    setPendingAction({ path, body, target: target ?? String(body.email ?? body.name ?? 'this customer'),
      label: path === '/platform/companies' ? 'Add user' : path.endsWith('reset-password') ? 'Reset password' : path.endsWith('profile') ? 'Save details' : body.status === 'active' ? 'Restore access' : body.status === 'removed' ? 'Remove access' : 'Disable access' });
  };
  const confirm = async () => {
    if (!pendingAction || !adminPassword || submitting.current) return;
    submitting.current = true;
    setBusy(true); setError(''); setNotice(''); setSecret(null); setReveal(false); setCopyStatus('');
    try {
      const { path, body } = pendingAction;
      const { data } = await api.post(path, { ...body, admin_password: adminPassword });
      if (data.initial_password) setSecret({ email: data.email, password: data.initial_password });
      if (path === '/platform/companies') { setName(''); setEmail(''); setPassword(''); setContact(''); setQuery(String(body.email)); setSearch(String(body.email)); setOffset(0); setStatus('active'); setNotice('Customer user added. Share the login details privately so they can sign in and process shipments.'); }
      else setNotice('Customer access updated. Shipment records and history are preserved.');
      setPendingAction(null); setLoading(true); setLoadError(''); setRefresh(value => value + 1);
    } catch (err) { setError(apiError(err)); }
    finally { setAdminPassword(''); setBusy(false); submitting.current = false; }
  };
  const closeAction = () => { if (!busy) { setPendingAction(null); setAdminPassword(''); setError(''); } };
  return <section className="max-w-6xl w-full mx-auto p-5 sm:p-8 space-y-6">
    <header className="rounded-2xl bg-[#0d1b3e] p-6 sm:p-8 text-white"><p className="text-xs uppercase tracking-widest text-[#a8c9fa] font-semibold">ClearanceX administration</p><h1 className="text-3xl font-bold mt-3">Your customers. One clear view.</h1><p className="mt-3 text-white/75 max-w-2xl">Add customer users, share their login details and manage access. Each company gets its own shipment workspace.</p><p className="mt-5 text-xs text-white/60">Admin dashboard · Public signup restricted</p></header>
    <div className="grid sm:grid-cols-3 gap-4">{[['Customer companies', summary.total], ['Active', summary.active], ['Access disabled', summary.suspended + summary.removed]].map(([label, value]) => <div key={label} className="rounded-xl border bg-surface-container-lowest p-5"><p className="text-sm text-on-surface-variant">{label}</p><p className="text-3xl font-bold mt-2">{value}</p></div>)}</div>
    {error && !pendingAction && <p role="alert" className="border border-error/30 rounded-xl p-4 text-error">{error}</p>}{notice && <p role="status" className="bg-secondary-container/20 rounded-xl p-4">{notice}</p>}
    {secret && <section role="status" className="border border-primary/40 rounded-xl bg-primary-fixed/20 p-5 space-y-3"><h2 className="font-semibold">Login details for {secret.email}</h2><p className="text-sm">Share these temporary login details privately. The customer must choose a new password on first sign-in. No email has been sent.</p><input aria-label="Customer login password" readOnly type={reveal ? 'text' : 'password'} value={secret.password} className="block w-full max-w-lg border rounded-lg p-3 font-mono" /><div className="flex flex-wrap gap-4 text-sm"><button onClick={() => setReveal(v => !v)} className="underline">{reveal ? 'Hide password' : 'Show password'}</button><button onClick={() => { void navigator.clipboard?.writeText(`ClearanceX sign in: ${window.location.origin}/auth/signin\nEmail: ${secret.email}\nPassword: ${secret.password}`).then(() => setCopyStatus('Login details copied. Share privately.')).catch(() => setCopyStatus('Copy unavailable. Use Show password to copy the login details manually.')); if (!navigator.clipboard) setCopyStatus('Copy unavailable. Use Show password to copy the login details manually.'); }} className="underline">Copy login details</button><button onClick={() => { setSecret(null); setReveal(false); setCopyStatus(''); }} className="underline">Dismiss login details</button></div>{copyStatus && <p className="text-sm">{copyStatus}</p>}</section>}
    <form onSubmit={e => { e.preventDefault(); void apply('/platform/companies', { name, email, contact_name: contact, ...(password ? { password } : {}) }); }} className="rounded-2xl border bg-surface-container-lowest p-5 space-y-4"><h2 className="text-xl font-semibold">Add customer user</h2><div className="grid sm:grid-cols-2 gap-4">
      <label className="text-sm">Company name<input required maxLength={200} value={name} onChange={e => setName(e.target.value)} className="block w-full border rounded-lg p-3 mt-1" /></label>
      <label className="text-sm">Customer email<input required type="email" autoComplete="off" maxLength={254} value={email} onChange={e => setEmail(e.target.value)} className="block w-full border rounded-lg p-3 mt-1" /></label>
      <label className="text-sm">Contact name (optional)<input maxLength={120} value={contact} onChange={e => setContact(e.target.value)} className="block w-full border rounded-lg p-3 mt-1" /></label>
      <label className="text-sm">Customer password (optional)<input type="password" autoComplete="new-password" minLength={8} maxLength={128} value={password} onChange={e => setPassword(e.target.value)} className="block w-full border rounded-lg p-3 mt-1" /><span className="block mt-1 text-xs text-on-surface-variant">Leave blank to generate a password.</span></label>
    </div><p className="text-sm text-on-surface-variant">Each new customer gets a private company workspace and the full shipment workflow. You’ll confirm with your admin password before saving.</p><button disabled={busy} className="rounded-lg bg-primary text-white px-5 py-3 disabled:opacity-40">{busy ? 'Saving…' : 'Add user'}</button></form>
    <section className="space-y-4"><div className="flex flex-wrap justify-between gap-3 items-end"><h2 className="text-xl font-semibold">Customer users</h2><form onSubmit={e => { e.preventDefault(); setLoading(true); setLoadError(''); setOffset(0); setSearch(query); setRefresh(v => v + 1); }} className="flex flex-wrap gap-2"><label className="text-sm">Customer status<select disabled={busy} value={status} onChange={e => { setStatus(e.target.value); setOffset(0); setLoading(true); setLoadError(''); }} className="block border rounded-lg p-2 mt-1"><option value="active">Active</option><option value="all">All customers</option><option value="suspended">Disabled</option><option value="removed">Access removed</option></select></label><label className="text-sm">Search company or email<input maxLength={100} value={query} onChange={e => setQuery(e.target.value)} className="block border rounded-lg p-2 mt-1" /></label><button disabled={busy} className="border rounded-lg p-2 self-end">Search / refresh</button></form></div>
      {loading ? <p role="status">Loading customers…</p> : loadError ? <div role="alert" className="border border-error/30 rounded-xl p-5"><p>{loadError}</p><button onClick={() => { setLoadError(''); setLoading(true); setRefresh(v => v + 1); }} className="mt-3 underline text-primary">Retry customer list</button></div> : <>{customers.map(customer => <CustomerCard key={`${customer.id}:${customer.version}`} customer={customer} busy={busy} apply={apply} />)}{!customers.length && <div className="rounded-xl border border-dashed p-8 text-center"><h3 className="font-semibold">{summary.total ? 'No customers match these filters' : 'Your first customer starts here'}</h3><p className="text-sm mt-2 text-on-surface-variant">{summary.total ? 'Try another email, company name or status.' : 'Add a company and user above, then share their private login details.'}</p></div>}<div className="flex items-center gap-4"><button disabled={busy || offset === 0} onClick={() => { setLoading(true); setOffset(v => Math.max(0, v - 20)); }} className="border rounded-lg p-2 disabled:opacity-40">Previous customers</button><span className="text-sm">{total ? offset + 1 : 0}–{Math.min(offset + customers.length, total)} of {total}</span><button disabled={busy || offset + customers.length >= total} onClick={() => { setLoading(true); setOffset(v => v + 20); }} className="border rounded-lg p-2 disabled:opacity-40">Next customers</button></div></>}
    </section>
    <section className="rounded-xl border p-5 space-y-3"><h2 className="font-semibold">Recent administration activity</h2>{events.length ? <ul className="text-sm space-y-2">{events.map(item => <li key={item.id}><time dateTime={new Date(item.created_at * 1000).toISOString()}>{new Date(item.created_at * 1000).toLocaleString()}</time> · {item.company_name && <strong>{item.company_name} · </strong>}{item.action.replaceAll('_', ' ')}</li>)}</ul> : <p className="text-sm">No customer changes recorded yet.</p>}</section>
    {pendingAction && <Modal title={`${pendingAction.label}: ${pendingAction.target}`} description={pendingAction.path.endsWith('reset-password') ? 'The previous password will stop working and existing sessions will be signed out. Share the new password privately.' : pendingAction.path.endsWith('/status') ? 'This changes the company’s sign-in access. Existing sessions will be signed out; shipment records and history are preserved.' : 'Confirm this customer change with your administrator password.'} busy={busy} onClose={closeAction}><form onSubmit={event => { event.preventDefault(); void confirm(); }} className="space-y-4"><label className="block text-sm">Your admin password<input required readOnly={busy} type="password" autoComplete="current-password" maxLength={512} value={adminPassword} onChange={event => setAdminPassword(event.target.value)} className="block border rounded-lg p-3 mt-2 w-full" /></label>{error && <p role="alert" className="text-error text-sm">{error}</p>}<div className="flex flex-wrap justify-end gap-3"><button type="button" disabled={busy} onClick={closeAction} className="rounded-lg border px-4 py-3">Cancel</button><button disabled={busy || !adminPassword} className="rounded-lg bg-primary px-4 py-3 text-white disabled:opacity-40">{busy ? 'Saving…' : `Confirm ${pendingAction.label.toLowerCase()}`}</button></div></form></Modal>}
  </section>;
}
