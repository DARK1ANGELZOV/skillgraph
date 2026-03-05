import { Navigate, Route, Routes } from "react-router-dom";

import { AdminLayout } from "./components/AdminLayout";
import { DashboardPage } from "./features/dashboard/DashboardPage";
import { AnalyticsPage } from "./features/analytics/AnalyticsPage";
import { InterviewsPage } from "./features/dashboard/InterviewsPage";
import { SettingsPage } from "./features/dashboard/SettingsPage";
import { SuperadminPage } from "./features/dashboard/SuperadminPage";
import { MarketingPage } from "./features/marketing/MarketingPage";
import { CandidateInterviewPage } from "./features/candidate/CandidateInterviewPage";
import { LoginPage } from "./features/auth/LoginPage";
import { useAuth } from "./features/auth/AuthContext";

function Protected({ children }) {
  const { loading, session } = useAuth();

  if (loading) {
    return <div className="center-screen">Loading session...</div>;
  }

  if (!session) {
    return <Navigate to="/auth" replace />;
  }

  return children;
}

function HomeRedirect() {
  const { session } = useAuth();
  if (!session) {
    return <Navigate to="/auth" replace />;
  }
  return <Navigate to={session.role === "SUPERADMIN" ? "/app/superadmin" : "/app/dashboard"} replace />;
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<MarketingPage />} />
      <Route path="/auth" element={<LoginPage />} />
      <Route path="/interview/:token" element={<CandidateInterviewPage />} />
      <Route
        path="/app"
        element={
          <Protected>
            <AdminLayout />
          </Protected>
        }
      >
        <Route index element={<HomeRedirect />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="interviews" element={<InterviewsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="superadmin" element={<SuperadminPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
