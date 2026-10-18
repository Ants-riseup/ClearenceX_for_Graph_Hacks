import { afterEach, expect, it, vi } from 'vitest';
import { act, render, screen } from '@testing-library/react';
import { ScreenContextAgent } from '../src/components/screens/ScreenContextAgent';

const mocks = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));
vi.mock('../src/utils/api', () => ({ api: { get: mocks.get, post: mocks.post }, apiError: (e: Error) => e.message }));
vi.mock('../src/hooks/useShipment', () => ({ useShipment: () => ({ shipmentId: 'slow-cloud-dossier', setShipmentId: vi.fn() }) }));
vi.mock('../src/hooks/useAuth', () => ({ useAuth: () => ({ user: { role: 'user' } }) }));
vi.mock('../src/components/review/DossierControls', () => ({ DossierControls: () => null }));
vi.mock('../src/components/review/ChangeImpactPanel', () => ({ ChangeImpactPanel: () => null }));
afterEach(() => { vi.useRealTimers(); vi.clearAllMocks(); });

it('allows a slow cloud field request to finish without overlapping polls discarding it', async () => {
  vi.useFakeTimers();
  let finishFields!: (result: unknown) => void;
  const delayed = new Promise(resolve => { finishFields = resolve; });
  mocks.get.mockImplementation((url: string) => {
    if (url.endsWith('/context-status')) return Promise.resolve({ data: { title: 'Demo', source_revision: 1, graph_revision: 1, status: 'synced', tasks: [], decisions: [], documents: [], archived_documents: [] } });
    if (url.endsWith('/agent-runs')) return Promise.resolve({ data: { runs: [] } });
    if (url.endsWith('/context-issues')) return delayed;
    if (url.endsWith('/context-evidence')) return Promise.resolve({ data: { evidence: [] } });
    return Promise.resolve({ data: {} });
  });
  mocks.post.mockResolvedValue({ data: {} });
  const view = render(<ScreenContextAgent />);
  await act(async () => { await vi.advanceTimersByTimeAsync(9000); });
  expect(mocks.get.mock.calls.filter(([url]) => url.endsWith('/context-issues'))).toHaveLength(1);
  await act(async () => { finishFields({ data: { fields: [{ canonical_field_id: 'weight', label: 'Gross weight', status: 'conflict', consensus_value: 450, unit: 'kg' }] } }); });
  expect(screen.getByRole('combobox', { name: 'Field' })).toHaveValue('weight');
  expect(screen.getByRole('option', { name: 'Gross weight · conflict' })).toBeInTheDocument();
  view.unmount();
});
