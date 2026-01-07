import { BrowserRouter as Router, Routes, Route, useLocation, Link } from 'react-router-dom';
import { useState } from 'react';
import { ToastProvider } from './contexts/ToastContext';
import { ToastContainer } from './components/Toast';
import { UIConfigProvider } from './contexts/UIConfigContext';
import { LightboxProvider } from './components/Lightbox';
import { MainLayout } from './components/Layout/MainLayout';
import Home from './pages/Home';
import { VideoStudio } from './pages/VideoStudio';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './components/Auth/Login';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { session, loading } = useAuth();
  
  if (loading) {
    return <div className="flex items-center justify-center h-screen bg-gray-900 text-white">Loading...</div>;
  }

  if (!session) {
    return <Login />;
  }

  return <>{children}</>;
};

const LayoutWrapper = () => {
  const [isLeftOpen, setLeftOpen] = useState(true);
  const [isRightOpen, setRightOpen] = useState(true);
  const location = useLocation();
  const isVideoPage = location.pathname.startsWith('/video');

  return (
    <MainLayout
       header={
         <div className="h-16 flex items-center justify-between px-6 border-b border-[var(--glass-border)] bg-[var(--md-sys-color-surface)]">
            <div className="font-bold text-xl text-[var(--md-sys-color-primary)] flex items-center gap-6">
                <Link to="/">GridWorkflow</Link>
                <Link to="/video" className={`text-sm font-medium ${isVideoPage ? 'text-blue-600' : 'text-gray-500 hover:text-blue-600'}`}>Video Studio</Link>
            </div>
            {!isVideoPage && (
            <div className="flex gap-2">
                <button className="btn-primary text-sm" onClick={() => setLeftOpen(!isLeftOpen)}>Toggle Left</button>
                <button className="btn-primary text-sm" onClick={() => setRightOpen(!isRightOpen)}>Toggle Right</button>
            </div>
            )}
         </div>
       }
       sidebarLeft={isVideoPage ? null : (
         <div className="p-4 h-full overflow-auto">
            <h3 className="font-bold mb-4">Sidebar Left</h3>
            <p className="text-sm text-[var(--md-sys-color-on-surface-variant)]">Navigation items go here.</p>
         </div>
       )}
       sidebarRight={isVideoPage ? null : (
         <div className="p-4 h-full overflow-auto">
            <h3 className="font-bold mb-4">Sidebar Right</h3>
             <p className="text-sm text-[var(--md-sys-color-on-surface-variant)]">Inspector or details go here.</p>
         </div>
       )}
       mobileNav={<div className="lg:hidden fixed bottom-0 left-0 right-0 h-16 bg-[var(--md-sys-color-surface)] border-t border-[var(--glass-border)]">Mobile Nav</div>}
       footer={null}
       isSidebarLeftOpen={isLeftOpen}
       isSidebarRightOpen={isRightOpen}
       onOverlayClick={() => { setLeftOpen(false); setRightOpen(false); }}
    >
      <div className={isVideoPage ? "h-full" : "h-full overflow-auto p-6"}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/video" element={<VideoStudio />} />
        </Routes>
      </div>
    </MainLayout>
  );
};

function App() {
  return (
    <UIConfigProvider>
      <ToastProvider>
        <LightboxProvider>
           <AuthProvider>
             <Router>
                <ProtectedRoute>
                  <LayoutWrapper />
                </ProtectedRoute>
                <ToastContainer />
             </Router>
           </AuthProvider>
        </LightboxProvider>
      </ToastProvider>
    </UIConfigProvider>
  );
}

export default App;
