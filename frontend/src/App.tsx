import { useCallback, useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { api } from "./api";
import { useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { ConfirmEmailPage } from "./pages/ConfirmEmailPage";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { NewObservationPage } from "./pages/NewObservationPage";
import { PetsPage } from "./pages/PetsPage";
import { ProfilePage } from "./pages/ProfilePage";
import { SignUpPage } from "./pages/SignUpPage";
import type { Pet } from "./types";

export default function App() {
  return <Routes>
    <Route path="/" element={<LandingPage />} />
    <Route path="/signup" element={<SignUpPage />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="/confirm-email" element={<ConfirmEmailPage />} />
    <Route path="/app/*" element={<ProtectedApp />} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>;
}

function ProtectedApp() {
  const { user, loading, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [pets, setPets] = useState<Pet[]>([]);
  const [loadError, setLoadError] = useState("");

  const refresh = useCallback(async () => {
    try { setPets(await api.listPets()); setLoadError(""); }
    catch { setLoadError("The API is unavailable or your session has expired."); }
  }, []);

  useEffect(() => {
    if (!user) return;
    void api.listPets().then(setPets).catch(() => {
      setLoadError("The API is unavailable or your session has expired.");
    });
  }, [user]);

  if (loading) return <div className="app-loading">Opening your journal…</div>;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;

  const page = location.pathname.endsWith("/observe")
    ? "observe"
    : location.pathname.endsWith("/profile") ? "profile" : "pets";
  return <Layout
    page={page}
    user={user}
    onNavigate={(next) => navigate(
      next === "pets" ? "/app" : next === "observe" ? "/app/observe" : "/app/profile",
    )}
    onLogout={() => { logout(); navigate("/"); }}
  >
    {loadError && <div className="notice error">{loadError}</div>}
    <Routes>
      <Route index element={<PetsPage pets={pets} refresh={refresh} />} />
      <Route path="observe" element={<NewObservationPage pets={pets} />} />
      <Route path="profile" element={<ProfilePage user={user} />} />
      <Route path="*" element={<Navigate to="/app" replace />} />
    </Routes>
  </Layout>;
}
