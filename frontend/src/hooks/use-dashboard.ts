import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { DashboardData } from "@/types/dashboard";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => {
      const { data } = await api.get<DashboardData>("/dashboard");
      return data;
    },
    refetchInterval: 30000,
  });
}
