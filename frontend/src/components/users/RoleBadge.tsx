import { Badge } from "@/components/ui/badge";
import type { UserRole } from "@/types/user";

interface RoleBadgeProps {
  role: UserRole;
}

export function RoleBadge({ role }: RoleBadgeProps) {
  const variants: Record<UserRole, "destructive" | "warning" | "default"> = {
    admin: "destructive",
    operator: "warning",
    viewer: "default",
  };

  return (
    <Badge variant={variants[role]} className="capitalize">
      {role}
    </Badge>
  );
}
