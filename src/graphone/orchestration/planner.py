from __future__ import annotations

from abc import ABC, abstractmethod

from graphone.orchestration.contracts import (
    OrchestrationPlan,
)


class Planner(ABC):
    """
    Abstract interface for an orchestration planner.

    A planner may use an LLM to interpret a user request,
    but its output is restricted to an OrchestrationPlan.

    It must never generate external records, entities,
    news, jobs, products, startups, or research papers.
    """

    @abstractmethod
    async def create_plan(
        self,
        user_query: str,
    ) -> OrchestrationPlan:
        """
        Convert a user request into a structured plan for
        searching existing GraphOne datasets.
        """

        raise NotImplementedError