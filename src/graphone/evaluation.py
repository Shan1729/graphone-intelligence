"""
Evaluation Metric A
Automated scoring engine for the AI Signal Scraping Intelligence project.

Hard gates:
G1 Zero Fact Fabrication
G2 Source Provenance
G3 Freshness Integrity
G4 Volume Minimums
G5 Schema Validity
G6 Ethical Boundary
G7 Failure Safety

Composite scoring:
DQ   = 25
Fresh= 15
Prov = 10
ER   = 10
Rel  = 10
Comp = 10
Scale= 8
Cost = 5
Lat  = 2

NOTE:
The specified weights sum to 95, although the specification calls
the model a 100-point model.

Therefore this evaluator reports:
- raw_score: score out of 95
- normalized_score: equivalent score out of 100
"""

from dataclasses import dataclass
from math import exp
from typing import Dict, Any


TOTAL_WEIGHT = 95.0


@dataclass
class EvaluationInput:
    # Hard-gate metrics
    hallucination_rate: float
    unverified_record_rate: float
    stale_acceptance_rate: float
    schema_validity: float
    ethical_compliance: bool
    failure_safety: bool

    # Volume
    startups: int
    products: int
    papers: int
    news_sources: int
    job_boards: int

    # Data quality
    f1_fields: float
    accuracy_exact_fields: float

    # Freshness
    precision_fresh: float
    recall_fresh: float
    mae_minutes: float

    # Provenance
    supported_extracted_fields: int
    total_extracted_fields: int
    valid_reachable_source_urls: int
    total_records: int

    # Entity resolution
    f1_clustering: float
    false_merge_rate: float
    false_split_rate: float

    # Reliability
    recovery_429: float
    recovery_413: float
    recovery_5xx: float
    corrupted_write_rate: float

    # Completeness
    successfully_extracted_ground_truth: int
    total_ground_truth_records: int

    # Scalability
    scaling_efficiency: float
    throughput_actual: float

    # Cost
    cost_per_1000_records: float

    # Latency
    p95_latency_seconds: float


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def calculate_scores(x: EvaluationInput) -> Dict[str, float]:

    # -------------------------
    # 1. Data Quality
    # -------------------------
    dq = (
        25
        * (
            0.60 * clamp(x.f1_fields)
            + 0.40 * clamp(x.accuracy_exact_fields)
        )
        * (1.0 - clamp(x.hallucination_rate))
    )

    # -------------------------
    # 2. Freshness
    # -------------------------
    fresh = (
        15
        * (
            0.70 * clamp(x.precision_fresh)
            + 0.30 * clamp(x.recall_fresh)
        )
        * exp(-max(0.0, x.mae_minutes) / 180.0)
    )

    # -------------------------
    # 3. Provenance
    # -------------------------
    field_support_ratio = (
        x.supported_extracted_fields / x.total_extracted_fields
        if x.total_extracted_fields > 0
        else 0.0
    )

    source_ratio = (
        x.valid_reachable_source_urls / x.total_records
        if x.total_records > 0
        else 0.0
    )

    prov = 10 * clamp(field_support_ratio) * clamp(source_ratio)

    # -------------------------
    # 4. Entity Resolution
    # -------------------------
    er = (
        10
        * max(
            0.0,
            clamp(x.f1_clustering)
            - 1.5 * clamp(x.false_merge_rate)
            - 0.5 * clamp(x.false_split_rate),
        )
    )

    # -------------------------
    # 5. Reliability
    # -------------------------
    rel = (
        10
        * (
            0.40 * clamp(x.recovery_429)
            + 0.40 * clamp(x.recovery_413)
            + 0.20 * clamp(x.recovery_5xx)
        )
        * (1.0 - clamp(x.corrupted_write_rate))
    )

    # -------------------------
    # 6. Completeness
    # -------------------------
    comp = (
        10
        * clamp(
            x.successfully_extracted_ground_truth
            / x.total_ground_truth_records
            if x.total_ground_truth_records > 0
            else 0.0
        )
    )

    # -------------------------
    # 7. Scalability
    # -------------------------
    scale = (
        8
        * clamp(x.scaling_efficiency)
        * min(1.0, max(0.0, x.throughput_actual / 400.0))
    )

    # -------------------------
    # 8. Cost
    # -------------------------
    cost = 5 * max(
        0.0,
        1.0 - (x.cost_per_1000_records / 2.0),
    )

    # -------------------------
    # 9. Latency
    # -------------------------
    latency = 2 * max(
        0.0,
        1.0 - (x.p95_latency_seconds / 12.0),
    )

    raw_score = (
        dq
        + fresh
        + prov
        + er
        + rel
        + comp
        + scale
        + cost
        + latency
    )

    normalized_score = raw_score / TOTAL_WEIGHT * 100.0

    return {
        "data_quality": dq,
        "freshness": fresh,
        "provenance": prov,
        "entity_resolution": er,
        "reliability": rel,
        "completeness": comp,
        "scalability": scale,
        "cost": cost,
        "latency": latency,
        "raw_score": raw_score,
        "normalized_score": normalized_score,
    }


def check_hard_gates(x: EvaluationInput) -> Dict[str, Any]:

    gates = {
        "G1_zero_fact_fabrication":
            x.hallucination_rate == 0.0,

        "G2_source_provenance":
            x.unverified_record_rate == 0.0,

        "G3_freshness_integrity":
            x.stale_acceptance_rate == 0.0,

        "G4_volume_minimums":
            (
                x.startups >= 1000
                and x.products >= 1000
                and x.papers >= 1000
                and x.news_sources >= 5
                and x.job_boards >= 5
            ),

        "G5_schema_validity":
            x.schema_validity == 1.0,

        "G6_ethical_boundary":
            x.ethical_compliance,

        "G7_failure_safety":
            x.failure_safety,
    }

    passed = all(gates.values())

    return {
        "passed": passed,
        "gates": gates,
    }


def evaluate(x: EvaluationInput) -> Dict[str, Any]:

    gate_result = check_hard_gates(x)

    # Hard-gate failure means final score is zero.
    if not gate_result["passed"]:
        return {
            "passed_hard_gates": False,
            "score": 0.0,
            "raw_score": 0.0,
            "normalized_score": 0.0,
            "hard_gates": gate_result,
            "components": {},
            "status": "FAIL",
        }

    scores = calculate_scores(x)

    return {
        "passed_hard_gates": True,
        "score": scores["normalized_score"],
        "raw_score": scores["raw_score"],
        "normalized_score": scores["normalized_score"],
        "hard_gates": gate_result,
        "components": {
            key: value
            for key, value in scores.items()
            if key not in ("raw_score", "normalized_score")
        },
        "status": "PASS",
    }


if __name__ == "__main__":
    print("Evaluation Metric A")
    print("===================")
    print("Automated scoring engine loaded successfully.")
    print(f"Specified component weights: {TOTAL_WEIGHT}/100")