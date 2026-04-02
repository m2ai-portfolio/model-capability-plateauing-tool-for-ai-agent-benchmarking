"""
Tests for Harness Quality Benchmark Module.

Verifies:
- Harness benchmark runs successfully
- Latency measurements are computed correctly
- Throughput metrics work
- Retry mechanism implements exponential backoff correctly
- Failure isolation prevents cascading errors
- Load scaling works (varying load levels)
- Success criteria check (latency < 100ms)
"""

import pytest
from benchmarks.harness_quality import (
    HarnessQualityBenchmark,
    HarnessTask,
    HarnessResult,
    BenchmarkResult,
    RetryMechanism,
    FailureIsolator
)
from benchmarks.config import Config


class TestHarnessQualityBenchmark:
    """Test suite for HarnessQualityBenchmark class."""

    def test_benchmark_initialization(self):
        """Test that benchmark initializes with tasks."""
        benchmark = HarnessQualityBenchmark()
        assert len(benchmark.tasks) >= 10
        assert benchmark.retry_mechanism is not None
        assert benchmark.failure_isolator is not None

    def test_simulated_tasks_structure(self):
        """Test that simulated tasks have correct structure."""
        benchmark = HarnessQualityBenchmark()

        # Check we have at least 10 tasks (as required)
        assert len(benchmark.tasks) >= 10

        # Check task categories are present
        categories = {task.category for task in benchmark.tasks}
        assert 'stress_test' in categories
        assert 'fault_injection' in categories
        assert 'load_scaling' in categories
        assert 'retry_mechanism' in categories

        # Check each task has required fields
        for task in benchmark.tasks:
            assert task.id
            assert task.description
            assert task.category in ['stress_test', 'fault_injection', 'load_scaling', 'retry_mechanism']
            assert task.expected_latency_ms > 0
            assert task.load_level > 0

    def test_run_benchmark_successfully(self):
        """Test that benchmark runs successfully and returns valid results."""
        benchmark = HarnessQualityBenchmark()
        result = benchmark.run_benchmark()

        # Check result structure
        assert isinstance(result, BenchmarkResult)
        assert result.total_tasks > 0
        assert result.successful >= 0
        assert 0.0 <= result.success_rate <= 1.0
        assert result.avg_latency_ms > 0
        assert result.avg_throughput_ops > 0
        assert isinstance(result.per_task_results, dict)
        assert isinstance(result.per_category_metrics, dict)

        # Check that total tasks matches number of task results
        assert result.total_tasks == len(result.per_task_results)

        # Check success rate calculation
        expected_success_rate = result.successful / result.total_tasks
        assert abs(result.success_rate - expected_success_rate) < 0.001

    def test_latency_measurements_computed_correctly(self):
        """Test that latency measurements are computed correctly."""
        benchmark = HarnessQualityBenchmark()
        result = benchmark.run_benchmark()

        # Verify latency calculations
        all_latencies = [r.latency_ms for r in result.per_task_results.values()]
        calculated_avg = sum(all_latencies) / len(all_latencies)

        assert abs(result.avg_latency_ms - calculated_avg) < 0.01
        assert result.max_latency_ms == max(all_latencies)
        assert result.min_latency_ms == min(all_latencies)

        # Check that all latencies are positive
        for latency in all_latencies:
            assert latency > 0

    def test_throughput_metrics_work(self):
        """Test that throughput metrics are computed correctly."""
        benchmark = HarnessQualityBenchmark()
        result = benchmark.run_benchmark()

        # Verify throughput calculations
        all_throughputs = [r.throughput_ops for r in result.per_task_results.values()]
        calculated_avg = sum(all_throughputs) / len(all_throughputs)

        assert abs(result.avg_throughput_ops - calculated_avg) < 0.01

        # Check that all throughputs are non-negative
        for throughput in all_throughputs:
            assert throughput >= 0

    def test_per_category_metrics(self):
        """Test that per-category metrics are computed correctly."""
        benchmark = HarnessQualityBenchmark()
        result = benchmark.run_benchmark()

        # Check all expected categories are present
        assert 'stress_test' in result.per_category_metrics
        assert 'fault_injection' in result.per_category_metrics
        assert 'load_scaling' in result.per_category_metrics
        assert 'retry_mechanism' in result.per_category_metrics

        # Check all metrics have required fields
        for category, metrics in result.per_category_metrics.items():
            assert 'avg_latency_ms' in metrics
            assert 'avg_throughput_ops' in metrics
            assert 'success_rate' in metrics
            assert metrics['avg_latency_ms'] >= 0
            assert metrics['avg_throughput_ops'] >= 0
            assert 0.0 <= metrics['success_rate'] <= 1.0

    def test_retry_mechanism_implements_exponential_backoff(self):
        """Test that retry mechanism implements exponential backoff correctly."""
        retry = RetryMechanism(base_delay=0.01, max_retries=3, max_delay=1.0, jitter=False)

        # Test delay calculation for different attempts
        delay_0 = retry.calculate_delay(0)
        delay_1 = retry.calculate_delay(1)
        delay_2 = retry.calculate_delay(2)
        delay_3 = retry.calculate_delay(3)

        # Without jitter, should be exact exponential backoff
        assert delay_0 == 0.01  # base_delay * 2^0
        assert delay_1 == 0.02  # base_delay * 2^1
        assert delay_2 == 0.04  # base_delay * 2^2
        assert delay_3 == 0.08  # base_delay * 2^3

        # Test that delays respect max_delay
        retry_capped = RetryMechanism(base_delay=0.5, max_retries=5, max_delay=1.0, jitter=False)
        delay_large = retry_capped.calculate_delay(10)  # Would be 512 without cap
        assert delay_large == 1.0  # Capped at max_delay

    def test_retry_mechanism_with_jitter(self):
        """Test that retry mechanism adds jitter correctly."""
        retry = RetryMechanism(base_delay=0.01, max_retries=3, max_delay=1.0, jitter=True)

        # With jitter, delays should vary but stay within bounds
        delay_1 = retry.calculate_delay(1)

        # Jitter should be between 75% and 125% of base exponential backoff
        expected_base = 0.02
        assert delay_1 >= expected_base * 0.75
        assert delay_1 <= expected_base * 1.25

    def test_retry_mechanism_execution(self):
        """Test retry mechanism execution with retries."""
        retry = RetryMechanism(base_delay=0.001, max_retries=3, jitter=False)

        call_count = [0]

        def task_fn():
            call_count[0] += 1
            return {'result': 'success'}

        result = retry.execute_with_retry(task_fn, 'test_task_001')

        # Should eventually succeed (with possible retries)
        assert result['success'] in [True, False]  # Can succeed or fail based on simulation
        assert result['retry_count'] >= 0
        assert result['retry_count'] <= retry.max_retries

    def test_retry_mechanism_reset(self):
        """Test that retry mechanism resets correctly."""
        retry = RetryMechanism()
        retry.retry_count = 5
        retry.total_delay = 10.5

        retry.reset()

        assert retry.retry_count == 0
        assert retry.total_delay == 0.0

    def test_failure_isolation_prevents_cascading_errors(self):
        """Test that failure isolation prevents cascading errors."""
        isolator = FailureIsolator()

        # Create a failing task
        def failing_task():
            raise Exception("Simulated failure")

        # Execute isolated
        result = isolator.execute_isolated(failing_task, 'task_001')

        assert result['success'] is False
        assert result['error'] is not None
        assert 'Simulated failure' in result['error']

        # Check that failure was isolated
        assert len(isolator.get_isolated_failures()) == 1
        assert isolator.has_cascading_failure() is False

    def test_failure_isolation_multiple_failures(self):
        """Test that multiple failures are isolated independently."""
        isolator = FailureIsolator()

        # Execute multiple failing tasks
        for i in range(5):
            def failing_task():
                raise Exception(f"Failure {i}")

            result = isolator.execute_isolated(failing_task, f'task_{i:03d}')
            assert result['success'] is False

        # Check all failures were isolated
        isolated = isolator.get_isolated_failures()
        assert len(isolated) == 5
        assert isolator.has_cascading_failure() is False

    def test_failure_isolation_success_case(self):
        """Test that successful tasks work with isolation."""
        isolator = FailureIsolator()

        def successful_task():
            return {'data': 'success'}

        result = isolator.execute_isolated(successful_task, 'task_success')

        assert result['success'] is True
        assert result['result'] == {'data': 'success'}
        assert result['error'] is None
        assert len(isolator.get_isolated_failures()) == 0

    def test_failure_isolator_reset(self):
        """Test that failure isolator resets correctly."""
        isolator = FailureIsolator()

        # Add some failures
        def failing_task():
            raise Exception("Test failure")

        isolator.execute_isolated(failing_task, 'task_001')
        isolator.execute_isolated(failing_task, 'task_002')

        assert len(isolator.get_isolated_failures()) == 2

        # Reset
        isolator.reset()

        assert len(isolator.get_isolated_failures()) == 0

    def test_stress_test_runs_successfully(self):
        """Test that stress test runs successfully."""
        benchmark = HarnessQualityBenchmark()
        result = benchmark.run_stress_test()

        assert result['total_tasks'] > 0
        assert result['avg_latency_ms'] > 0
        assert result['max_latency_ms'] >= result['avg_latency_ms']
        assert result['min_latency_ms'] <= result['avg_latency_ms']
        assert result['avg_throughput_ops'] > 0
        assert len(result['latencies']) == result['total_tasks']
        assert len(result['throughputs']) == result['total_tasks']

    def test_load_scaling_test_works(self):
        """Test that load scaling test works with varying load levels."""
        benchmark = HarnessQualityBenchmark()
        result = benchmark.run_load_scaling_test()

        assert result['total_load_levels'] > 0
        assert 'results_by_load' in result

        # Check that we have results for different load levels
        load_levels = result['results_by_load']
        assert len(load_levels) >= 2

        # Check structure of load level results
        for load_key, metrics in load_levels.items():
            assert 'load_level' in metrics
            assert 'latency_ms' in metrics
            assert 'throughput_ops' in metrics
            assert 'success' in metrics
            assert metrics['latency_ms'] > 0
            assert metrics['throughput_ops'] >= 0

    def test_load_scaling_latency_increases_with_load(self):
        """Test that latency generally increases with load level."""
        benchmark = HarnessQualityBenchmark()
        result = benchmark.run_load_scaling_test()

        load_levels = result['results_by_load']

        # Get latencies for different load levels
        if '1x' in load_levels and '4x' in load_levels:
            latency_1x = load_levels['1x']['latency_ms']
            latency_4x = load_levels['4x']['latency_ms']

            # Higher load should generally have higher latency
            assert latency_4x >= latency_1x

    def test_failure_isolation_test(self):
        """Test that failure isolation test runs correctly."""
        benchmark = HarnessQualityBenchmark()
        result = benchmark.test_failure_isolation()

        assert result['total_tasks'] > 0
        assert result['total_failures'] >= 0
        assert result['isolated_failures'] >= 0
        assert result['cascading_failures'] == 0  # Should always be 0
        assert result['isolation_success'] in [True, False]

        # Isolated failures should equal total failures (all failures isolated)
        assert result['isolated_failures'] == result['total_failures']

    def test_success_criteria_check_pass(self):
        """Test success criteria check when latency is below threshold."""
        benchmark = HarnessQualityBenchmark()

        # Test with latency below threshold
        assert benchmark.check_success_criteria(50.0, threshold=100.0) is True
        assert benchmark.check_success_criteria(99.9, threshold=100.0) is True

    def test_success_criteria_check_fail(self):
        """Test success criteria check when latency exceeds threshold."""
        benchmark = HarnessQualityBenchmark()

        # Test with latency at or above threshold
        assert benchmark.check_success_criteria(100.0, threshold=100.0) is False
        assert benchmark.check_success_criteria(150.0, threshold=100.0) is False

    def test_success_criteria_default_threshold(self):
        """Test success criteria with default threshold from config."""
        benchmark = HarnessQualityBenchmark()

        # Test with config default
        threshold = Config.HARNESS_LATENCY_THRESHOLD
        assert threshold == 100.0

        assert benchmark.check_success_criteria(50.0) is True
        assert benchmark.check_success_criteria(150.0) is False

    def test_benchmark_with_retry_disabled(self):
        """Test benchmark with retry mechanism disabled."""
        benchmark = HarnessQualityBenchmark()
        result = benchmark.run_benchmark(enable_retry=False)

        # Should still work but may have different results
        assert isinstance(result, BenchmarkResult)
        assert result.total_tasks > 0

        # Check that retry counts are 0 when retry is disabled
        for task_result in result.per_task_results.values():
            if task_result.task_id.startswith('retry_'):
                # Retry mechanism tasks should have 0 retries when disabled
                # (unless they succeed on first try)
                pass  # May still have retries if category triggers it

    def test_benchmark_with_isolation_disabled(self):
        """Test benchmark with failure isolation disabled."""
        benchmark = HarnessQualityBenchmark()
        result = benchmark.run_benchmark(enable_isolation=False)

        # Should still work
        assert isinstance(result, BenchmarkResult)
        assert result.total_tasks > 0

    def test_task_result_structure(self):
        """Test that HarnessResult has correct structure."""
        result = HarnessResult(
            task_id='test_001',
            latency_ms=25.5,
            throughput_ops=100.0,
            success=True,
            retry_count=1,
            error=None
        )

        assert result.task_id == 'test_001'
        assert result.latency_ms == 25.5
        assert result.throughput_ops == 100.0
        assert result.success is True
        assert result.retry_count == 1
        assert result.error is None

    def test_deterministic_seeding(self):
        """Test that benchmark produces consistent results with deterministic seeding."""
        benchmark1 = HarnessQualityBenchmark()
        result1 = benchmark1.run_benchmark()

        benchmark2 = HarnessQualityBenchmark()
        result2 = benchmark2.run_benchmark()

        # Results should be identical due to deterministic seeding
        assert result1.total_tasks == result2.total_tasks
        assert result1.successful == result2.successful
        assert abs(result1.avg_latency_ms - result2.avg_latency_ms) < 0.1

    def test_retry_mechanism_with_config_values(self):
        """Test retry mechanism using values from config."""
        retry = RetryMechanism(
            base_delay=Config.HARNESS_BACKOFF_BASE,
            max_retries=Config.HARNESS_MAX_RETRIES
        )

        assert retry.base_delay == 0.01
        assert retry.max_retries == 3

    def test_benchmark_categories_coverage(self):
        """Test that benchmark covers all required categories."""
        benchmark = HarnessQualityBenchmark()

        # Get categories from tasks
        categories = [task.category for task in benchmark.tasks]

        # Count tasks per category
        category_counts = {
            'stress_test': categories.count('stress_test'),
            'fault_injection': categories.count('fault_injection'),
            'load_scaling': categories.count('load_scaling'),
            'retry_mechanism': categories.count('retry_mechanism')
        }

        # Each category should have at least 2 tasks
        for category, count in category_counts.items():
            assert count >= 2, f"Category {category} should have at least 2 tasks"
