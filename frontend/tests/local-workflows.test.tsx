import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { ScreenDossiers } from '../src/components/screens/ScreenDossiers';
import { ScreenTariffDirectory } from '../src/components/screens/ScreenTariffDirectory';
import { ScreenAuditTrail } from '../src/components/screens/ScreenAuditTrail';
import { ScreenBatchFiling } from '../src/components/screens/ScreenBatchFiling';

const mocks = vi.hoisted(() => ({
  get: vi.fn(), post: vi.fn(), upload: vi.fn(), audit: vi.fn(), list: vi.fn(),
  setShipment: vi.fn(), shipment: { id: null as string | null },
}));
vi.mock('../src/hooks/useShipment', () => ({ useShipment: () => ({ shipmentId: mocks.shipment.id, setShipmentId: mocks.setShipment }) }));
vi.mock('../src/hooks/useAuth', () => ({ useAuth: () => ({ user: { role: 'reviewer' } }) }));
vi.mock('../src/utils/api', () => ({
  api: { get: mocks.get, post: mocks.post }, uploadShipment: mocks.upload,
  getAuditTrail: mocks.audit, listDossiers: mocks.list,
  apiError: (e: Error) => e.message, downloadBlob: vi.fn(),
}));

beforeEach(() => {
  vi.clearAllMocks(); mocks.shipment.id = null;
});

