from __future__ import annotations

import asyncio
import json
import os

from google import genai
from google.genai import errors

from graphone.orchestration.contracts import (
    OrchestrationPlan,
    SearchRequest,
)
from graphone.orchestration.planner import (
    Planner,
)


ALLOWED_DATASETS = {
    "startups",
    "products",
    "research_papers",
    "jobs",
    "news",
}


class GeminiPlanner(Planner):
    """
    Gemini-backed orchestration planner for GraphOne.

    Gemini is used ONLY for:

    - understanding the user's request
    - selecting relevant GraphOne datasets
    - producing structured search requests

    Gemini must NOT generate:

    - startup records
    - product records
    - job records
    - news records
    - research paper records
    - companies
    - people
    - URLs
    - external facts

    The actual data must always come from real,
    deterministic source acquisition and retrieval.
    """

    MAX_ATTEMPTS = 5

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-3.6-flash",
    ) -> None:

        resolved_api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
        )

        if not resolved_api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable "
                "is not set"
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
        Call Gemini with application-level retry handling.

        Temporary server failures such as HTTP 503
        are retried using exponential backoff.
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
                        "Gemini planning failed after "
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

    async def create_plan(
        self,
        user_query: str,
    ) -> OrchestrationPlan:
        """
        Convert a user request into a validated search plan.

        Gemini may decide WHAT should be searched,
        but cannot provide the actual data.
        """

        normalized_query = " ".join(
            user_query.split()
        )

        if not normalized_query:
            raise ValueError(
                "user_query must not be empty"
            )

        prompt = f"""
You are the orchestration planner for GraphOne.

Your ONLY responsibility is to determine which existing
GraphOne datasets should be searched.

You are NOT a data source.

You MUST NOT generate, invent, infer, complete, or provide:

- startup records
- companies
- products
- jobs
- job listings
- news articles
- research papers
- people
- URLs
- GitHub repositories
- external facts
- source records

You must ONLY create a search plan.

The available GraphOne datasets are:

- startups
- products
- research_papers
- jobs
- news

Return ONLY valid JSON.

Required format:

{{
  "searches": [
    {{
      "dataset": "startups",
      "query": "search query derived only from the user's request",
      "limit": 20
    }}
  ]
}}

Rules:

1. "dataset" must be exactly one of:
   startups
   products
   research_papers
   jobs
   news

2. Select every dataset that is genuinely relevant
   to the user's request.

3. "query" must be based only on the user's request.

4. Do not introduce company names, product names,
   people, URLs, facts, or entities that the user
   did not provide.

5. "limit" must be an integer between 1 and 50.

6. Do not answer the user's question.

7. Do not provide search results.

8. Do not provide explanations.

9. Do not use Markdown.

10. Return JSON only.

User request:

{normalized_query}
"""

        response = (
            await self._generate_with_retry(
                prompt
            )
        )

        response_text = response.text

        if not response_text:
            raise RuntimeError(
                "Gemini returned an empty response"
            )

        response_text = response_text.strip()

        try:

            payload = json.loads(
                response_text
            )

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                "Gemini returned invalid JSON: "
                f"{response_text}"
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):
            raise ValueError(
                "Gemini plan must be a JSON object"
            )

        raw_searches = payload.get(
            "searches"
        )

        if not isinstance(
            raw_searches,
            list,
        ):
            raise ValueError(
                "Gemini plan must contain "
                "a searches list"
            )

        searches: list[
            SearchRequest
        ] = []

        seen_datasets: set[
            str
        ] = set()

        for raw_search in raw_searches:

            if not isinstance(
                raw_search,
                dict,
            ):
                raise ValueError(
                    "Each search must be "
                    "a JSON object"
                )

            dataset = raw_search.get(
                "dataset"
            )

            query = raw_search.get(
                "query"
            )

            limit = raw_search.get(
                "limit"
            )

            # Deterministic dataset whitelist.
            if (
                not isinstance(
                    dataset,
                    str,
                )
                or dataset
                not in ALLOWED_DATASETS
            ):
                raise ValueError(
                    "Gemini selected an invalid "
                    "dataset: "
                    f"{dataset}"
                )

            # Avoid duplicate searches of the same
            # dataset in a single plan.
            if dataset in seen_datasets:
                continue

            if (
                not isinstance(
                    query,
                    str,
                )
                or not query.strip()
            ):
                raise ValueError(
                    "Search query must be "
                    "a non-empty string"
                )

            normalized_search_query = " ".join(
                query.split()
            )

            if (
                not isinstance(
                    limit,
                    int,
                )
                or isinstance(
                    limit,
                    bool,
                )
                or limit < 1
                or limit > 50
            ):
                raise ValueError(
                    "Search limit must be "
                    "an integer between 1 and 50"
                )

            seen_datasets.add(
                dataset
            )

            searches.append(
                SearchRequest(
                    dataset=dataset,
                    query=normalized_search_query,
                    limit=limit,
                )
            )

        if not searches:
            raise ValueError(
                "Gemini produced no valid "
                "search requests"
            )

        return OrchestrationPlan(
            user_query=normalized_query,
            searches=tuple(
                searches
            ),
        )