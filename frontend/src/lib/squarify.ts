// Squarified treemap algorithm (Bruls, Huijsing, van Wijk, 2000).
// Lays out items proportionally by size while keeping aspect ratios close to 1.

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface SizedItem {
  name: string;
  size: number;
}

export interface LaidOutRect extends Rect {
  name: string;
}

interface RowItem {
  name: string;
  area: number;
}

function worst(row: RowItem[], shortestSide: number): number {
  if (row.length === 0) return Infinity;
  const sum = row.reduce((s, r) => s + r.area, 0);
  const max = Math.max(...row.map((r) => r.area));
  const min = Math.min(...row.map((r) => r.area));
  const s2 = shortestSide * shortestSide;
  const sum2 = sum * sum;
  return Math.max((s2 * max) / sum2, sum2 / (s2 * min));
}

function layoutRow(
  row: RowItem[],
  rect: Rect,
): { rects: LaidOutRect[]; remaining: Rect } {
  const sum = row.reduce((s, r) => s + r.area, 0);
  const result: LaidOutRect[] = [];

  if (rect.w >= rect.h) {
    // Lay along the left (vertical) edge: column of width (sum/h), full height.
    const colWidth = sum / rect.h;
    let y = rect.y;
    for (const item of row) {
      const itemHeight = item.area / colWidth;
      result.push({ name: item.name, x: rect.x, y, w: colWidth, h: itemHeight });
      y += itemHeight;
    }
    return {
      rects: result,
      remaining: { x: rect.x + colWidth, y: rect.y, w: rect.w - colWidth, h: rect.h },
    };
  } else {
    // Lay along the top (horizontal) edge: row of height (sum/w), full width.
    const rowHeight = sum / rect.w;
    let x = rect.x;
    for (const item of row) {
      const itemWidth = item.area / rowHeight;
      result.push({ name: item.name, x, y: rect.y, w: itemWidth, h: rowHeight });
      x += itemWidth;
    }
    return {
      rects: result,
      remaining: { x: rect.x, y: rect.y + rowHeight, w: rect.w, h: rect.h - rowHeight },
    };
  }
}

export function squarify(items: SizedItem[], container: Rect): LaidOutRect[] {
  // Sort descending by size and drop zero/negative items.
  const sorted = items
    .filter((it) => it.size > 0)
    .sort((a, b) => b.size - a.size);

  if (sorted.length === 0) return [];

  const totalArea = container.w * container.h;
  const totalSize = sorted.reduce((s, it) => s + it.size, 0);
  if (totalSize <= 0) return [];

  const scale = totalArea / totalSize;
  const scaled: RowItem[] = sorted.map((it) => ({ name: it.name, area: it.size * scale }));

  const result: LaidOutRect[] = [];
  let row: RowItem[] = [];
  let rect: Rect = { ...container };

  for (const item of scaled) {
    const shortestSide = Math.min(rect.w, rect.h);
    const withItem = [...row, item];
    if (row.length === 0 || worst(withItem, shortestSide) <= worst(row, shortestSide)) {
      row = withItem;
    } else {
      const { rects, remaining } = layoutRow(row, rect);
      result.push(...rects);
      rect = remaining;
      row = [item];
    }
  }

  if (row.length > 0) {
    const { rects } = layoutRow(row, rect);
    result.push(...rects);
  }

  return result;
}
