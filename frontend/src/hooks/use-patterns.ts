import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Pattern, PatternCreate, PatternUpdate } from "@/types/pattern";
import type { PaginatedResponse } from "@/types/pagination";

export function usePatterns(params?: { camera_id?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ["patterns", params],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Pattern>>("/patterns", { params });
      return data;
    },
  });
}

export function useCreatePattern() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (pattern: PatternCreate) => {
      const { data } = await api.post<Pattern>("/patterns", pattern);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patterns"] });
    },
  });
}

export function useUpdatePattern() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...update }: PatternUpdate & { id: string }) => {
      const { data } = await api.patch<Pattern>(`/patterns/${id}`, update);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patterns"] });
    },
  });
}

export function useDeletePattern() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/patterns/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patterns"] });
    },
  });
}
