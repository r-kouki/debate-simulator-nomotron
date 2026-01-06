export type Rect = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export const clampRectToBounds = (rect: Rect, bounds: Rect): Rect => {
  const maxX = bounds.width - rect.width;
  const maxY = bounds.height - rect.height;
  return {
    x: Math.min(Math.max(rect.x, 0), Math.max(maxX, 0)),
    y: Math.min(Math.max(rect.y, 0), Math.max(maxY, 0)),
    width: rect.width,
    height: rect.height
  };
};

export const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
};
