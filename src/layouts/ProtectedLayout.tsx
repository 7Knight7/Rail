import { Navigate, Outlet, useLocation } from "react-router-dom";
import { Train } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Spinner } from "@/components/ui/Spinner";

function LoadingScreen() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-100">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-600">
        <Train className="h-8 w-8 text-white" />
      </div>
      <Spinner size="lg" />
      <p className="mt-4 text-sm text-slate-600">Loading...</p>
    </div>
  );
}

export function ProtectedLayout() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}
