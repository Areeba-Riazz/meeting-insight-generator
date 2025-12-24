import React from "react";
import { Routes, Route, NavLink, useNavigate, useLocation } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import InsightsPage from "./pages/InsightsPage";

export default function App() {
  const navigate = useNavigate();

  return (
    <>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/insights/:meetingId" element={<InsightsPage />} />
        <Route path="/insights/preview" element={<InsightsPage />} />
      </Routes>
    </>
  );
}