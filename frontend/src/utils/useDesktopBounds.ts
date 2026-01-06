import { useEffect, useRef, useState } from "react";
import type { Rect } from "./windowUtils";

export const useDesktopBounds = () => {
  const ref = useRef<HTMLDivElement | null>(null);
  const [bounds, setBounds] = useState<Rect>({ x: 0, y: 0, width: 0, height: 0 });

  useEffect(() => {
    if (!ref.current) {
      return;
    }
    const element = ref.current;
    const update = () => {
      const rect = element.getBoundingClientRect();
      setBounds({ x: 0, y: 0, width: rect.width, height: rect.height });
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return { ref, bounds } as const;
};
