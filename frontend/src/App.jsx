import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './utils/auth';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import RFQCreatePage from './pages/RFQCreatePage';
import AuctionListingPage from './pages/AuctionListingPage';
import AuctionDetailPage from './pages/AuctionDetailPage';

function ProtectedRoute({ children, requireRole }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  if (requireRole && user.role !== requireRole) {
    return <Navigate to="/auctions" replace />;
  }

  return children;
}

function AppLayout({ children }) {
  return (
    <div className="min-h-screen bg-[#0a0f1e]">
      <Navbar />
      <main>{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected: all authenticated users */}
          <Route path="/auctions" element={
            <ProtectedRoute>
              <AppLayout><AuctionListingPage /></AppLayout>
            </ProtectedRoute>
          } />
          <Route path="/auction/:id" element={
            <ProtectedRoute>
              <AppLayout><AuctionDetailPage /></AppLayout>
            </ProtectedRoute>
          } />

          {/* Protected: buyers only */}
          <Route path="/rfq/create" element={
            <ProtectedRoute requireRole="buyer">
              <AppLayout><RFQCreatePage /></AppLayout>
            </ProtectedRoute>
          } />

          {/* Fallback */}
          <Route path="/" element={<Navigate to="/auctions" replace />} />
          <Route path="*" element={<Navigate to="/auctions" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
