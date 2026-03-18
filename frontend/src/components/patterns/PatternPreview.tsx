import { useEffect, useRef } from "react";

interface PatternPreviewProps {
  imageUrl: string;
  patternType: string;
  configJson: Record<string, unknown>;
  width?: number;
  height?: number;
}

export function PatternPreview({
  imageUrl,
  patternType,
  configJson,
  width = 320,
  height = 240,
}: PatternPreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.drawImage(img, 0, 0, width, height);
      drawOverlay(ctx);
    };
    img.onerror = () => {
      ctx.fillStyle = "#1a1a2e";
      ctx.fillRect(0, 0, width, height);
      drawOverlay(ctx);
    };
    img.src = imageUrl;

    function drawOverlay(ctx: CanvasRenderingContext2D) {
      if (patternType === "line_cross") {
        drawLine(ctx);
      } else if (["zone_intrusion", "loitering", "crowd"].includes(patternType)) {
        drawZone(ctx);
      } else if (["smoking", "weapon"].includes(patternType)) {
        // Optional zone for ML patterns
        const zone = configJson.zone as number[][] | undefined;
        if (zone && zone.length >= 3) {
          drawZone(ctx);
        }
      }
    }

    function drawLine(ctx: CanvasRenderingContext2D) {
      const line = configJson.line as Record<string, number> | undefined;
      if (!line) return;

      // Check if coordinates are normalized (0-1) or pixel
      const isNormalized =
        line.x1 <= 1 && line.y1 <= 1 && line.x2 <= 1 && line.y2 <= 1;
      const x1 = isNormalized ? line.x1 * width : (line.x1 / img.naturalWidth) * width;
      const y1 = isNormalized ? line.y1 * height : (line.y1 / img.naturalHeight) * height;
      const x2 = isNormalized ? line.x2 * width : (line.x2 / img.naturalWidth) * width;
      const y2 = isNormalized ? line.y2 * height : (line.y2 / img.naturalHeight) * height;

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.strokeStyle = "rgba(239, 68, 68, 0.8)";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    function drawZone(ctx: CanvasRenderingContext2D) {
      const zone = configJson.zone as number[][] | undefined;
      if (!zone || zone.length < 3) return;

      ctx.beginPath();
      const [fx, fy] = zone[0];
      // Check if normalized
      const isNormalized = zone.every(([x, y]) => x <= 1 && y <= 1);
      const toX = (x: number) => (isNormalized ? x * width : (x / img.naturalWidth) * width);
      const toY = (y: number) => (isNormalized ? y * height : (y / img.naturalHeight) * height);

      ctx.moveTo(toX(fx), toY(fy));
      for (let i = 1; i < zone.length; i++) {
        ctx.lineTo(toX(zone[i][0]), toY(zone[i][1]));
      }
      ctx.closePath();
      ctx.fillStyle = "rgba(59, 130, 246, 0.2)";
      ctx.fill();
      ctx.strokeStyle = "rgba(59, 130, 246, 0.8)";
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }, [imageUrl, patternType, configJson, width, height]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      className="w-full rounded border border-gray-700"
      style={{ maxWidth: width, aspectRatio: `${width}/${height}` }}
    />
  );
}
