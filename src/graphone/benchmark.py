from dataclasses import dataclass, field
from time import perf_counter


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    elapsed_ms: float
    success: bool


def run_benchmark(name, fn) -> BenchmarkResult:
    start = perf_counter()

    try:
        fn()
        success = True
    except Exception:
        success = False

    elapsed_ms = (perf_counter() - start) * 1000

    return BenchmarkResult(
        name=name,
        elapsed_ms=elapsed_ms,
        success=success,
    )

@dataclass
class BenchmarkSuite:
    results: list[BenchmarkResult] = field(default_factory=list)

    def add(self, name: str, fn) -> BenchmarkResult:
        result = run_benchmark(name, fn)
        self.results.append(result)
        return result

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def successful(self) -> int:
        return sum(result.success for result in self.results)

    @property
    def failed(self) -> int:
        return self.total - self.successful