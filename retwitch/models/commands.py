from dataclasses import dataclass
import typing
from collections.abc import Callable


@dataclass
class Command:
    name: str
    data: typing.Mapping | None = None
    real_runner: Callable[..., typing.Any] | None = None
