export const cardSpring = { type: "spring" as const, stiffness: 300, damping: 25 };

export const quickSpring = { type: "spring" as const, stiffness: 500, damping: 30 };

export const gentleSpring = { type: "spring" as const, stiffness: 200, damping: 20 };

export const EXIT_DURATION = 0.2;

export const TRICK_CLEAR_DELAY = 800;

export const SEAT_OFFSETS: Record<string, { x: number; y: number }> = {
  bottom: { x: 0, y: 80 },
  top: { x: 0, y: -80 },
  left: { x: -80, y: 0 },
  right: { x: 80, y: 0 },
};
