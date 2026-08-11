import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/AppShell";
import { ProjectProvider } from "./context/ProjectContext";
import { ApprovalPage } from "./pages/ApprovalPage";
import { CameraAnalysisPage } from "./pages/CameraAnalysisPage";
import { DraftReviewPage } from "./pages/DraftReviewPage";
import { EditingPlanPage } from "./pages/EditingPlanPage";
import { EvidencePage } from "./pages/EvidencePage";
import { ProjectSetupPage } from "./pages/ProjectSetupPage";
import { SynchronisationPage } from "./pages/SynchronisationPage";

export default function App() {
  return (
    <Routes>
      <Route
        element={
          <ProjectProvider>
            <AppShell />
          </ProjectProvider>
        }
      >
        <Route index element={<ProjectSetupPage />} />
        <Route
          path="projects/:projectId/setup"
          element={<ProjectSetupPage />}
        />
        <Route
          path="projects/:projectId/analysis"
          element={<CameraAnalysisPage />}
        />
        <Route
          path="projects/:projectId/synchronisation"
          element={<SynchronisationPage />}
        />
        <Route
          path="projects/:projectId/editing-plan"
          element={<EditingPlanPage />}
        />
        <Route
          path="projects/:projectId/draft-review"
          element={<DraftReviewPage />}
        />
        <Route path="projects/:projectId/approval" element={<ApprovalPage />} />
        <Route path="projects/:projectId/evidence" element={<EvidencePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
