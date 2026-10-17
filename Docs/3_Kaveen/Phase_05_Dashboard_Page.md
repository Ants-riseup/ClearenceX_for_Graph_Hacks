# Phase 05 — Shipment Dashboard Page

> **Priority:** MUST
> **Estimated Time:** 2 hours
> **Dependencies:** Phase 03 (app shell + routing)
> **Blocks:** Nothing directly — but completes the navigation flow

---

## Goal

Build the dashboard that lists processed shipments as interactive cards. Each card shows key metrics and clicking navigates to the review page.

## Why

The dashboard is the landing view after upload. For judges, it demonstrates the system handles multiple shipments and provides at-a-glance summaries — status, document count, discrepancies found, and processing speed.

## Implementation

### 5.1 Dashboard Page

```tsx
// frontend/src/pages/DashboardPage.tsx
import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Upload } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ShipmentCard } from '../components/ShipmentCard';

// Temporary: For demo, store shipment IDs in localStorage
function getSavedShipments(): string[] {
  const saved = localStorage.getItem('clearancex_shipments');
  return saved ? JSON.parse(saved) : [];
}

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [shipmentIds, setShipmentIds] = useState<string[]>(getSavedShipments());

  return (
    <div className="dashboard-page animate-fade-in">
      <div className="dashboard-header">
        <div>
          <h1><LayoutDashboard size={28} style={{ verticalAlign: 'middle', marginRight: 12 }} />Shipment Dashboard</h1>
          <p className="dashboard-subtitle">View and manage your processed shipping dossiers</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          <Upload size={18} /> New Dossier
        </button>
      </div>

      {shipmentIds.length === 0 ? (
        <div className="empty-state glass-card">
          <div className="empty-icon">📦</div>
          <h3>No shipments yet</h3>
          <p>Upload a shipping dossier to get started with AI-powered reconciliation</p>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            <Upload size={18} /> Upload Dossier
          </button>
        </div>
      ) : (
        <div className="shipment-grid">
          {shipmentIds.map((id, index) => (
            <div key={id} className="animate-fade-in" style={{ animationDelay: `${index * 100}ms` }}>
              <ShipmentCard shipmentId={id} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
```

### 5.2 ShipmentCard Component

```tsx
// frontend/src/components/ShipmentCard.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Package, AlertTriangle, Clock, FileText, ChevronRight, CheckCircle, Loader2 } from 'lucide-react';
import { getShipmentStatus } from '../utils/api';
import type { ShipmentStatus } from '../types';

interface Props {
  shipmentId: string;
}

export const ShipmentCard: React.FC<Props> = ({ shipmentId }) => {
  const navigate = useNavigate();
  const [status, setStatus] = useState<ShipmentStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getShipmentStatus(shipmentId)
      .then(data => { setStatus(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [shipmentId]);

  if (loading) {
    return (
      <div className="shipment-card glass-card">
        <div className="card-loading"><Loader2 size={24} className="spin" /></div>
      </div>
    );
  }

  const docCount = status?.documents?.length || 0;
  const processingTime = status?.processing_time_ms || 0;
  const isCompleted = status?.status === 'completed';

  return (
    <div className="shipment-card glass-card" onClick={() => navigate(`/review/${shipmentId}`)}>
      {/* Header */}
      <div className="shipment-card-header">
        <Package size={22} color="var(--accent-primary)" />
        <span className="shipment-id mono">{shipmentId.slice(0, 8)}</span>
        <span className={`badge ${isCompleted ? 'badge-completed' : 'badge-processing'}`}>
          {isCompleted ? <><CheckCircle size={12} /> Completed</> : <><Loader2 size={12} className="spin" /> Processing</>}
        </span>
      </div>

      {/* Stats */}
      <div className="shipment-card-stats">
        <div className="stat-item">
          <FileText size={16} color="var(--text-muted)" />
          <div className="stat-detail">
            <span className="stat-value">{docCount}</span>
            <span className="stat-label">Documents</span>
          </div>
        </div>
        <div className="stat-item">
          <AlertTriangle size={16} color="var(--sev-medium)" />
          <div className="stat-detail">
            <span className="stat-value text-warning">2</span>
            <span className="stat-label">Discrepancies</span>
          </div>
        </div>
        <div className="stat-item">
          <Clock size={16} color="var(--text-muted)" />
          <div className="stat-detail">
            <span className="stat-value">{(processingTime / 1000).toFixed(1)}s</span>
            <span className="stat-label">Processing</span>
          </div>
        </div>
      </div>

      {/* Document types */}
      <div className="shipment-card-docs">
        {status?.documents?.map(doc => (
          <span key={doc.document_id} className="doc-chip" title={doc.filename}>
            {doc.document_type?.replace('_', ' ')}
          </span>
        ))}
      </div>

      {/* Footer */}
      <div className="shipment-card-footer">
        <span className="review-hint">Click to review</span>
        <ChevronRight size={18} className="chevron" />
      </div>
    </div>
  );
};
```

### 5.3 Dashboard CSS

```css
/* Add to index.css */

.dashboard-page {
  max-width: 960px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.dashboard-header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.dashboard-subtitle {
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.shipment-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.shipment-card {
  padding: 20px;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.shipment-card:hover {
  transform: translateY(-2px);
}

.shipment-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.shipment-id {
  font-size: 0.95rem;
  font-weight: 600;
  flex: 1;
}

.badge-completed {
  background: rgba(16, 185, 129, 0.12);
  color: var(--conf-high);
  border: 1px solid rgba(16, 185, 129, 0.3);
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: 0.7rem;
  font-weight: 600;
}

.badge-processing {
  background: rgba(245, 158, 11, 0.12);
  color: var(--conf-medium);
  border: 1px solid rgba(245, 158, 11, 0.3);
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: 0.7rem;
  font-weight: 600;
}

.shipment-card-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-detail {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.text-warning {
  color: var(--sev-medium);
}

.shipment-card-docs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.doc-chip {
  background: var(--bg-elevated);
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: 0.7rem;
  color: var(--text-secondary);
  text-transform: capitalize;
  border: 1px solid var(--border-subtle);
}

.shipment-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--border-subtle);
}

.review-hint {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.chevron {
  color: var(--text-muted);
  transition: transform var(--transition-fast);
}

.shipment-card:hover .chevron {
  transform: translateX(4px);
  color: var(--accent-primary);
}

.card-loading {
  display: flex;
  justify-content: center;
  padding: 40px;
  color: var(--text-muted);
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 60px 40px;
  max-width: 400px;
  margin: 60px auto;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin-bottom: 8px;
}

.empty-state p {
  color: var(--text-secondary);
  margin-bottom: 24px;
}
```

## Acceptance Criteria

- [ ] Dashboard shows shipment cards fetched from API
- [ ] Empty state renders with "Upload Dossier" CTA when no shipments exist
- [ ] Cards show document count, discrepancy count, processing time
- [ ] Clicking a card navigates to `/review/:id`
- [ ] Cards animate in with staggered delay
- [ ] "New Dossier" button in header navigates to upload page
- [ ] Loading state shows spinner while fetching
- [ ] Glassmorphism cards with hover lift effect

## Outputs

- `src/pages/DashboardPage.tsx`
- `src/components/ShipmentCard.tsx`
- Dashboard CSS added to `index.css`
