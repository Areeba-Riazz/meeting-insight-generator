import React from "react";
import { Routes, Route } from "react-router-dom";
import ProjectsPage from "./pages/ProjectsPage";
import ProjectDetailPage from "./pages/ProjectDetailPage";
import UploadPage from "./pages/UploadPage";
import InsightsPage from "./pages/InsightsPage";
import SearchPage from "./pages/SearchPage";

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<ProjectsPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
        <Route path="/projects/:projectId/upload" element={<UploadPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/insights/:meetingId" element={<InsightsPage />} />
        <Route path="/insights/preview" element={<InsightsPage />} />
      </Routes>
    </>
  );
}