describe('Upload controls', () => {
  function showUpload() {
    return render(<MemoryRouter><ScreenDossiers onTriggerToast={vi.fn()} /></MemoryRouter>);
  }

  it('opens the file input from the upload action when no file is selected, without submitting an empty request', async () => {
    showUpload();
    const input = screen.getByLabelText('1. Choose PDFs') as HTMLInputElement;
    const picker = vi.spyOn(input, 'click');
    await userEvent.click(screen.getByRole('button', { name: 'Upload and extract' }));
    expect(picker).toHaveBeenCalledOnce();
    expect(mocks.upload).not.toHaveBeenCalled();
  });

  it('uploads four selected PDFs, renders saved processing results and clears the input for reuse', async () => {
    const names = ['Air Waybill.pdf', 'Commercial Invoice (1).pdf', 'Customs Declaration Entry Worksheet.pdf', 'Export Packing List.pdf'];
    mocks.upload.mockResolvedValue({ shipment_id: 'qa-dossier' });
    mocks.get.mockResolvedValue({ data: { status: 'done', completed_documents: 4, total_documents: 4,
      documents: names.map((name, i) => ({ document_id: String(i), original_name: name, status: 'done', quality_status: 'extracted' })) } });
    showUpload();
    const input = screen.getByLabelText('1. Choose PDFs') as HTMLInputElement;
    const files = names.map(name => new File(['%PDF-test'], name, { type: 'application/pdf' }));
    await userEvent.upload(input, files);
    expect(screen.getByText(/4 PDFs selected/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Upload and extract' }));
    await screen.findByText(/Extraction saved —/);
    expect(mocks.upload.mock.calls[0][0]).toEqual(files);
    expect(mocks.setShipment).toHaveBeenCalledWith('qa-dossier');
    expect(screen.getByText(/4 of 4 documents processed/)).toBeInTheDocument();
    expect(input.files).toHaveLength(0);
    await userEvent.upload(input, files);
    expect(screen.getByText(/4 PDFs selected/)).toBeInTheDocument();
  });

  it('rejects a non-PDF drop and prevents an earlier selection from being submitted instead', async () => {
    const { container } = showUpload();
    const input = screen.getByLabelText('1. Choose PDFs') as HTMLInputElement;
    await userEvent.upload(input, new File(['%PDF-test'], 'valid.pdf', { type: 'application/pdf' }));
    const dropTarget = container.querySelector('[class*="border-dashed"]')!;
    fireEvent.drop(dropTarget, { dataTransfer: { files: [new File(['text'], 'invalid.txt')] } });
    expect(screen.getByRole('alert')).toHaveTextContent('Only PDF files are accepted.');
    await userEvent.click(screen.getByRole('button', { name: 'Upload and extract' }));
    expect(mocks.upload).not.toHaveBeenCalled();
  });

  it('rejects more than ten files before submitting', () => {
    showUpload();
    fireEvent.change(screen.getByLabelText('1. Choose PDFs'), { target: { files: Array.from({ length: 11 }, (_, i) => new File(['pdf'], `${i}.pdf`)) } });
    expect(screen.getByRole('alert')).toHaveTextContent('Choose 1–10 PDFs');
    expect(mocks.upload).not.toHaveBeenCalled();
  });

  it('shows an upload failure and preserves the selected PDFs for retry', async () => {
    mocks.upload.mockRejectedValueOnce(new Error('Upload connection failed'));
    showUpload();
    await userEvent.upload(screen.getByLabelText('1. Choose PDFs'), new File(['pdf'], 'retry.pdf', { type: 'application/pdf' }));
    await userEvent.click(screen.getByRole('button', { name: 'Upload and extract' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Upload connection failed');
    expect(screen.getByText(/1 PDF selected/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Upload and extract' })).toBeEnabled();
  });
});

describe('Sample tariff interactions', () => {
  it('filters by sector and HS search, shows an empty result and loads a selected sample', async () => {
    render(<ScreenTariffDirectory onTriggerToast={vi.fn()} />);
    await userEvent.click(screen.getByRole('button', { name: 'Textiles', exact: true }));
    expect(screen.getAllByRole('button', { name: /Use sample HS/ })).toHaveLength(1);
    await userEvent.click(screen.getByRole('button', { name: 'Use sample HS 6006.22.00' }));
    expect(screen.getByLabelText('Target HS subheading')).toHaveValue('6006.22.00');
    await userEvent.type(screen.getByRole('textbox', { name: 'Search HS code or keyword' }), 'missing');
    expect(screen.getByText('No sample references match your search.')).toBeInTheDocument();
    await userEvent.clear(screen.getByRole('textbox', { name: 'Search HS code or keyword' }));
    await userEvent.type(screen.getByRole('textbox', { name: 'Search HS code or keyword' }), '6006');
    expect(screen.getAllByRole('button', { name: /Use sample HS/ })).toHaveLength(1);
  });

  it('calculates 910 kg net for 1,000 kg gross and four pallets and reports an illustrative result', async () => {
    const toast = vi.fn(); render(<ScreenTariffDirectory onTriggerToast={toast} />);
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Gross mass in kg' }), { target: { value: '1000' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Euro pallets' }), { target: { value: '4' } });
    expect(screen.getByText('910.00 KG')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /Check sample calculation/ }));
    expect(toast.mock.lastCall?.[0].message).toContain('Illustrative net mass: 910.00 kg');
  });

  it.each(['-1', '1.5', '1000'])('rejects invalid pallet count %s without claiming a valid result', value => {
    render(<ScreenTariffDirectory onTriggerToast={vi.fn()} />);
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Euro pallets' }), { target: { value } });
    expect(screen.getByRole('alert')).toHaveTextContent('whole pallet count');
    expect(screen.getByRole('button', { name: /Check sample calculation/ })).toBeDisabled();
    expect(screen.getByText('Invalid inputs')).toBeInTheDocument();
  });
});

describe('Audit refresh', () => {
  it('fetches events again on refresh and displays the selected event details', async () => {
    mocks.shipment.id = 'qa-dossier';
    const entry = (action: string) => ({ module: 'context', action, timestamp: '2026-10-18T06:00:00+00:00', outcome: 'recorded', confidence: null });
    mocks.audit.mockResolvedValueOnce({ entries: [entry('upload_accepted')] })
      .mockResolvedValueOnce({ entries: [entry('upload_accepted'), entry('decision_approved')] });
    render(<ScreenAuditTrail onTriggerToast={vi.fn()} />);
    await screen.findByText('1 events');
    await userEvent.click(screen.getByRole('button', { name: /Refresh audit trail/ }));
    await screen.findByText('2 events');
    await userEvent.click(screen.getByRole('cell', { name: 'decision_approved' }));
    expect(screen.getAllByText('decision_approved')).toHaveLength(2);
    expect(mocks.audit).toHaveBeenCalledTimes(2);
  });
});

describe('Batch review messages', () => {
  it('shows readable blockers and disables download when no item was prepared', async () => {
    mocks.list.mockResolvedValue({ dossiers: [] });
    mocks.get.mockResolvedValue({ data: { batches: [{ batch_id: 'blocked-qa', status: 'blocked', items: [{ shipment_id: 'qa-dossier', status: 'blocked', detail: { readiness: { blockers: [{ message: 'Verify invoice value before export.' }], prepared_line_items: [{ secretImplementationField: true }] } } }] }] } });
    const { container } = render(<ScreenBatchFiling onTriggerToast={vi.fn()} />);
    await screen.findByText('Verify invoice value before export.');
    expect(container.textContent).not.toContain('secretImplementationField');
    expect(screen.getByRole('button', { name: /Download available prepared/ })).toBeDisabled();
  });
});
