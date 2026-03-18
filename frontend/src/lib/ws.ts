type EventCallback = (event: Record<string, unknown>) => void;

class SmartNVRWebSocket {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private listeners: Set<EventCallback> = new Set();

  connect() {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    this.ws = new WebSocket(
      `${protocol}://${window.location.host}/ws/events?token=${token}`
    );

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.listeners.forEach((fn) => fn(data));
    };

    this.ws.onclose = () => {
      this.reconnectTimer = setTimeout(() => this.connect(), 5000);
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }

  subscribe(callback: EventCallback) {
    this.listeners.add(callback);
    return () => {
      this.listeners.delete(callback);
    };
  }
}

export const wsClient = new SmartNVRWebSocket();
