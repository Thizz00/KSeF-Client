import time
from ksef.constants import RATE_LIMIT_WINDOW


class RateLimiter:

    def __init__(self, rate_limit: int):
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.request_count = 0

    def wait_if_needed(self):
        current_time = time.time()

        if self._should_reset_counter(current_time):
            self._reset_counter(current_time)

        if self._limit_reached():
            self._sleep_until_next_window(current_time)

        self.request_count += 1

    def _should_reset_counter(self, current_time: float) -> bool:
        return current_time - self.last_request_time >= RATE_LIMIT_WINDOW

    def _reset_counter(self, current_time: float):
        self.request_count = 0
        self.last_request_time = current_time

    def _limit_reached(self) -> bool:
        return self.request_count >= self.rate_limit

    def _sleep_until_next_window(self, current_time: float):
        sleep_time = RATE_LIMIT_WINDOW - (current_time - self.last_request_time)
        if sleep_time > 0:
            time.sleep(sleep_time)
            self._reset_counter(time.time())
