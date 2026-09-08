from __future__ import annotations

from graphone.orchestration.contracts import (
    GroundedResponse,
)
from graphone.orchestration.grounded_responder import (
    GroundedResponder,
)
from graphone.orchestration.planner import (
    Planner,
)
from graphone.orchestration.plan_validator import (
    PlanValidator,
)
from graphone.orchestration.router import (
    DatasetRouter,
)
from graphone.retrieval.evidence_ranker import (
    EvidenceRanker,
)


class GraphOnePipeline:
    """
    End-to-end GraphOne orchestration pipeline.

    User Query
        ↓
    Planner
        ↓
    OrchestrationPlan
        ↓
    PlanValidator
        ↓
    Validated OrchestrationPlan
        ↓
    DatasetRouter
        ↓
    Raw EvidenceRecord objects
        ↓
    EvidenceRanker
        ↓
    Top Relevant EvidenceRecord objects
        ↓
    GroundedResponder
        ↓
    GroundedResponse
    """

    def __init__(
        self,
        planner: Planner,
        validator: PlanValidator,
        router: DatasetRouter,
        ranker: EvidenceRanker,
        responder: GroundedResponder,
        evidence_limit: int = 20,
    ) -> None:

        if (
            not isinstance(
                evidence_limit,
                int,
            )
            or isinstance(
                evidence_limit,
                bool,
            )
            or evidence_limit < 1
        ):
            raise ValueError(
                "evidence_limit must be a "
                "positive integer"
            )

        self.planner = planner
        self.validator = validator
        self.router = router
        self.ranker = ranker
        self.responder = responder
        self.evidence_limit = evidence_limit

    async def run(
        self,
        user_query: str,
    ) -> GroundedResponse:
        """
        Execute the complete GraphOne pipeline.

        The planner proposes searches.

        The validator deterministically validates
        the proposed orchestration plan.

        The router retrieves only real GraphOne
        evidence records.

        The evidence ranker deterministically selects
        the most relevant retrieved records.

        The responder generates an answer grounded
        exclusively in the ranked evidence.
        """

        normalized_query = " ".join(
            user_query.split()
        )

        if not normalized_query:

            raise ValueError(
                "user_query must not be empty"
            )

        plan = (
            await self.planner.create_plan(
                normalized_query
            )
        )

        validated_plan = (
            self.validator.validate(
                plan
            )
        )

        evidence = (
            await self.router.execute(
                validated_plan
            )
        )

        ranked_evidence = (
            self.ranker.rank(
                user_query=normalized_query,
                evidence=evidence,
                limit=self.evidence_limit,
            )
        )

        response = (
            await self.responder.generate(
                user_query=normalized_query,
                evidence=ranked_evidence,
            )
        )

        return response