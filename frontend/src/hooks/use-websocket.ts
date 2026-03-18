import { useEffect } from "react";
import { wsClient } from "@/lib/ws";
import { useNotificationStore } from "@/stores/notification-store";
import { toast } from "sonner";

export function useWebSocket() {
  const addNotification = useNotificationStore((s) => s.addNotification);

  useEffect(() => {
    wsClient.connect();

    const unsubscribe = wsClient.subscribe((event) => {
      const notification = {
        id: event.id as string || crypto.randomUUID(),
        event_type: event.event_type as string || "unknown",
        camera_name: event.camera_name as string || "Unknown Camera",
        severity: event.severity as string || "info",
        timestamp: event.created_at as string || new Date().toISOString(),
      };

      addNotification(notification);

      const message = `${notification.event_type} detected on ${notification.camera_name}`;
      const severity = notification.severity.toLowerCase();

      if (severity === "critical") {
        toast.error(message, { duration: Infinity });
      } else if (severity === "warning") {
        toast.warning(message, { duration: 10000 });
      } else {
        toast.info(message, { duration: 5000 });
      }
    });

    return () => {
      unsubscribe();
      wsClient.disconnect();
    };
  }, [addNotification]);
}
