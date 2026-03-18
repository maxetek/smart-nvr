import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { User, UserRoleUpdate } from "@/types/user";
import type { PaginatedResponse } from "@/types/pagination";

export function useUsers(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ["users", params],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<User>>("/users", { params });
      return data;
    },
  });
}

export function useUpdateUserRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...update }: UserRoleUpdate & { id: string }) => {
      const { data } = await api.patch<User>(`/users/${id}/role`, update);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
}

export function useDeactivateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, is_active }: { id: string; is_active: boolean }) => {
      const { data } = await api.patch<User>(`/users/${id}`, { is_active });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
}
