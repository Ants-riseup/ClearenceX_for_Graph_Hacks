import { useCallback, useState } from 'react';
import { BrowserRouter, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { ShipmentProvider, useShipment } from './hooks/useShipment';

import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { ToastNotification } from './components/layout/ToastNotification';

import { ScreenOverview } from './components/screens/ScreenOverview';
import { ScreenDossiers } from './components/screens/ScreenDossiers';
import { ScreenReviewWorkspace } from './components/screens/ScreenReviewWorkspace';
import { ScreenDiscrepancies } from './components/screens/ScreenDiscrepancies';
import { ScreenBatchFiling } from './components/screens/ScreenBatchFiling';
import { ScreenAsycudaGateway } from './components/screens/ScreenAsycudaGateway';
import { ScreenKnowledgeGraph } from './components/screens/ScreenKnowledgeGraph';
import { ScreenAuditTrail } from './components/screens/ScreenAuditTrail';
import { ScreenTariffDirectory } from './components/screens/ScreenTariffDirectory';
import { ScreenSettings } from './components/screens/ScreenSettings';
import { ScreenContextAgent } from './components/screens/ScreenContextAgent';
import { ScreenSignIn, ScreenSignUp, ScreenRecovery } from './components/screens/ScreenAuth';

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
  const isOverview = location.pathname === '/';

  const showToast = useCallback((toastObj: Toast) => {
    setToast(toastObj);
    setTimeout(() => setToast(null), 4000);
  }, []);

  if (authLoading) return <main className="min-h-screen grid place-items-center">Checking your session…</main>;
  if (!user && !location.pathname.startsWith('/auth/')) return <Navigate to="/auth/signin" replace />;

  return (
    <div className="min-h-screen flex flex-col bg-background font-sans text-on-surface antialiased">
      <Header />
      <main className={`w-full flex-1 flex flex-col ${ isOverview ? '' : 'pt-20' }`}>
          <Routes>
            <Route path="/" element={<ScreenOverview onTriggerToast={showToast} />} />
            <Route path="/dossiers" element={<ScreenDossiers onTriggerToast={showToast} />} />
            <Route path="/context-agent" element={<ScreenContextAgent key={shipmentId ?? 'empty'} />} />
            <Route path="/review-workspace" element={<ScreenReviewWorkspace onTriggerToast={showToast} />} />
            <Route path="/discrepancies" element={<ScreenDiscrepancies onTriggerToast={showToast} />} />
            <Route path="/batch-filing" element={<ScreenBatchFiling onTriggerToast={showToast} />} />
            <Route path="/asycuda-gateway" element={<ScreenAsycudaGateway onTriggerToast={showToast} />} />
            <Route path="/knowledge-graph" element={<ScreenKnowledgeGraph onTriggerToast={showToast} />} />
            <Route path="/audit-trail" element={<ScreenAuditTrail onTriggerToast={showToast} />} />
            <Route path="/tariff-directory" element={<ScreenTariffDirectory onTriggerToast={showToast} />} />
            <Route path="/settings" element={<ScreenSettings onTriggerToast={showToast} />} />
            <Route path="/auth/signin" element={<ScreenSignIn onTriggerToast={showToast} />} />
            <Route path="/auth/signup" element={<ScreenSignUp onTriggerToast={showToast} />} />
            <Route path="/auth/recovery" element={<ScreenRecovery onTriggerToast={showToast} />} />
          </Routes>
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
