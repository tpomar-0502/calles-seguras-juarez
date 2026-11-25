import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Navbar } from "./components/Navbar";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { CreateReportPage } from "./pages/CreateReportPage";
import { ExplorePage } from "./pages/ExplorePage";
import { LoginPage } from "./pages/LoginPage";
import { ModerationPage } from "./pages/ModerationPage";
import { MyReportsPage } from "./pages/MyReportsPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ReportDetailPage } from "./pages/ReportDetailPage";

const ProtectedRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { usuario, cargando } = useAuth();
  if (cargando) return <div className="container page-content"><p>Verificando sesión...</p></div>;
  if (!usuario) return <Navigate to="/login" replace />;
  return children;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="app-shell">
          <Navbar />
          <main className="app-main">
            <Routes>
              <Route path="/" element={<ExplorePage />} />
              <Route path="/reportes/:folio" element={<ReportDetailPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/registro" element={<RegisterPage />} />
              <Route
                path="/reportar"
                element={<ProtectedRoute><CreateReportPage /></ProtectedRoute>}
              />
              <Route
                path="/mis-reportes"
                element={<ProtectedRoute><MyReportsPage /></ProtectedRoute>}
              />
              <Route
                path="/moderacion"
                element={<ProtectedRoute><ModerationPage /></ProtectedRoute>}
              />
              <Route
                path="/admin"
                element={<ProtectedRoute><AdminDashboardPage /></ProtectedRoute>}
              />
            </Routes>
          </main>
          <footer className="site-footer">
            <div className="container">
              <p>
                Asociación Civil <strong>Calles Seguras Juárez</strong> · Ciudad Juárez, Chihuahua ·
                Aviso de Privacidad conforme a la LFPDPPP (los reportes públicos son anónimos).
              </p>
            </div>
          </footer>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;