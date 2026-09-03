from graphone.benchmark import run_benchmark


def test_benchmark_success():
    result = run_benchmark("test", lambda: None)

    assert result.name == "test"
    assert result.success is True
    assert result.elapsed_ms >= 0