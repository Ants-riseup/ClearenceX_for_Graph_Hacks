# Phase 03 — Application Shell + Routing + Navigation

> **Priority:** MUST
> **Estimated Time:** 2 hours
> **Dependencies:** Phase 01 (React project setup)
> **Blocks:** All page-level phases (04, 05, 06)

---

## Goal

Build the application shell with a sidebar, top bar, React Router navigation, and page layout skeleton. Every subsequent page slots into this shell.

## Why

The shell establishes the visual identity. Judges see this first. A polished, professional shell with smooth navigation signals quality.

## Implementation

### 3.1 Set Up Router (`App.tsx`)

```tsx
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { UploadPage } from './pages/UploadPage';
import { DashboardPage } from './pages/DashboardPage';
import { ReviewPage } from './pages/ReviewPage';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Navbar />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/review/:shipmentId" element={<ReviewPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
```

### 3.2 Build Navbar Component

```tsx
// frontend/src/components/Navbar.tsx
import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Upload, LayoutDashboard, Shield, FileSearch } from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Upload', icon: Upload },
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  ];

  return (
    <nav className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Shield size={28} strokeWidth={2.5} />
        </div>
        <div className="brand-text">
          <span className="brand-name">ClearanceX</span>
          <span className="brand-subtitle">XAI Copilot</span>
        </div>
      </div>

      {/* Navigation */}
      <div className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'nav-item-active' : ''}`
            }
          >
            <item.icon size={20} />
            <span>{item.label}</span>
          </NavLink>
        ))}

        {/* Review link only shows when on review page */}
        {location.pathname.startsWith('/review') && (
          <div className="nav-item nav-item-active">
            <FileSearch size={20} />
            <span>Review</span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="xai-badge">
          <span>6-Layer XAI</span>
        </div>
        <span className="version-text">CodeSplash '26</span>
      </div>
    </nav>
  );
};
```

### 3.3 Navbar CSS

```css
/* Add to index.css */

/* ============================================ */
/*  APP LAYOUT                                  */
/* ============================================ */
.app-layout {
  display: flex;
  min-height: 100vh;
}

.app-main {
  flex: 1;
  margin-left: 240px; /* sidebar width */
  padding: 24px 32px;
  min-height: 100vh;
  background: var(--bg-primary);
}

/* ============================================ */
/*  SIDEBAR                                     */
/* ============================================ */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  width: 240px;
  height: 100vh;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  padding: 20px 12px;
  z-index: 100;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  margin-bottom: 32px;
}

.brand-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  border-radius: var(--radius-md);
  color: white;
  box-shadow: 0 2px 12px var(--accent-glow);
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.brand-subtitle {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
  transition: all var(--transition-fast);
  text-decoration: none;
  cursor: pointer;
}

.nav-item:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.nav-item-active {
  background: rgba(99, 102, 241, 0.12) !important;
  color: var(--accent-primary) !important;
  border-left: 3px solid var(--accent-primary);
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--border-subtle);
}

.xai-badge {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  color: white;
  padding: 4px 14px;
  border-radius: var(--radius-full);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.version-text {
  font-size: 0.7rem;
  color: var(--text-muted);
}
```

### 3.4 Create Placeholder Pages

```tsx
// frontend/src/pages/UploadPage.tsx
import React from 'react';
export const UploadPage: React.FC = () => (
  <div className="animate-fade-in">
    <h1>Upload Shipping Dossier</h1>
    <p style={{ color: 'var(--text-secondary)' }}>Phase 04 — coming next</p>
  </div>
);

// frontend/src/pages/DashboardPage.tsx
import React from 'react';
export const DashboardPage: React.FC = () => (
  <div className="animate-fade-in">
    <h1>Shipment Dashboard</h1>
    <p style={{ color: 'var(--text-secondary)' }}>Phase 05 — coming next</p>
  </div>
);

// frontend/src/pages/ReviewPage.tsx
import React from 'react';
import { useParams } from 'react-router-dom';
export const ReviewPage: React.FC = () => {
  const { shipmentId } = useParams<{ shipmentId: string }>();
  return (
    <div className="animate-fade-in">
      <h1>Review Shipment</h1>
      <p style={{ color: 'var(--text-secondary)' }}>Shipment: {shipmentId}</p>
    </div>
  );
};
```

## Acceptance Criteria

- [ ] Sidebar displays with ClearanceX branding and "6-Layer XAI" badge
- [ ] Navigation links route between Upload / Dashboard / Review
- [ ] Active page is highlighted in sidebar
- [ ] Page transitions have fade-in animation
- [ ] Dark theme renders correctly with glassmorphism
- [ ] Layout is clean with no content overflow

## Outputs

- `src/App.tsx` — Router setup
- `src/components/Navbar.tsx` — Sidebar navigation
- Placeholder pages ready for real content
- App shell ready for all subsequent phases
