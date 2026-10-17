import { useAuth } from '../../hooks/useAuth';
interface Props { onTriggerToast: (t: { title: string; message: string }) => void }
export function ScreenSettings(_props: Props) {
  const { user } = useAuth();
  return <section className="max-w-4xl mx-auto w-full p-8 flex flex-col gap-5">
    <h1 className="text-2xl font-bold">Workspace settings</h1>
    <div className="rounded-xl border p-5 bg-surface-container-lowest"><h2 className="font-semibold">Account</h2><p className="mt-2">{user?.email} · {user?.role}</p><p className="text-sm text-on-surface-variant mt-2">Sessions expire after 30 minutes idle or 8 hours total. Workspace administration uses the local admin command.</p></div>
    <div className="rounded-xl border p-5 bg-surface-container-lowest"><h2 className="font-semibold">Prototype comparison policy · comparison-v1</h2><p className="text-sm mt-2">Absolute numeric tolerance: 0.01 in compatible normalized units. Text comparison is conservative and role-aware. This policy is not an official customs regulation.</p><p className="text-sm text-on-surface-variant mt-2">Policy changes require a versioned server change and tests. Interactive tolerance editing is planned; there are no unsaved sliders.</p></div>
    <div className="rounded-xl border p-5 bg-surface-container-lowest"><h2 className="font-semibold">Human review</h2><p className="text-sm mt-2">The agent may propose a task. It cannot approve a value, file a declaration or silently reuse an approval after its source changes.</p></div>
  </section>;
}
