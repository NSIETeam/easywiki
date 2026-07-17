"""
熔断器 - 外部服务异常时自动降级, 防止连锁故障
"""
import time
import threading
from enum import Enum
from typing import Callable, Dict


class CircuitState(Enum):
    CLOSED = "closed"       # 正常
    OPEN = "open"           # 熔断
    HALF_OPEN = "half_open" # 半开探测


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = 0.0
        self._lock = threading.Lock()

    def call(self, fn: Callable, *args, **kwargs):
        with self._lock:
            if self.state == CircuitState.OPEN:
                if time.monotonic() - self.last_failure_time > self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise CircuitBreakerOpenError(self.name)

        try:
            result = fn(*args, **kwargs)
            with self._lock:
                self.failure_count = 0
                self.state = CircuitState.CLOSED
            return result
        except Exception as e:
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.monotonic()
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
            raise e


class CircuitBreakerOpenError(Exception):
    pass


_breakers: Dict[str, CircuitBreaker] = {}


def get_breaker(name: str) -> CircuitBreaker:
    if name not in _breakers:
        from orgmind.config_production import CIRCUIT_BREAKER_FAILURE_THRESHOLD, CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        _breakers[name] = CircuitBreaker(
            name, CIRCUIT_BREAKER_FAILURE_THRESHOLD, CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
        )
    return _breakers[name]
