import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Event, EventListParams, AcknowledgeRequest } from "@/types/event";
import type { PaginatedResponse } from "@/types/pagination";

export function useEvents(params?: EventListParams) {
  return useQuery({
    queryKey: ["events", params],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Event>>("/events", { params });
      return data;
    },
  });
}

export function useEvent(id: string) {
  return useQuery({
    queryKey: ["events", id],
    queryFn: async () => {
      const { data } = await api.get<Event>(`/events/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useAcknowledgeEvents() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (req: AcknowledgeRequest) => {
      const { data } = await api.post("/events/acknowledge", req);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
