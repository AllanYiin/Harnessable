from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .schemas import HarnessEvent


Subscriber = Callable[[HarnessEvent], Any]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: list[Subscriber] = []
        self.events: list[HarnessEvent] = []

    def subscribe(self, subscriber: Subscriber) -> None:
        self._subscribers.append(subscriber)

    def emit(self, event: HarnessEvent) -> None:
        self.events.append(event)
        for subscriber in list(self._subscribers):
            subscriber(event)
