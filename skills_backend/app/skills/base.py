from __future__ import annotations

from abc import ABC, abstractmethod
from app.models import PipelineState


class Skill(ABC):
    name: str = "base"

    @abstractmethod
    def run(self, state: PipelineState) -> PipelineState:
        raise NotImplementedError
