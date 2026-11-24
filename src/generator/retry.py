import random
import time
import logging

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

class RetryError(Exception):
    """Все попытки выполнения исчерпаны."""

class RetryPolicy:
    def __init__(
            self,
            max_attempts: int,
            base_delay: float,
            max_delay: float,
            backoff_factor: float = 2.0,
            jitter: float = 0.1,
            retry_on: tuple[type[BaseException], ...] = (Exception,),
            sleep: Callable[[float], None] = time.sleep,
            rng: random.Random | None = None,
    ) -> None:
        #Проверка параметров
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if max_delay < base_delay:
            raise ValueError("max_delay cannot be less than base_delay")
        if backoff_factor < 1:
            raise ValueError("backoff_factor must be >= 1")
        if not 0 <= jitter < 1:
            raise ValueError("jitter must be between 0 and 1")

        #Сохраняем настройки проекта
        self._max_attempts = max_attempts
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._backoff_factor = backoff_factor
        self._jitter = jitter
        self._retry_on = retry_on
        self._sleep = sleep

        #отдельный генератор случайных чисел при jitter
        self._rng = rng if rng is not None else random.Random()

    def execute(self, fn: Callable[[], T]) -> T:
        logger = logging.getLogger(__name__)

        for attempt in range(1, self._max_attempts + 1):
            try:
                return fn()
            except self._retry_on as error:
                logger.warning(
                    "Attempt %d/%d failed: %s",
                    attempt,
                    self._max_attempts,
                    error
                )

                #если попытки закончились - больше не ждем
                if attempt == self._max_attempts:
                    raise RetryError("All retry attempts exhausted") from error

                #Рассчитываем задержку перед следующей попыткой
                delay = self._base_delay * (self._backoff_factor ** (attempt - 1))

                #Ограничиваем максимальную задержку
                delay = min(delay, self._max_delay)

                #Случайное отклонение
                jitter_factor = self._rng.uniform(
                    1 - self._jitter,
                    1 + self._jitter
                )
                delay *= jitter_factor
                self._sleep(delay)
        raise RuntimeError("Unexpected retry state")