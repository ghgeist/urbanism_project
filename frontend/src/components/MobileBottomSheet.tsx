/**
 * Map-first bottom sheet for the mobile Explore page.
 * Three snap points: peek (just the handle + summary teaser visible),
 * half (~50vh), and full (everything but the sticky search bar).
 *
 * Drag the handle to resize; release snaps to the nearest point.
 * When at "full", inner content scrolls. When dragging starts on the
 * handle, body scroll is suppressed via pointer capture.
 */

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

export type SheetSnap = "peek" | "half" | "full";

interface MobileBottomSheetProps {
  children: ReactNode;
  /** Initial snap point. Defaults to "peek". */
  initialSnap?: SheetSnap;
  /** Optional label for the handle button (a11y). */
  ariaLabel?: string;
}

/** Snap-point heights as a fraction of the viewport height. */
const SNAP_FRACTIONS: Record<SheetSnap, number> = {
  peek: 0.18,
  half: 0.5,
  full: 0.88,
};

const SNAP_ORDER: SheetSnap[] = ["peek", "half", "full"];

function pickNearestSnap(heightPx: number, viewportPx: number): SheetSnap {
  const frac = heightPx / Math.max(1, viewportPx);
  let best: SheetSnap = "peek";
  let bestDist = Infinity;
  for (const snap of SNAP_ORDER) {
    const d = Math.abs(frac - SNAP_FRACTIONS[snap]);
    if (d < bestDist) {
      bestDist = d;
      best = snap;
    }
  }
  return best;
}

export function MobileBottomSheet({
  children,
  initialSnap = "peek",
  ariaLabel = "Results panel",
}: MobileBottomSheetProps) {
  const [snap, setSnap] = useState<SheetSnap>(initialSnap);
  const [dragHeightPx, setDragHeightPx] = useState<number | null>(null);
  const dragRef = useRef<{ startY: number; startHeight: number; pointerId: number; didMove: boolean } | null>(null);
  /** Set true at the end of a drag so the synthetic click that fires after
   *  pointerup doesn't also cycle the snap. Reset on the next click. */
  const suppressNextClickRef = useRef(false);
  const sheetRef = useRef<HTMLDivElement>(null);

  const viewportHeight = () =>
    typeof window === "undefined" ? 800 : window.innerHeight;

  const targetHeightPx =
    dragHeightPx !== null ? dragHeightPx : viewportHeight() * SNAP_FRACTIONS[snap];

  const onPointerDown = useCallback((e: React.PointerEvent<HTMLButtonElement>) => {
    const rect = sheetRef.current?.getBoundingClientRect();
    if (!rect) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    dragRef.current = {
      startY: e.clientY,
      startHeight: rect.height,
      pointerId: e.pointerId,
      didMove: false,
    };
    setDragHeightPx(rect.height);
  }, []);

  /** Pixel threshold above which a pointer movement is treated as a drag
   *  (and therefore should NOT also cycle the snap on click release). */
  const DRAG_THRESHOLD_PX = 4;

  const onPointerMove = useCallback((e: React.PointerEvent<HTMLButtonElement>) => {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== e.pointerId) return;
    const delta = drag.startY - e.clientY;  // positive when dragging up = grow sheet
    if (Math.abs(delta) > DRAG_THRESHOLD_PX) drag.didMove = true;
    const vh = viewportHeight();
    const next = Math.max(80, Math.min(vh * 0.95, drag.startHeight + delta));
    setDragHeightPx(next);
  }, []);

  const endDrag = useCallback((e: React.PointerEvent<HTMLButtonElement>) => {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== e.pointerId) return;
    if (e.currentTarget.hasPointerCapture(e.pointerId)) {
      e.currentTarget.releasePointerCapture(e.pointerId);
    }
    const finalHeight = dragHeightPx ?? drag.startHeight;
    const didMove = drag.didMove;
    dragRef.current = null;
    setDragHeightPx(null);
    if (didMove) {
      // Real drag: snap to nearest, and swallow the synthetic click that
      // fires next so it doesn't override the snap by cycling.
      suppressNextClickRef.current = true;
      setSnap(pickNearestSnap(finalHeight, viewportHeight()));
    }
    // If !didMove, leave snap alone — the click handler will cycle.
  }, [dragHeightPx]);

  const onClick = useCallback(() => {
    if (suppressNextClickRef.current) {
      suppressNextClickRef.current = false;
      return;
    }
    const order: SheetSnap[] = ["peek", "half", "full"];
    setSnap((prev) => order[(order.indexOf(prev) + 1) % order.length]);
  }, []);

  // Keep snap height in sync with viewport size changes (rotate, etc.).
  useEffect(() => {
    if (typeof window === "undefined") return;
    const handler = () => {
      // Recompute via state nudge only when not dragging.
      if (dragRef.current === null) setDragHeightPx(null);
    };
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);

  return (
    <div
      ref={sheetRef}
      className={`mobile-sheet mobile-sheet--${snap}`}
      style={{ height: `${Math.round(targetHeightPx)}px` }}
      role="dialog"
      aria-label={ariaLabel}
    >
      <button
        type="button"
        className="mobile-sheet__handle"
        aria-label={`Drag to resize. Currently ${snap}. Tap to cycle.`}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
        onClick={onClick}
      >
        <span className="mobile-sheet__grabber" aria-hidden />
      </button>
      <div className="mobile-sheet__content">{children}</div>
    </div>
  );
}
