import { useCallback, useEffect, useRef, useState } from "react";

interface ZoneEditorProps {
  imageUrl: string;
  mode: "polygon" | "line";
  initialData?: number[][];
  onChange: (coords: number[][]) => void;
  width?: number;
  height?: number;
}

const POINT_RADIUS = 6;
const POINT_HIT_RADIUS = 12;

export function ZoneEditor({
  imageUrl,
  mode,
  initialData,
  onChange,
  width = 640,
  height = 480,
}: ZoneEditorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement | null>(null);
  const [points, setPoints] = useState<number[][]>(initialData || []);
  const [dragging, setDragging] = useState<number | null>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imgSize, setImgSize] = useState({ w: width, h: height });

  // Load image
  useEffect(() => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      imgRef.current = img;
      setImgSize({ w: img.naturalWidth, h: img.naturalHeight });
      setImageLoaded(true);
    };
    img.onerror = () => {
      imgRef.current = null;
      setImageLoaded(true);
    };
    img.src = imageUrl;
  }, [imageUrl]);

  // Convert normalized coords to canvas coords
  const toCanvas = useCallback(
    (nx: number, ny: number): [number, number] => [nx * width, ny * height],
    [width, height]
  );

  // Convert canvas coords to normalized coords
  const toNormalized = useCallback(
    (cx: number, cy: number): [number, number] => [
      Math.max(0, Math.min(1, cx / width)),
      Math.max(0, Math.min(1, cy / height)),
    ],
    [width, height]
  );

  // Draw on canvas
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    // Draw image
    if (imgRef.current) {
      ctx.drawImage(imgRef.current, 0, 0, width, height);
    } else {
      ctx.fillStyle = "#1a1a2e";
      ctx.fillRect(0, 0, width, height);
      ctx.fillStyle = "#666";
      ctx.font = "14px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("No snapshot available", width / 2, height / 2);
    }

    if (points.length === 0) return;

    const canvasPoints = points.map(([x, y]) => toCanvas(x, y));

    if (mode === "polygon") {
      // Draw filled polygon with transparency
      ctx.beginPath();
      ctx.moveTo(canvasPoints[0][0], canvasPoints[0][1]);
      for (let i = 1; i < canvasPoints.length; i++) {
        ctx.lineTo(canvasPoints[i][0], canvasPoints[i][1]);
      }
      ctx.closePath();
      ctx.fillStyle = "rgba(59, 130, 246, 0.2)";
      ctx.fill();
      ctx.strokeStyle = "rgba(59, 130, 246, 0.8)";
      ctx.lineWidth = 2;
      ctx.stroke();
    } else {
      // Draw line with direction arrow
      if (canvasPoints.length >= 2) {
        ctx.beginPath();
        ctx.moveTo(canvasPoints[0][0], canvasPoints[0][1]);
        ctx.lineTo(canvasPoints[1][0], canvasPoints[1][1]);
        ctx.strokeStyle = "rgba(239, 68, 68, 0.8)";
        ctx.lineWidth = 3;
        ctx.stroke();

        // Direction arrow at midpoint
        const mx = (canvasPoints[0][0] + canvasPoints[1][0]) / 2;
        const my = (canvasPoints[0][1] + canvasPoints[1][1]) / 2;
        const angle = Math.atan2(
          canvasPoints[1][1] - canvasPoints[0][1],
          canvasPoints[1][0] - canvasPoints[0][0]
        );
        const arrowLen = 12;
        ctx.beginPath();
        ctx.moveTo(mx, my);
        ctx.lineTo(
          mx - arrowLen * Math.cos(angle - Math.PI / 6),
          my - arrowLen * Math.sin(angle - Math.PI / 6)
        );
        ctx.moveTo(mx, my);
        ctx.lineTo(
          mx - arrowLen * Math.cos(angle + Math.PI / 6),
          my - arrowLen * Math.sin(angle + Math.PI / 6)
        );
        ctx.strokeStyle = "rgba(239, 68, 68, 0.8)";
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    }

    // Draw points
    for (let i = 0; i < canvasPoints.length; i++) {
      ctx.beginPath();
      ctx.arc(canvasPoints[i][0], canvasPoints[i][1], POINT_RADIUS, 0, Math.PI * 2);
      ctx.fillStyle = i === dragging ? "#fbbf24" : "#3b82f6";
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }, [points, width, height, mode, toCanvas, dragging]);

  useEffect(() => {
    draw();
  }, [draw, imageLoaded]);

  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>): [number, number] => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    const scaleX = width / rect.width;
    const scaleY = height / rect.height;
    return [
      (e.clientX - rect.left) * scaleX,
      (e.clientY - rect.top) * scaleY,
    ];
  };

  const findPoint = (cx: number, cy: number): number | null => {
    for (let i = 0; i < points.length; i++) {
      const [px, py] = toCanvas(points[i][0], points[i][1]);
      const dist = Math.hypot(cx - px, cy - py);
      if (dist <= POINT_HIT_RADIUS) return i;
    }
    return null;
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const [cx, cy] = getCanvasCoords(e);
    const idx = findPoint(cx, cy);

    if (idx !== null) {
      setDragging(idx);
      return;
    }

    // For line mode, only allow 2 points
    if (mode === "line" && points.length >= 2) return;

    const [nx, ny] = toNormalized(cx, cy);
    const newPoints = [...points, [nx, ny]];
    setPoints(newPoints);
    onChange(newPoints);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (dragging === null) return;
    const [cx, cy] = getCanvasCoords(e);
    const [nx, ny] = toNormalized(cx, cy);
    const newPoints = [...points];
    newPoints[dragging] = [nx, ny];
    setPoints(newPoints);
    onChange(newPoints);
  };

  const handleMouseUp = () => {
    setDragging(null);
  };

  const handleDoubleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const [cx, cy] = getCanvasCoords(e);
    const idx = findPoint(cx, cy);

    if (idx !== null) {
      // Remove point on double-click
      const newPoints = points.filter((_, i) => i !== idx);
      setPoints(newPoints);
      onChange(newPoints);
    }
  };

  const handleClear = () => {
    setPoints([]);
    onChange([]);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-300">
          {mode === "polygon" ? "Draw Zone (click to add points)" : "Draw Line (click two points)"}
        </span>
        <button
          type="button"
          onClick={handleClear}
          className="text-xs text-red-400 hover:text-red-300"
        >
          Clear
        </button>
      </div>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="w-full cursor-crosshair rounded border border-gray-700"
        style={{ maxWidth: width, aspectRatio: `${width}/${height}` }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onDoubleClick={handleDoubleClick}
      />
      <p className="text-xs text-gray-500">
        {mode === "polygon"
          ? "Click to add vertices. Double-click a point to remove it. Drag to reposition."
          : "Click to place start and end points. Double-click a point to remove it. Drag to reposition."}
      </p>
    </div>
  );
}
