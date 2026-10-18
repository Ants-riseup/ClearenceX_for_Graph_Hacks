import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { BrowserRouter, Routes, Route, useLocation, Navigate, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { ShipmentProvider, useShipment } from './hooks/useShipment';

const Header = lazy(() => import('./components/layout/Header').then(module => ({ default: module.Header })));
import { Footer } from './components/layout/Footer';
import { ToastNotification } from './components/layout/ToastNotification';
import { ScreenBoundary } from './components/layout/ScreenBoundary';

const ScreenOverview = lazy(() => import('./components/screens/ScreenOverview').then(module => ({ default: module.ScreenOverview })));
const ScreenDossiers = lazy(() => import('./components/screens/ScreenDossiers').then(module => ({ default: module.ScreenDossiers })));
const ScreenReviewWorkspace = lazy(() => import('./components/screens/ScreenReviewWorkspace').then(module => ({ default: module.ScreenReviewWorkspace })));
const ScreenDiscrepancies = lazy(() => import('./components/screens/ScreenDiscrepancies').then(module => ({ default: module.ScreenDiscrepancies })));
const ScreenBatchFiling = lazy(() => import('./components/screens/ScreenBatchFiling').then(module => ({ default: module.ScreenBatchFiling })));
const ScreenAsycudaGateway = lazy(() => import('./components/screens/ScreenAsycudaGateway').then(module => ({ default: module.ScreenAsycudaGateway })));
const ScreenKnowledgeGraph = lazy(() => import('./components/screens/ScreenKnowledgeGraph').then(m => ({ default: m.ScreenKnowledgeGraph })));
const ScreenAuditTrail = lazy(() => import('./components/screens/ScreenAuditTrail').then(module => ({ default: module.ScreenAuditTrail })));
const ScreenTariffDirectory = lazy(() => import('./components/screens/ScreenTariffDirectory').then(module => ({ default: module.ScreenTariffDirectory })));
const ScreenSettings = lazy(() => import('./components/screens/ScreenSettings').then(module => ({ default: module.ScreenSettings })));
const ScreenAdminDashboard = lazy(() => import('./components/screens/ScreenAdminDashboard').then(module => ({ default: module.ScreenAdminDashboard })));
const ScreenContextAgent = lazy(() => import('./components/screens/ScreenContextAgent').then(module => ({ default: module.ScreenContextAgent })));
const ScreenSignIn = lazy(() => import('./components/screens/ScreenAuth').then(module => ({ default: module.ScreenSignIn })));
const ScreenSignUp = lazy(() => import('./components/screens/ScreenAuth').then(module => ({ default: module.ScreenSignUp })));
const ScreenRecovery = lazy(() => import('./components/screens/ScreenAuth').then(module => ({ default: module.ScreenRecovery })));
const ScreenChangePassword = lazy(() => import('./components/screens/ScreenAuth').then(module => ({ default: module.ScreenChangePassword })));

interface Toast {
  title: string;
  message: string;
  type?: 'error' | 'info' | 'success';
}

function AppInner() {
  const { shipmentId } = useShipment();
  const { user, loading: authLoading } = useAuth();
  const [toast, setToast] = useState<Toast | null>(null);
  const location = useLocation();
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mainRef = useRef<HTMLElement>(null);
  useEffect(() => () => { if (toastTimer.current) clearTimeout(toastTimer.current); }, []);
  useEffect(() => { window.scrollTo({ top: 0 }); mainRef.current?.focus(); }, [location.pathname]);
  const isOverview = location.pathname === '/';

  const showToast = useCallback((toastObj: Toast) => {
    setToast(toastObj);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 6000);
  }, []);

  if (authLoading) return <main className="min-h-screen grid place-items-center">Checking your session…</main>;
  if (!user && !location.pathname.startsWith('/auth/')) return <Navigate to="/auth/signin" replace />;
  if (!user && location.pathname === '/auth/change-password') return <Navigate to="/auth/signin" replace />;
  if (user?.requires_password_change && location.pathname !== '/auth/change-password') return <Navigate to="/auth/change-password" replace />;
  if (user?.role === 'platform_admin' && location.pathname !== '/admin/companies') return <Navigate to="/admin/companies" replace />;
  if (user && user.role !== 'platform_admin' && location.pathname.startsWith('/admin/')) return <Navigate to="/" replace />;

  if (user && location.pathname.startsWith('/auth/') && location.pathname !== '/auth/change-password') return <Navigate to={user.role === 'platform_admin' ? '/admin/companies' : '/'} replace />;

  return (
    <div className="min-h-screen flex flex-col bg-background font-sans text-on-surface antialiased">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[110] focus:rounded-lg focus:bg-white focus:p-3 focus:text-primary">Skip to content</a>
      {user && !user.requires_password_change && <ScreenBoundary><Suspense fallback={<header className="fixed top-0 inset-x-0 z-50 bg-surface-container-lowest px-6 py-5 font-semibold">ClearanceX</header>}><Header /></Suspense></ScreenBoundary>}
      <main id="main-content" tabIndex={-1} ref={mainRef} className={`w-full flex-1 flex flex-col ${ !user || user.requires_password_change || isOverview ? '' : 'pt-20' }`}>
          <ScreenBoundary key={location.pathname}><Suspense fallback={<div role="status" className="p-12 text-center text-on-surface-variant">Loading your workspace…</div>}><Routes>
            <Route path="/" element={<ScreenOverview onTriggerToast={showToast} />} />
            <Route path="/dossiers" element={<ScreenDossiers onTriggerToast={showToast} />} />
            <Route path="/context-agent" element={<ScreenContextAgent key={shipmentId ?? 'empty'} />} />
            <Route path="/review-workspace" element={<ScreenReviewWorkspace onTriggerToast={showToast} />} />
            <Route path="/discrepancies" element={<ScreenDiscrepancies onTriggerToast={showToast} />} />
            <Route path="/batch-filing" element={<ScreenBatchFiling onTriggerToast={showToast} />} />
            <Route path="/asycuda-gateway" element={<ScreenAsycudaGateway onTriggerToast={showToast} />} />
            <Route path="/knowledge-graph" element={<Suspense fallback={<p role="status" className="p-8">Loading graph explorer…</p>}><ScreenKnowledgeGraph onTriggerToast={showToast} /></Suspense>} />
            <Route path="/audit-trail" element={<ScreenAuditTrail onTriggerToast={showToast} />} />
            <Route path="/tariff-directory" element={<ScreenTariffDirectory onTriggerToast={showToast} />} />
            <Route path="/settings" element={<ScreenSettings onTriggerToast={showToast} />} />
            <Route path="/admin/companies" element={<ScreenAdminDashboard />} />
            <Route path="/auth/signin" element={<ScreenSignIn onTriggerToast={showToast} />} />
            <Route path="/auth/signup" element={<ScreenSignUp onTriggerToast={showToast} />} />
            <Route path="/auth/recovery" element={<ScreenRecovery onTriggerToast={showToast} />} />
            <Route path="/auth/change-password" element={<ScreenChangePassword onTriggerToast={showToast} />} />
            <Route path="*" element={<section className="max-w-xl mx-auto p-10 text-center"><p className="text-primary text-sm font-semibold">404</p><h1 className="text-3xl font-bold mt-3">This page could not be found</h1><p className="mt-3 text-on-surface-variant">The link may be outdated. Your saved shipments are still available.</p><Link to={user ? "/" : "/auth/signin"} className="inline-block mt-6 rounded-lg bg-primary text-white px-5 py-3">{user ? "Return to your workspace" : "Go to sign in"}</Link></section>} />
          </Routes></Suspense></ScreenBoundary>
        </main>
        <Footer />
        <ToastNotification toast={toast} onClose={() => setToast(null)} />
      </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <ShipmentProvider>
        <AuthProvider><AppInner /></AuthProvider>
      </ShipmentProvider>
    </BrowserRouter>
  );
}

export default App;
