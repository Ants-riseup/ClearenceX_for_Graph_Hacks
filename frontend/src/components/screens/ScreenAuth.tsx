import { useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { apiError } from '../../utils/api';
interface Props { onTriggerToast: (t: { title: string; message: string }) => void }
export function ScreenSignIn({ onTriggerToast }: Props) {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const submitting = useRef(false);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); if (submitting.current) return; submitting.current = true; setBusy(true); setError('');
    try { const account = await login(email, password); onTriggerToast({ title: 'Signed in', message: account.requires_password_change ? 'Choose your own password to open your company workspace.' : 'Your private workspace is ready.' }); navigate(account.requires_password_change ? '/auth/change-password' : account.role === 'platform_admin' ? '/admin/companies' : '/', { replace: true }); }
    catch (err) { setError(apiError(err, 'Sign-in failed. Check your credentials and API connection.')); }
    finally { setBusy(false); submitting.current = false; }
  };
  return <section className="w-full min-h-[85dvh] grid lg:grid-cols-2">
    <div className="relative overflow-hidden bg-[#0d1b3e] text-white p-8 sm:p-12 lg:p-16 flex flex-col justify-between gap-12">
      <div aria-hidden="true" className="pointer-events-none absolute -right-32 -top-32 w-96 h-96 rounded-full border-[60px] border-[#5b8fd4]/10" />
      <Link to="/auth/signin" className="relative flex items-center gap-3 w-fit"><span aria-hidden="true" className="material-symbols-outlined rounded-xl bg-white/10 p-2 text-[#a8c9fa]">token</span><span className="text-xl font-semibold tracking-tight">Clearance<span className="text-[#7cabed]">X</span></span></Link>
      <div className="relative max-w-lg"><p className="text-xs uppercase tracking-[0.2em] text-[#a8c9fa] font-semibold">Built for export teams</p><h2 className="text-4xl sm:text-5xl font-semibold leading-tight tracking-tight mt-5">Clear evidence.<br />Confident next steps.</h2><p className="text-white/70 text-base leading-relaxed mt-6">Bring shipment documents together, review the differences and keep track of the evidence behind every decision.</p><ol className="mt-9 space-y-5 text-sm">{[['01', 'Upload your shipment PDFs'], ['02', 'Review connected source evidence'], ['03', 'Prepare your reviewed export']].map(([step, label]) => <li key={step} className="flex gap-4 items-center"><span className="w-9 h-9 rounded-full border border-white/20 grid place-items-center text-xs text-[#a8c9fa]">{step}</span>{label}</li>)}</ol></div>
      <p className="relative text-xs text-white/55">Your company’s documents stay in its own private workspace.</p>
    </div>
    <div className="grid place-items-center p-6 sm:p-12 bg-surface-container-lowest"><div className="w-full max-w-md py-8"><p className="text-sm text-primary font-semibold">Welcome back</p><h1 className="text-3xl sm:text-4xl font-bold tracking-tight mt-3">Sign in to ClearanceX</h1><p className="text-sm text-on-surface-variant mt-4 mb-8 leading-relaxed">Use the account provided by your ClearanceX administrator. You’ll arrive in the workspace assigned to you.</p>
      <form onSubmit={submit} className="flex flex-col gap-5" aria-busy={busy}>
        <label className="text-sm font-medium">Email<input disabled={busy} autoComplete="username" type="email" required maxLength={254} value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" className="block w-full p-3.5 border border-outline-variant rounded-xl mt-2" /></label>
        <div><label htmlFor="signin-password" className="text-sm font-medium">Password</label><div className="relative mt-2"><input id="signin-password" disabled={busy} autoComplete="current-password" type={showPassword ? 'text' : 'password'} required maxLength={512} value={password} onChange={e => setPassword(e.target.value)} className="block w-full p-3.5 pr-20 border border-outline-variant rounded-xl" /><button type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} aria-pressed={showPassword} onClick={() => setShowPassword(value => !value)} className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-primary px-1 py-2">{showPassword ? 'Hide' : 'Show'}</button></div></div>
        {error && <p role="alert" className="text-error text-sm rounded-xl bg-error/5 border border-error/20 p-3">{error}</p>}
        <button disabled={busy} className="bg-primary text-white p-3.5 rounded-xl font-semibold disabled:opacity-50 mt-1">{busy ? 'Signing in…' : 'Sign in'}</button>
      </form><div className="flex flex-wrap justify-between gap-3 mt-6 text-sm"><span className="text-on-surface-variant">Access is provided by invitation.</span><Link to="/auth/recovery" className="text-primary underline">Need access?</Link></div><p className="text-xs text-on-surface-variant border-t border-outline-variant/40 mt-8 pt-5 leading-relaxed">Human review remains part of the process. ClearanceX helps prepare documents; it does not submit declarations to customs.</p>
    </div></div>
  </section>;
}
export function ScreenChangePassword({ onTriggerToast }: Props) {
  const { user, updatePassword, logout } = useAuth();
  const navigate = useNavigate();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const submitting = useRef(false);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); if (submitting.current) return;
    setError('');
    if (next !== confirmation) { setError('Your new passwords do not match.'); return; }
    if (next === current) { setError('Choose a password different from your current password.'); return; }
    if (!next.trim()) { setError('Choose a password containing at least one non-space character.'); return; }
    submitting.current = true; setBusy(true);
    try { await updatePassword(current, next); setCurrent(''); setNext(''); setConfirmation(''); onTriggerToast({ title: 'Password updated', message: 'Your company workspace is ready. Previous sessions have been signed out.' }); navigate('/', { replace: true }); }
    catch (err) { setError(apiError(err)); }
    finally { submitting.current = false; setBusy(false); }
  };
  return <section className="w-full max-w-lg mx-auto my-10 sm:my-16 p-6 sm:p-8 rounded-2xl bg-surface-container-lowest border border-outline-variant/40 shadow-sm">
    <p className="text-xs font-semibold uppercase tracking-widest text-primary">ClearanceX · {user?.company_name ?? 'Company workspace'}</p><h1 className="text-3xl font-bold mt-4">{user?.requires_password_change ? 'Choose your own password' : 'Change your password'}</h1><p className="text-sm text-on-surface-variant leading-relaxed mt-4">{user?.requires_password_change ? 'You signed in with a password supplied by your administrator. Set a new password before processing shipments.' : 'Update the password for your customer account. Other signed-in sessions will be signed out.'}</p><p className="text-sm font-medium mt-3 break-all">{user?.email}</p>
    <form onSubmit={submit} className="space-y-5 mt-7" aria-busy={busy}>
      <label className="block text-sm font-medium">Current password<input disabled={busy} required maxLength={512} type="password" autoComplete="current-password" value={current} onChange={event => setCurrent(event.target.value)} className="block w-full border rounded-xl p-3 mt-2" /></label>
      <label className="block text-sm font-medium">New password<input disabled={busy} required minLength={10} maxLength={128} type="password" autoComplete="new-password" value={next} onChange={event => setNext(event.target.value)} aria-describedby="password-requirements" className="block w-full border rounded-xl p-3 mt-2" /></label><p id="password-requirements" className="text-xs text-on-surface-variant">Use 10–128 characters. A memorable phrase with several words works well.</p>
      <label className="block text-sm font-medium">Confirm new password<input disabled={busy} required minLength={10} maxLength={128} type="password" autoComplete="new-password" value={confirmation} onChange={event => setConfirmation(event.target.value)} className="block w-full border rounded-xl p-3 mt-2" /></label>
      {error && <p role="alert" className="text-error rounded-lg border border-error/20 p-3 text-sm">{error}</p>}
      <button disabled={busy} className="w-full rounded-xl bg-primary text-white p-3.5 font-semibold disabled:opacity-40">{busy ? 'Updating password…' : 'Save password and continue'}</button>
    </form><button disabled={busy} onClick={() => { setBusy(true); void logout().catch(err => setError(apiError(err))).finally(() => setBusy(false)); }} className="mt-5 underline text-sm text-primary">Sign out</button>
  </section>;
}
export function ScreenSignUp(_props: Props) {
  return <AccessHelp />;
}
export function ScreenRecovery(_props: Props) {
  return <AccessHelp />;
}
function AccessHelp() {
  return <section className="max-w-lg mx-auto my-16 p-8 rounded-xl bg-surface-container-lowest">
    <h1 className="text-xl font-bold">Workspace access</h1>
    <p className="my-4 text-sm">Your company’s access is provided by ClearanceX. Contact the administrator for a customer account or password reset. After receiving a temporary password, sign in and choose your own password.</p>
    <Link to="/auth/signin" className="text-primary underline">Return to sign in</Link>
  </section>;
}
