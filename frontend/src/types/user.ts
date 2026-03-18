export type UserRole = "admin" | "operator" | "viewer";

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserRoleUpdate {
  role: UserRole;
}
