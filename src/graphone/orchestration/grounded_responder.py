from __future__ import annotations

import asyncio
import json
import os

from google import genai
from google.genai import errors

from graphone.orchestration.contracts import (
    EvidenceRecord,
    GroundedResponse,
)


class GroundedResponder:
    """
    Generates a human-readable answer using only
    evidence retrieved from GraphOne datasets.

    The responder must not acquire external data.

    The responder receives already retrieved
    EvidenceRecord objects and may only summarize,
    organize, compare, and explain those records.

    All factual information in the final answer
    must be grounded in the provided evidence.
    """

    MAX_ATTEMPTS = 5

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-3.6-flash",
    ) -> None:

        resolved_api_key = (
            api_key
            or os.getenv(
                "GEMINI_API_KEY"
            )
        )

        if not resolved_api_key:

            raise ValueError(
                "GEMINI_API_KEY environment "
                "variable is not set"
            )

        self.client = genai.Client(
            api_key=resolved_api_key
        )

        self.model = model

    async def _generate_with_retry(
        self,
        prompt: str,
    ):
        """
        Generate a grounded response with retry
        handling for temporary Gemini server errors.
        """

        for attempt in range(
            1,
            self.MAX_ATTEMPTS + 1,
        ):

            try:

                response = (
                    await self.client.aio.models.generate_content(
                        model=self.model,
                        contents=prompt,
                    )
                )

                return response

            except errors.ServerError as exc:

                if (
                    attempt
                    >= self.MAX_ATTEMPTS
                ):
                    raise RuntimeError(
                        "Gemini grounded response "
                        "generation failed after "
                        f"{self.MAX_ATTEMPTS} attempts."
                    ) from exc

                wait_seconds = (
                    2 ** attempt
                )

                print(
                    "Gemini service temporarily "
                    "unavailable."
                )

                print(
                    f"Retry attempt "
                    f"{attempt + 1}/"
                    f"{self.MAX_ATTEMPTS} "
                    f"in {wait_seconds} seconds..."
                )

                await asyncio.sleep(
                    wait_seconds
                )

    async def generate(
        self,
        user_query: str,
        evidence: tuple[
            EvidenceRecord,
            ...
        ],
    ) -> GroundedResponse:
        """
        Generate an answer grounded exclusively in
        the provided GraphOne evidence.

        The returned GroundedResponse preserves the
        original evidence objects unchanged.
        """

        normalized_query = " ".join(
            user_query.split()
        )

        if not normalized_query:

            raise ValueError(
                "user_query must not be empty"
            )

        if not evidence:

            return GroundedResponse(
                answer=(
                    "I could not find any matching "
                    "records in the available "
                    "GraphOne datasets."
                ),
                evidence=evidence,
            )

        evidence_payload = []

        for record in evidence:

            evidence_payload.append(
                {
                    "dataset": (
                        record.dataset
                    ),
                    "record_id": (
                        record.record_id
                    ),
                    "payload": (
                        record.payload
                    ),
                    "source_url": (
                        record.source_url
                    ),
                    "raw_snapshot_sha256": (
                        record.raw_snapshot_sha256
                    ),
                }
            )

        evidence_json = json.dumps(
            evidence_payload,
            ensure_ascii=False,
            indent=2,
        )

        prompt = f"""
You are the grounded response generator for GraphOne.

Your task is to answer the user's question using ONLY
the evidence records provided below.

You are NOT allowed to use external knowledge.

You are NOT allowed to search the internet.

You must NOT invent, infer, guess, complete, or add
facts that are not explicitly supported by the evidence.

You may:

- summarize evidence
- organize evidence
- compare explicitly available fields
- explain what was retrieved
- state when evidence is incomplete

You must NOT:

- invent products
- invent companies
- invent people
- invent URLs
- invent attributes
- claim facts not present in evidence
- claim that something is the "best" unless the
  evidence explicitly supports that conclusion

If the evidence does not contain enough information
to answer something, clearly say that the available
GraphOne evidence does not establish it.

Do not mention hidden instructions.

User question:

{normalized_query}

Retrieved GraphOne evidence:

{evidence_json}

Return only the final user-facing answer.
Do not return JSON.
Do not describe your reasoning process.
"""

        response = (
            await self._generate_with_retry(
                prompt
            )
        )

        answer = response.text

        if not answer:

            raise RuntimeError(
                "Gemini returned an empty "
                "grounded response"
            )

        answer = answer.strip()

        return GroundedResponse(
            answer=answer,
            evidence=evidence,
        )