import pytest

from graphone.orchestration.deterministic_planner import (
    DeterministicPlanner,
)


@pytest.mark.asyncio
async def test_startup_and_job_query_creates_correct_plan():
    planner = DeterministicPlanner()

    plan = await planner.create_plan(
        "Find AI startups that are hiring engineers"
    )

    assert plan.user_query == (
        "Find AI startups that are hiring engineers"
    )

    datasets = [
        search.dataset
        for search in plan.searches
    ]

    assert "startups" in datasets
    assert "jobs" in datasets


@pytest.mark.asyncio
async def test_product_query_creates_product_plan():
    planner = DeterministicPlanner()

    plan = await planner.create_plan(
        "Find products related to renewable energy"
    )

    datasets = [
        search.dataset
        for search in plan.searches
    ]

    assert datasets == ["products"]


@pytest.mark.asyncio
async def test_unknown_query_falls_back_to_all_datasets():
    planner = DeterministicPlanner()

    plan = await planner.create_plan(
        "Find interesting opportunities"
    )

    datasets = [
        search.dataset
        for search in plan.searches
    ]

    assert set(datasets) == {
        "startups",
        "products",
        "research_papers",
        "jobs",
        "news",
    }


@pytest.mark.asyncio
async def test_empty_query_is_rejected():
    planner = DeterministicPlanner()

    with pytest.raises(ValueError):
        await planner.create_plan("   ")