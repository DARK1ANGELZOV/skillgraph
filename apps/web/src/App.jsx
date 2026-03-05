import { Navigate, Route, Routes } from "react-router-dom";

import { LandingPage } from "./pages/LandingPage";
import { InterviewPage } from "./pages/InterviewPage";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/interview/:token" element={<InterviewPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
