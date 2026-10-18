import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ScreenSignIn, ScreenChangePassword } from '../src/components/screens/ScreenAuth';
import { ChangeImpactPanel } from '../src/components/review/ChangeImpactPanel';
const mocks = vi.hoisted(() => ({ get: vi.fn(), login: vi.fn(), updatePassword: vi.fn(), logout: vi.fn() }));
vi.mock('../src/hooks/useAuth', () => ({ useAuth: () => ({ login: mocks.login, updatePassword: mocks.updatePassword, logout: mocks.logout, user: { email: 'customer@example.test', company_name: 'Acme Exports', requires_password_change: true } }) }));
vi.mock('../src/utils/api', () => ({ api: { get: mocks.get }, apiError: (err: Error) => err.message }));
beforeEach(() => vi.clearAllMocks());

describe('Customer sign in', () => {
  it('toggles password visibility without submitting the form', async () => {
    render(<MemoryRouter><ScreenSignIn onTriggerToast={vi.fn()} /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText('Password'), 'private-test-password');
    await userEvent.click(screen.getByRole('button', { name: 'Show password' }));
    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'text');
    expect(mocks.login).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button', { name: 'Hide password' }));
    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'password');
  });
  it('reports a login failure without claiming success or losing the email', async () => {
    mocks.login.mockRejectedValue(new Error('Email or password is incorrect.'));
    const toast = vi.fn(); render(<MemoryRouter><ScreenSignIn onTriggerToast={toast} /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText('Email'), 'customer@example.test');
    await userEvent.type(screen.getByLabelText('Password'), 'wrong-password');
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Email or password is incorrect');
    expect(screen.getByLabelText('Email')).toHaveValue('customer@example.test');
    expect(toast).not.toHaveBeenCalled(); expect(screen.getByRole('button', { name: 'Sign in' })).toBeEnabled();
  });
  it('routes temporary customer credentials directly to password setup', async () => {
    mocks.login.mockResolvedValue({ role: 'user', requires_password_change: true });
    render(<MemoryRouter initialEntries={['/auth/signin']}><Routes><Route path="/auth/signin" element={<ScreenSignIn onTriggerToast={vi.fn()} />} /><Route path="/auth/change-password" element={<p>Password setup screen</p>} /><Route path="/" element={<p>Shipment workspace</p>} /></Routes></MemoryRouter>);
    await userEvent.type(screen.getByLabelText('Email'), 'customer@example.test');
    await userEvent.type(screen.getByLabelText('Password'), 'temporary-password');
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));
    expect(await screen.findByText('Password setup screen')).toBeInTheDocument();
    expect(screen.queryByText('Shipment workspace')).not.toBeInTheDocument();
  });
});

describe('First sign-in password setup', () => {
  function show(toast = vi.fn()) {
    render(<MemoryRouter initialEntries={['/auth/change-password']}><Routes><Route path="/auth/change-password" element={<ScreenChangePassword onTriggerToast={toast} />} /><Route path="/" element={<p>Shipment workspace</p>} /></Routes></MemoryRouter>);
  }
  async function enter(confirmation: string, next = 'My private passphrase') {
    await userEvent.type(screen.getByLabelText('Current password'), 'temporary-password');
    await userEvent.type(screen.getByLabelText('New password'), next);
    await userEvent.type(screen.getByLabelText('Confirm new password'), confirmation);
    await userEvent.click(screen.getByRole('button', { name: 'Save password and continue' }));
  }
  it('rejects mismatched confirmation before contacting the server', async () => {
    show(); await enter('A different private passphrase');
    expect(screen.getByRole('alert')).toHaveTextContent('Your new passwords do not match');
    expect(mocks.updatePassword).not.toHaveBeenCalled();
  });
  it('changes the password before entering the shipment product', async () => {
    mocks.updatePassword.mockResolvedValue(undefined); const toast = vi.fn(); show(toast);
    await enter('My private passphrase');
    expect(await screen.findByText('Shipment workspace')).toBeInTheDocument();
    expect(mocks.updatePassword).toHaveBeenCalledWith('temporary-password', 'My private passphrase');
    expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: 'Password updated' }));
    expect(localStorage.length).toBe(0); expect(sessionStorage.length).toBe(0);
  });
  it('keeps password setup visible when the current password is rejected', async () => {
    mocks.updatePassword.mockRejectedValue(new Error('Your current password is incorrect.'));
    show(); await enter('My private passphrase');
    expect(await screen.findByRole('alert')).toHaveTextContent('Your current password is incorrect');
    expect(screen.queryByText('Shipment workspace')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Save password and continue' })).toBeEnabled();
  });
  it('accepts a ten-character password with matching form requirements', async () => {
    mocks.updatePassword.mockResolvedValue(undefined); show();
    expect(screen.getByLabelText('New password')).toHaveAttribute('minlength', '10');
    expect(screen.getByLabelText('Confirm new password')).toHaveAttribute('minlength', '10');
    await enter('Sample2004', 'Sample2004');
    expect(await screen.findByText('Shipment workspace')).toBeInTheDocument();
    expect(mocks.updatePassword).toHaveBeenCalledWith('temporary-password', 'Sample2004');
  });
});

describe('Graph change-impact preview', () => {
  function show(synced = true) {
    return render(<MemoryRouter><ChangeImpactPanel shipmentId="shipment" documents={[{ document_id: 'packing', source_filename: 'Packing list.pdf' }, { document_id: 'invoice', source_filename: 'Invoice.pdf' }]} revision={7} synced={synced} /></MemoryRouter>);
  }
  it('reads graph dependencies for the displayed revision without making a mutation', async () => {
    mocks.get.mockResolvedValue({ data: { impact: [{ id: 'decision-1', type: 'Decision', artifact: { field_id: 'shipment:field:GROSS_WEIGHT', value: '450', validity_state: 'current', reason: 'Checked the packing list.' } }] } });
    show(); await userEvent.click(screen.getByRole('button', { name: 'Preview source dependencies' }));
    expect(await screen.findByRole('status')).toHaveTextContent('1 connected record · graph revision 7');
    expect(screen.getByText('Reviewed value: 450')).toBeInTheDocument();
    expect(mocks.get).toHaveBeenCalledWith('/shipments/shipment/change-impact', expect.objectContaining({ params: { document_id: 'packing', expected_revision: 7 } }));
    await userEvent.selectOptions(screen.getByLabelText('Source document'), 'invoice');
    expect(screen.queryByText('Reviewed value: 450')).not.toBeInTheDocument();
  });
  it('shows a graph failure honestly and allows retry', async () => {
    mocks.get.mockRejectedValueOnce(new Error('Graph context is unavailable.')).mockResolvedValueOnce({ data: { impact: [] } });
    show(); await userEvent.click(screen.getByRole('button', { name: 'Preview source dependencies' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Graph context is unavailable');
    await userEvent.click(screen.getByRole('button', { name: 'Preview source dependencies' }));
    expect(await screen.findByText(/No dependent review records were found/)).toHaveTextContent('Other shipment readiness checks still apply');
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
  it('blocks preview when graph context is pending', () => {
    show(false);
    expect(screen.getByRole('button', { name: 'Preview source dependencies' })).toBeDisabled();
    expect(mocks.get).not.toHaveBeenCalled();
  });
});
