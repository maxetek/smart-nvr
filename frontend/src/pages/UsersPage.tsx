import { useUsers, useUpdateUserRole, useDeactivateUser } from "@/hooks/use-users";
import { useAuthStore } from "@/stores/auth-store";
import { UserTable } from "@/components/users/UserTable";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import type { UserRole } from "@/types/user";

export default function UsersPage() {
  const { data, isLoading } = useUsers({ limit: 100 });
  const user = useAuthStore((s) => s.user);
  const roleMutation = useUpdateUserRole();
  const toggleMutation = useDeactivateUser();

  const users = data?.items || [];

  const handleRoleChange = async (userId: string, role: UserRole) => {
    try {
      await roleMutation.mutateAsync({ id: userId, role });
      toast.success("Role updated");
    } catch {
      toast.error("Failed to update role");
    }
  };

  const handleToggleActive = async (userId: string, isActive: boolean) => {
    try {
      await toggleMutation.mutateAsync({ id: userId, is_active: isActive });
      toast.success(isActive ? "User activated" : "User deactivated");
    } catch {
      toast.error("Failed to update user status");
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-100">Users</h1>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-100">Users</h1>

      <div className="rounded-lg border border-gray-800 bg-gray-900">
        <UserTable
          users={users}
          onRoleChange={handleRoleChange}
          onToggleActive={handleToggleActive}
          currentUserId={user?.id}
        />
      </div>
    </div>
  );
}
