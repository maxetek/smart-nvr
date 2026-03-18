import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Camera, CameraCreate, CameraUpdate } from "@/types/camera";
import type { PaginatedResponse } from "@/types/pagination";

export function useCameras(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ["cameras", params],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Camera>>("/cameras", { params });
      return data;
    },
  });
}

export function useCamera(id: string) {
  return useQuery({
    queryKey: ["cameras", id],
    queryFn: async () => {
      const { data } = await api.get<Camera>(`/cameras/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateCamera() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (camera: CameraCreate) => {
      const { data } = await api.post<Camera>("/cameras", camera);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cameras"] });
    },
  });
}

export function useUpdateCamera() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...update }: CameraUpdate & { id: string }) => {
      const { data } = await api.patch<Camera>(`/cameras/${id}`, update);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cameras"] });
    },
  });
}

export function useDeleteCamera() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/cameras/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cameras"] });
    },
  });
}
