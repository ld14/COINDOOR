import { useEffect, useState } from 'react';

type DominantColor = {
  hex: string;
  rgb: [number, number, number];
};

function rgbToHex(r: number, g: number, b: number): string {
  return '#' + [r, g, b].map((c) => c.toString(16).padStart(2, '0')).join('');
}

function quantize(value: number, levels: number): number {
  const step = 256 / levels;
  return Math.floor(value / step) * step + Math.floor(step / 2);
}

function extractColors(image: HTMLImageElement, count: number): DominantColor[] {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  if (!ctx) return [];

  const sampleSize = 64;
  canvas.width = sampleSize;
  canvas.height = sampleSize;
  ctx.drawImage(image, 0, 0, sampleSize, sampleSize);

  const imageData = ctx.getImageData(0, 0, sampleSize, sampleSize);
  const pixels = imageData.data;

  const colorMap = new Map<string, { count: number; r: number; g: number; b: number }>();
  const levels = 8;

  for (let i = 0; i < pixels.length; i += 4) {
    const r = quantize(pixels[i], levels);
    const g = quantize(pixels[i + 1], levels);
    const b = quantize(pixels[i + 2], levels);
    const key = `${r}-${g}-${b}`;

    const existing = colorMap.get(key);
    if (existing) {
      existing.count++;
    } else {
      colorMap.set(key, { count: 1, r, g, b });
    }
  }

  const sorted = Array.from(colorMap.values())
    .sort((a, b) => b.count - a.count)
    .slice(0, count);

  return sorted.map((color) => ({
    hex: rgbToHex(color.r, color.g, color.b),
    rgb: [color.r, color.g, color.b] as [number, number, number],
  }));
}

export function useDominantColors(src: string | undefined, count = 4): {
  colors: DominantColor[];
  loading: boolean;
} {
  const [colors, setColors] = useState<DominantColor[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!src) {
      setColors([]);
      return;
    }

    setLoading(true);
    const img = new Image();
    img.crossOrigin = 'anonymous';

    img.onload = () => {
      try {
        const extracted = extractColors(img, count);
        setColors(extracted);
      } catch {
        setColors([]);
      } finally {
        setLoading(false);
      }
    };

    img.onerror = () => {
      setColors([]);
      setLoading(false);
    };

    img.src = src;
  }, [src, count]);

  return { colors, loading };
}
