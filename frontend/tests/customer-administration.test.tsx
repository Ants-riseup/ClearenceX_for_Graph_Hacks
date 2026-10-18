import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ScreenAdminDashboard } from '../src/components/screens/ScreenAdminDashboard';
const mocks = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), role: 'platform_admin' }));
vi.mock('../src/hooks/useAuth', () => ({ useAuth: () => ({ user: { id: 'operator', role: mocks.role } }) }));
vi.mock('../src/utils/api', () => ({ api: { get: mocks.get, post: mocks.post }, apiError: (err: Error) => err.message }));
beforeEach(() => {
  vi.clearAllMocks(); mocks.role = 'platform_admin';
  mocks.get.mockImplementation(async (path: string) => ({ data: path.endsWith('events') ? { events: [] } : {
    companies: [{ id: 'company', name: 'Acme Exports', contact_name: 'Owner', status: 'active', version: 3, shipment_count: 2, users: [{ id: 'customer', email: 'customer@example.test', enabled: true }] }],
    total: 1, summary: { total: 1, active: 1, suspended: 0, removed: 0 },
  } }));
});
describe('ClearanceX operator dashboard', () => {
  it('denies customer users and legacy company admins before loading company data', () => {
    for (const role of ['user', 'admin']) {
      mocks.role = role;
      const result = render(<ScreenAdminDashboard />);
      expect(screen.getByRole('alert')).toHaveTextContent('ClearanceX administrator access is required');
      expect(mocks.get).not.toHaveBeenCalled(); result.unmount();
    }
  });
  it('adds a customer login with a private company workspace and displays masked login details', async () => {
    mocks.post.mockResolvedValue({ data: { email: 'new@example.test', initial_password: 'generated-test-only' } });
    render(<ScreenAdminDashboard />); await screen.findByText('customer@example.test');
    expect(screen.queryByLabelText('New account role')).not.toBeInTheDocument();
    await userEvent.type(screen.getByLabelText('Company name'), 'New Exporter');
    await userEvent.type(screen.getByLabelText('Customer email'), 'new@example.test');
    await userEvent.click(screen.getByRole('button', { name: 'Add user' }));
    expect(mocks.post).not.toHaveBeenCalled();
    const dialog = screen.getByRole('dialog');
    await userEvent.type(within(dialog).getByLabelText('Your admin password'), 'operator-confirmation');
    await userEvent.click(within(dialog).getByRole('button', { name: 'Confirm add user' }));
    await screen.findByRole('heading', { name: 'Login details for new@example.test' });
    expect(mocks.post).toHaveBeenCalledWith('/platform/companies', { name: 'New Exporter', email: 'new@example.test', contact_name: '', admin_password: 'operator-confirmation' });
    expect(screen.queryByLabelText('Your admin password')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Customer login password')).toHaveAttribute('type', 'password');
    expect(localStorage.length).toBe(0); expect(sessionStorage.length).toBe(0);
    await waitFor(() => expect(mocks.get).toHaveBeenCalledWith('/platform/companies', expect.objectContaining({ params: expect.objectContaining({ search: 'new@example.test', status: 'active', offset: 0 }) })));
    await userEvent.click(screen.getByRole('button', { name: 'Dismiss login details' }));
    expect(screen.queryByLabelText('Customer login password')).not.toBeInTheDocument();
  });
  it('disables customer access using the current version', async () => {
    mocks.post.mockResolvedValue({ data: {} });
    render(<ScreenAdminDashboard />); await screen.findByText('customer@example.test');
    await userEvent.click(screen.getByRole('button', { name: 'Disable access for Acme Exports' }));
    expect(mocks.post).not.toHaveBeenCalled();
    await userEvent.type(screen.getByLabelText('Your admin password'), 'operator-confirmation');
    await userEvent.click(screen.getByRole('button', { name: 'Confirm disable access' }));
    await screen.findByText('Customer access updated. Shipment records and history are preserved.');
    expect(mocks.post).toHaveBeenCalledWith('/platform/companies/company/status', { status: 'suspended', expected_version: 3, admin_password: 'operator-confirmation' });
  });
  it('shows stale failures and clears the admin confirmation password', async () => {
    mocks.post.mockRejectedValue(new Error('Customer changed. Refresh before applying this action.'));
    render(<ScreenAdminDashboard />); await screen.findByText('customer@example.test');
    await userEvent.click(screen.getByRole('button', { name: 'Reset password for customer@example.test' }));
    await userEvent.type(screen.getByLabelText('Your admin password'), 'operator-confirmation');
    await userEvent.click(screen.getByRole('button', { name: 'Confirm reset password' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Customer changed. Refresh');
    expect(screen.getByLabelText('Your admin password')).toHaveValue('');
  });
  it('cancels a removal without sending a request and restores keyboard focus', async () => {
    render(<ScreenAdminDashboard />); await screen.findByText('customer@example.test');
    const trigger = screen.getByRole('button', { name: 'Remove access for Acme Exports' });
    await userEvent.click(trigger);
    expect(screen.getByRole('dialog')).toHaveTextContent('Acme Exports');
    expect(screen.getByLabelText('Your admin password')).toHaveFocus();
    await userEvent.keyboard('{Shift>}{Tab}{/Shift}');
    expect(screen.getByRole('button', { name: 'Cancel' })).toHaveFocus();
    await userEvent.keyboard('{Escape}');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(mocks.post).not.toHaveBeenCalled(); expect(trigger).toHaveFocus();
  });
  it('retrieves the chosen customer status from the server', async () => {
    render(<ScreenAdminDashboard />); await screen.findByText('customer@example.test');
    await userEvent.selectOptions(screen.getByLabelText('Customer status'), 'suspended');
    await waitFor(() => expect(mocks.get).toHaveBeenCalledWith('/platform/companies', expect.objectContaining({ params: expect.objectContaining({ status: 'suspended', offset: 0 }) })));
  });
  it('retains newly generated credentials when refreshing the saved list fails', async () => {
    mocks.post.mockResolvedValue({ data: { email: 'new@example.test', initial_password: 'generated-test-only' } });
    render(<ScreenAdminDashboard />); await screen.findByText('customer@example.test');
    await userEvent.type(screen.getByLabelText('Company name'), 'New Exporter');
    await userEvent.type(screen.getByLabelText('Customer email'), 'new@example.test');
    await userEvent.click(screen.getByRole('button', { name: 'Add user' }));
    mocks.get.mockRejectedValue(new Error('List refresh unavailable'));
    await userEvent.type(screen.getByLabelText('Your admin password'), 'operator-confirmation');
    await userEvent.click(screen.getByRole('button', { name: 'Confirm add user' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('List refresh unavailable');
    expect(screen.getByLabelText('Customer login password')).toHaveValue('generated-test-only');
    expect(screen.getByRole('button', { name: 'Retry customer list' })).toBeEnabled();
  });
});
