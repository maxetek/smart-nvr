import { useEffect } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/stores/auth-store";
import { Skeleton } from "@/components/ui/skeleton";
import type { UserRole } from "@/types/user";

interface ProtectedRouteProps {
  requiredRole?: UserRole;
  children?: React.ReactNode;
}

export function ProtectedRoute({ requiredRole, children }: ProtectedRouteProps) {
  const { isAuthenticated, user, fetchProfile } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated && !user) {
      fetchProfile();
    }
  }, [isAuthenticated, user, fetchProfile]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950">
        <div className="space-y-4 w-64">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </div>
    );
  }

  if (requiredRole && user.role !== requiredRole && user.role !== "admin") {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-100">403</h1>
          <p className="mt-2 text-gray-400">You don't have permission to access this page.</p>
        </div>
      </div>
    );
  }

  return children ? <>{children}</> : <Outlet />;
}
