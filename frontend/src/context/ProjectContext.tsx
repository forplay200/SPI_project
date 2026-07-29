import { useQuery } from "@tanstack/react-query";
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  type ReactNode,
} from "react";
import { useParams } from "react-router-dom";

import { api } from "../api/client";

const STORAGE_KEY = "graduation-video-project-id";

type ProjectContextValue = {
  projectId: string | null;
  setProjectId: (value: string) => void;
};

const ProjectContext = createContext<ProjectContextValue | null>(null);

export function ProjectProvider({ children }: { children: ReactNode }) {
  const params = useParams();
  const routeId = params.projectId ?? null;
  useEffect(() => {
    if (routeId) localStorage.setItem(STORAGE_KEY, routeId);
  }, [routeId]);
  const value = useMemo(
    () => ({
      projectId: routeId ?? localStorage.getItem(STORAGE_KEY),
      setProjectId: (id: string) => localStorage.setItem(STORAGE_KEY, id),
    }),
    [routeId],
  );
  return (
    <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>
  );
}

export function useProjectContext() {
  const value = useContext(ProjectContext);
  if (!value) throw new Error("ProjectProvider is missing");
  return value;
}

export function useCurrentProject() {
  const { projectId } = useProjectContext();
  return useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId as string),
    enabled: Boolean(projectId),
  });
}
