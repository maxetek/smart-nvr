import { format } from "date-fns";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RoleBadge } from "./RoleBadge";
import type { User, UserRole } from "@/types/user";

interface UserTableProps {
  users: User[];
  onRoleChange: (userId: string, role: UserRole) => void;
  onToggleActive: (userId: string, isActive: boolean) => void;
  currentUserId?: string;
}

const roles: UserRole[] = ["admin", "operator", "viewer"];

export function UserTable({ users, onRoleChange, onToggleActive, currentUserId }: UserTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Username</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Role</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Created</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {users.map((user) => (
          <TableRow key={user.id}>
            <TableCell className="font-medium">{user.username}</TableCell>
            <TableCell className="text-gray-400">{user.email}</TableCell>
            <TableCell>
              <select
                className="rounded border border-gray-700 bg-gray-800 px-2 py-1 text-xs text-gray-100"
                value={user.role}
                onChange={(e) => onRoleChange(user.id, e.target.value as UserRole)}
                disabled={user.id === currentUserId}
              >
                {roles.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </TableCell>
            <TableCell>
              <Badge variant={user.is_active ? "success" : "outline"}>
                {user.is_active ? "Active" : "Inactive"}
              </Badge>
            </TableCell>
            <TableCell className="text-gray-400">
              {format(new Date(user.created_at), "MMM d, yyyy")}
            </TableCell>
            <TableCell>
              {user.id !== currentUserId && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onToggleActive(user.id, !user.is_active)}
                >
                  {user.is_active ? "Deactivate" : "Activate"}
                </Button>
              )}
            </TableCell>
          </TableRow>
        ))}
        {users.length === 0 && (
          <TableRow>
            <TableCell colSpan={6} className="text-center text-gray-400 py-8">
              No users found.
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}

// Keep RoleBadge import used
void RoleBadge;
