import { useRef, useEffect, useState } from "react";
import { Maximize, RefreshCw, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface CameraPlayerProps {
  cameraName: string;
}

export function CameraPlayer({ cameraName }: CameraPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const [status, setStatus] = useState<"connecting" | "connected" | "error">("connecting");

  useEffect(() => {
    let cancelled = false;
    let mseWs: WebSocket | null = null;

    async function tryWebRTC() {
      try {
        const pc = new RTCPeerConnection();
        pcRef.current = pc;

        pc.addTransceiver("video", { direction: "recvonly" });
        pc.addTransceiver("audio", { direction: "recvonly" });

        pc.ontrack = (event) => {
          if (videoRef.current && event.streams[0]) {
            videoRef.current.srcObject = event.streams[0];
            if (!cancelled) setStatus("connected");
          }
        };

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        const resp = await fetch(
          `/go2rtc/api/webrtc?src=${encodeURIComponent(cameraName)}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/sdp" },
            body: offer.sdp,
          }
        );

        if (!resp.ok) throw new Error("WebRTC negotiation failed");

        const sdp = await resp.text();
        await pc.setRemoteDescription(new RTCSessionDescription({ type: "answer", sdp }));
      } catch {
        if (!cancelled) tryMSE();
      }
    }

    function tryMSE() {
      try {
        const video = videoRef.current;
        if (!video || !("MediaSource" in window)) {
          if (!cancelled) setStatus("error");
          return;
        }

        const ms = new MediaSource();
        video.src = URL.createObjectURL(ms);

        ms.addEventListener("sourceopen", () => {
          const protocol = window.location.protocol === "https:" ? "wss" : "ws";
          mseWs = new WebSocket(
            `${protocol}://${window.location.host}/go2rtc/api/ws?src=${encodeURIComponent(cameraName)}`
          );
          mseWs.binaryType = "arraybuffer";

          let sourceBuffer: SourceBuffer | null = null;
          const queue: ArrayBuffer[] = [];
          let mimeType = "";

          mseWs.onmessage = (event) => {
            if (typeof event.data === "string") {
              const msg = JSON.parse(event.data);
              if (msg.type === "mse") {
                mimeType = msg.value;
                sourceBuffer = ms.addSourceBuffer(mimeType);
                sourceBuffer.addEventListener("updateend", () => {
                  if (queue.length > 0 && sourceBuffer && !sourceBuffer.updating) {
                    sourceBuffer.appendBuffer(queue.shift()!);
                  }
                });
                if (!cancelled) setStatus("connected");
              }
            } else if (sourceBuffer) {
              if (sourceBuffer.updating) {
                queue.push(event.data);
              } else {
                sourceBuffer.appendBuffer(event.data);
              }
            }
          };

          mseWs.onerror = () => {
            if (!cancelled) setStatus("error");
          };
        });
      } catch {
        if (!cancelled) setStatus("error");
      }
    }

    tryWebRTC();

    return () => {
      cancelled = true;
      pcRef.current?.close();
      pcRef.current = null;
      mseWs?.close();
    };
  }, [cameraName]);

  const handleReconnect = () => {
    setStatus("connecting");
    pcRef.current?.close();
    pcRef.current = null;
    // Re-trigger by changing key — handled by parent
    window.location.reload();
  };

  const handleFullscreen = () => {
    videoRef.current?.requestFullscreen();
  };

  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-md border border-gray-800 bg-black">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="h-full w-full object-contain"
      />

      {status === "connecting" && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/60">
          <Loader2 className="h-8 w-8 animate-spin text-blue-400" />
        </div>
      )}

      {status === "error" && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/60">
          <p className="text-sm text-gray-400">Connection failed</p>
          <Button variant="outline" size="sm" onClick={handleReconnect}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Reconnect
          </Button>
        </div>
      )}

      {status === "connected" && (
        <div className="absolute bottom-2 right-2 opacity-0 transition-opacity hover:opacity-100 group-hover:opacity-100">
          <Button variant="ghost" size="icon" onClick={handleFullscreen}>
            <Maximize className="h-4 w-4" />
          </Button>
        </div>
      )}

      <div className="absolute left-2 top-2">
        <span className="rounded bg-black/70 px-2 py-1 text-xs text-gray-200">
          {cameraName}
        </span>
      </div>
    </div>
  );
}
