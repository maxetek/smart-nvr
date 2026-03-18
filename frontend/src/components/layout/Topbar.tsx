import { Menu, LogOut, User } from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { useNavigate } from "react-router-dom";
import { DropdownMenu, DropdownMenuItem } from "@/components/ui/dropdown-menu";

interface TopbarProps {
  onMenuClick: () => void;
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-gray-800 bg-gray-900 px-4">
      <button
        onClick={onMenuClick}
        className="rounded p-1 text-gray-400 hover:text-gray-100 lg:hidden"
      >
        <Menu className="h-6 w-6" />
      </button>

      <div className="hidden lg:block" />

      <DropdownMenu
        trigger={
          <button className="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm text-gray-300 hover:bg-gray-800 transition-colors">
            <User className="h-4 w-4" />
            <span>{user?.username}</span>
          </button>
        }
      >
        <div className="border-b border-gray-800 px-3 py-2">
          <p className="text-sm font-medium text-gray-100">{user?.username}</p>
          <p className="text-xs text-gray-400">{user?.email}</p>
          <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
        </div>
        <DropdownMenuItem onClick={handleLogout}>
          <LogOut className="mr-2 h-4 w-4" />
          Logout
        </DropdownMenuItem>
      </DropdownMenu>
    </header>
  );
}
