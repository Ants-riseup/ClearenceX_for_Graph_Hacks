import { useState } from 'react';
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
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setError('');
    try { await login(email, password); onTriggerToast({ title: 'Signed in', message: 'Your private workspace is ready.' }); navigate('/', { replace: true }); }
    catch (err) { setError(apiError(err, 'Sign-in failed. Check your credentials and API connection.')); }
    finally { setBusy(false); }
  };
  return <main className="max-w-md w-full mx-auto my-16 p-8 rounded-xl bg-surface-container-lowest shadow-sm border border-outline-variant/30">
    <p className="text-primary text-xs uppercase tracking-widest mb-2">ClearanceX Context Agent</p>
    <h1 className="text-2xl font-bold">Sign in to your workspace</h1>
    <p className="text-sm text-on-surface-variant my-4">Use the account created by your workspace administrator.</p>
    <form onSubmit={submit} className="flex flex-col gap-4">
      <label className="text-sm">Email<input autoComplete="username" type="email" required value={email} onChange={e => setEmail(e.target.value)} className="block w-full p-3 border rounded-lg mt-1" /></label>
      <label className="text-sm">Password<input autoComplete="current-password" type="password" required value={password} onChange={e => setPassword(e.target.value)} className="block w-full p-3 border rounded-lg mt-1" /></label>
      {error && <p role="alert" className="text-error text-sm">{error}</p>}
      <button disabled={busy} className="bg-primary text-white p-3 rounded-lg font-semibold disabled:opacity-50">{busy ? 'Signing in…' : 'Sign in'}</button>
    </form>
    <p className="mt-5 text-sm"><Link to="/auth/recovery" className="text-primary underline">Need access?</Link></p>
  </main>;
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
    <p className="my-4 text-sm">Public registration and email recovery are not enabled. Ask your administrator to create or restore your account using the local administration instructions.</p>
    <Link to="/auth/signin" className="text-primary underline">Return to sign in</Link>
  </section>;
}
