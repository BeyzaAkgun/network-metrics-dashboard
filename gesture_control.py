from collections import deque


class SwipeDetector:
    def __init__(
        self,
        distance_threshold: float = 0.20,
        time_window: float = 0.70,
        cooldown: float = 1.0,
    ) -> None:
        self.distance_threshold = distance_threshold
        self.time_window = time_window
        self.cooldown = cooldown

        self.positions: deque[tuple[float, float, float]] = deque()
        self.last_swipe_time = float("-inf")

    def reset(self) -> None:
        self.positions.clear()

    def update(
        self,
        x: float,
        y: float,
        now: float,
    ) -> str | None:
        if now - self.last_swipe_time < self.cooldown:
            self.reset()
            return None

        self.positions.append((now, x, y))

        while (
            self.positions
            and now - self.positions[0][0] > self.time_window
        ):
            self.positions.popleft()

        if len(self.positions) < 2:
            return None

        start_time, start_x, start_y = self.positions[0]

        elapsed = now - start_time
        dx = x - start_x
        dy = y - start_y

        if elapsed < 0.15:
            return None

        if abs(dx) < self.distance_threshold:
            return None

        if abs(dy) > abs(dx) * 0.60:
            return None

        self.last_swipe_time = now
        self.reset()

        return "right" if dx > 0 else "left"