import asyncio

from graphone.orchestration.gemini_planner import (
    GeminiPlanner,
)


async def main():
    planner = GeminiPlanner()

    user_query = (
        "Find AI startups that are hiring "
        "machine learning engineers"
    )

    print("=" * 80)
    print("GRAPHONE GEMINI ORCHESTRATION TEST")
    print("=" * 80)
    print()

    print("USER QUERY:")
    print(user_query)
    print()

    print("CALLING GEMINI FOR ORCHESTRATION PLAN...")
    print()

    plan = await planner.create_plan(
        user_query
    )

    print("ORCHESTRATION PLAN")
    print("-" * 80)

    print(
        f"Normalized query: "
        f"{plan.user_query}"
    )

    print()
    print("SEARCH REQUESTS:")

    for index, search in enumerate(
        plan.searches,
        start=1,
    ):
        print()

        print(
            f"Search {index}"
        )

        print(
            f"Dataset: "
            f"{search.dataset}"
        )

        print(
            f"Query: "
            f"{search.query}"
        )

        print(
            f"Limit: "
            f"{search.limit}"
        )

    print()
    print("=" * 80)
    print("TEST PASSED")
    print("=" * 80)

    print(
        "Gemini produced a structured "
        "orchestration plan."
    )

    print(
        "No external records were generated "
        "or retrieved in this test."
    )


if __name__ == "__main__":
    asyncio.run(main())