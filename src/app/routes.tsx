import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppRootLayout } from "@/layouts/AppRootLayout";
import { AppShell } from "@/layouts/AppShell";
import { ProtectedLayout } from "@/layouts/ProtectedLayout";
import { WorkflowLayout } from "@/layouts/WorkflowLayout";
import { AdminLayout } from "@/layouts/AdminLayout";
import { LoginPage } from "@/features/auth/LoginPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import {
  MergingPage,
  DivisionPage,
  TrainNoPage,
  TypesPage,
  SCRTrainPage,
  SCRStationPage,
  SummaryPage,
} from "@/features/workflows";
import { TemplateListPage, TemplateEditorPage } from "@/features/admin/templates";
import { PromptListPage, PromptEditorPage } from "@/features/admin/prompts";
import { AutomationDashboardPage } from "@/features/admin/automation";
import { SettingsPage } from "@/features/settings/SettingsPage";
import { LogsPage } from "@/features/logs/LogsPage";
import { NotFoundPage } from "@/features/errors/NotFoundPage";

export const router = createBrowserRouter([
  {
    element: <AppRootLayout />,
    children: [
      {
        path: "/login",
        element: <LoginPage />,
      },
      {
        path: "/",
        element: <ProtectedLayout />,
        children: [
          {
            element: <AppShell />,
            children: [
              {
                index: true,
                element: <Navigate to="/dashboard" replace />,
              },
              {
                path: "dashboard",
                element: <DashboardPage />,
              },
              {
                element: <WorkflowLayout />,
                children: [
                  {
                    path: "workflows/merging",
                    element: <MergingPage />,
                  },
                  {
                    path: "workflows/division",
                    element: <DivisionPage />,
                  },
                  {
                    path: "workflows/train-no",
                    element: <TrainNoPage />,
                  },
                  {
                    path: "workflows/types",
                    element: <TypesPage />,
                  },
                  {
                    path: "workflows/scr-train",
                    element: <SCRTrainPage />,
                  },
                  {
                    path: "workflows/scr-station",
                    element: <SCRStationPage />,
                  },
                  {
                    path: "workflows/summary",
                    element: <SummaryPage />,
                  },
                ],
              },
              {
                element: <AdminLayout />,
                children: [
                  {
                    path: "admin/templates",
                    element: <TemplateListPage />,
                  },
                  {
                    path: "admin/templates/:id/edit",
                    element: <TemplateEditorPage />,
                  },
                  {
                    path: "admin/templates/new",
                    element: <TemplateEditorPage />,
                  },
                  {
                    path: "admin/prompts",
                    element: <PromptListPage />,
                  },
                  {
                    path: "admin/prompts/new",
                    element: <PromptEditorPage />,
                  },
                  {
                    path: "admin/prompts/:id/edit",
                    element: <PromptEditorPage />,
                  },
                  {
                    path: "admin/automation",
                    element: <AutomationDashboardPage />,
                  },
                  {
                    path: "settings",
                    element: <SettingsPage />,
                  },
                  {
                    path: "logs",
                    element: <LogsPage />,
                  },
                ],
              },
            ],
          },
        ],
      },
      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
]);
