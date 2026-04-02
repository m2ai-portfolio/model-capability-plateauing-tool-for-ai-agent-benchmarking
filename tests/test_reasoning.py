"""
Tests for Reasoning Benchmark Module.

Verifies:
- Benchmark runs successfully
- Accuracy score is computed correctly
- GSM8K evaluation works
- Ablation reports delta correctly
- Success criteria check (accuracy > 80%)
"""

import pytest
from benchmarks.reasoning import ReasoningBenchmark, ReasoningTask, BenchmarkResult
from benchmarks.config import Config


class TestReasoningBenchmark:
    """Test suite for ReasoningBenchmark class."""

    def test_benchmark_initialization(self):
        """Test that benchmark initializes with tasks."""
        benchmark = ReasoningBenchmark()
        assert len(benchmark.tasks) > 0
        assert benchmark.baseline_accuracy == 0.75

    def test_simulated_tasks_structure(self):
        """Test that simulated tasks have correct structure."""
        benchmark = ReasoningBenchmark()

        # Check we have at least 10 tasks (as required)
        assert len(benchmark.tasks) >= 10

        # Check task categories are present
        categories = {task.category for task in benchmark.tasks}
        assert 'symbolic' in categories
        assert 'planning' in categories
        assert 'math' in categories

        # Check each task has required fields
        for task in benchmark.tasks:
            assert task.id
            assert task.question
            assert task.answer
            assert task.category in ['symbolic', 'planning', 'math']
            assert task.difficulty in ['easy', 'medium', 'hard']
            assert isinstance(task.requires_modules, list)

    def test_run_benchmark_successfully(self):
        """Test that benchmark runs successfully and returns valid results."""
        benchmark = ReasoningBenchmark()
        result = benchmark.run_benchmark()

        # Check result structure
        assert isinstance(result, BenchmarkResult)
        assert result.total_tasks > 0
        assert result.correct >= 0
        assert 0.0 <= result.accuracy <= 1.0
        assert isinstance(result.per_task_results, dict)
        assert isinstance(result.per_category_accuracy, dict)

        # Check that total tasks matches number of task results
        assert result.total_tasks == len(result.per_task_results)

        # Check accuracy calculation
        expected_accuracy = result.correct / result.total_tasks
        assert abs(result.accuracy - expected_accuracy) < 0.001

    def test_accuracy_score_computed_correctly(self):
        """Test that accuracy score computation is correct."""
        benchmark = ReasoningBenchmark()
        result = benchmark.run_benchmark()

        # Manually compute accuracy
        correct_count = sum(result.per_task_results.values())
        total_count = len(result.per_task_results)
        expected_accuracy = correct_count / total_count

        assert result.correct == correct_count
        assert result.total_tasks == total_count
        assert abs(result.accuracy - expected_accuracy) < 0.001

    def test_per_category_accuracy(self):
        """Test that per-category accuracy is computed correctly."""
        benchmark = ReasoningBenchmark()
        result = benchmark.run_benchmark()

        # Check all expected categories are present
        assert 'symbolic' in result.per_category_accuracy
        assert 'planning' in result.per_category_accuracy
        assert 'math' in result.per_category_accuracy

        # Check all values are valid percentages
        for category, accuracy in result.per_category_accuracy.items():
            assert 0.0 <= accuracy <= 1.0

    def test_gsm8k_evaluation_works(self):
        """Test that GSM8K evaluation works correctly."""
        benchmark = ReasoningBenchmark()
        result = benchmark.evaluate_gsm8k_style()

        # Check result structure
        assert isinstance(result, BenchmarkResult)
        assert result.total_tasks > 0  # Should have math tasks
        assert result.correct >= 0
        assert 0.0 <= result.accuracy <= 1.0
        assert result.baseline_comparison is not None

        # Check baseline comparison calculation
        expected_comparison = result.accuracy - benchmark.baseline_accuracy
        assert abs(result.baseline_comparison - expected_comparison) < 0.001

        # Check that only math tasks are included
        math_tasks = [t for t in benchmark.tasks if t.category == 'math']
        assert result.total_tasks == len(math_tasks)

    def test_gsm8k_baseline_comparison(self):
        """Test baseline comparison in GSM8K evaluation."""
        benchmark = ReasoningBenchmark()
        result = benchmark.evaluate_gsm8k_style()

        # Baseline comparison should be the difference
        assert result.baseline_comparison == result.accuracy - benchmark.baseline_accuracy

        # Check if comparison is in reasonable range
        assert -1.0 <= result.baseline_comparison <= 1.0

    def test_ablation_reports_delta_correctly(self):
        """Test that ablation study reports delta correctly."""
        benchmark = ReasoningBenchmark()

        # Test ablation on symbolic_reasoning module
        ablation_result = benchmark.run_ablation('symbolic_reasoning')

        # Check structure
        assert 'module_disabled' in ablation_result
        assert 'baseline_accuracy' in ablation_result
        assert 'ablated_accuracy' in ablation_result
        assert 'delta' in ablation_result
        assert 'baseline_result' in ablation_result
        assert 'ablated_result' in ablation_result

        # Check module name
        assert ablation_result['module_disabled'] == 'symbolic_reasoning'

        # Check delta calculation
        expected_delta = ablation_result['ablated_accuracy'] - ablation_result['baseline_accuracy']
        assert abs(ablation_result['delta'] - expected_delta) < 0.001

        # Check that delta is negative (disabling module should hurt performance)
        assert ablation_result['delta'] < 0

    def test_ablation_all_modules(self):
        """Test ablation on all available modules."""
        benchmark = ReasoningBenchmark()
        modules = Config.ABLATION_MODULES

        for module in modules:
            ablation_result = benchmark.run_ablation(module)

            # Each ablation should have valid structure
            assert ablation_result['module_disabled'] == module
            assert 0.0 <= ablation_result['baseline_accuracy'] <= 1.0
            assert 0.0 <= ablation_result['ablated_accuracy'] <= 1.0
            assert -1.0 <= ablation_result['delta'] <= 1.0

            # Disabling modules should generally decrease accuracy
            # (or at least not increase it significantly)
            assert ablation_result['delta'] <= 0.05

    def test_success_criteria_pass(self):
        """Test success criteria check when accuracy > 80%."""
        benchmark = ReasoningBenchmark()

        # Test with accuracy above threshold
        assert benchmark.check_success_criteria(0.85, 0.80) is True
        assert benchmark.check_success_criteria(0.90, 0.80) is True
        assert benchmark.check_success_criteria(1.00, 0.80) is True

    def test_success_criteria_fail(self):
        """Test success criteria check when accuracy <= 80%."""
        benchmark = ReasoningBenchmark()

        # Test with accuracy at or below threshold
        assert benchmark.check_success_criteria(0.80, 0.80) is False
        assert benchmark.check_success_criteria(0.75, 0.80) is False
        assert benchmark.check_success_criteria(0.50, 0.80) is False

    def test_success_criteria_with_actual_benchmark(self):
        """Test that actual benchmark results meet success criteria."""
        benchmark = ReasoningBenchmark()
        result = benchmark.run_benchmark()

        # Check success criteria
        threshold = Config.REASONING_SUCCESS_THRESHOLD
        success = benchmark.check_success_criteria(result.accuracy, threshold)

        # The benchmark should achieve >80% accuracy
        assert result.accuracy > 0.80, f"Expected accuracy > 80%, got {result.accuracy:.2%}"
        assert success is True, "Success criteria should be met"

    def test_answer_normalization(self):
        """Test answer normalization for comparison."""
        benchmark = ReasoningBenchmark()

        # Test exact matches
        assert benchmark._check_answer("yes", "yes") is True
        assert benchmark._check_answer("Yes", "yes") is True
        assert benchmark._check_answer("YES", "yes") is True

        # Test with punctuation
        assert benchmark._check_answer("yes.", "yes") is True
        assert benchmark._check_answer("yes!", "yes") is True

        # Test numeric answers - exact match
        assert benchmark._check_answer("42", "42") is True
        assert benchmark._check_answer("8", "8") is True

        # Test numeric answers - within tolerance (handled by float conversion)
        # The normalization removes punctuation, so numeric comparison happens
        assert benchmark._check_answer("prepare walls", "prepare walls") is True
        assert benchmark._check_answer("charlie", "charlie") is True

        # Test negative cases
        assert benchmark._check_answer("no", "yes") is False
        assert benchmark._check_answer("43", "42") is False

    def test_deterministic_results(self):
        """Test that benchmark results are deterministic."""
        benchmark1 = ReasoningBenchmark()
        benchmark2 = ReasoningBenchmark()

        result1 = benchmark1.run_benchmark()
        result2 = benchmark2.run_benchmark()

        # Results should be identical
        assert result1.accuracy == result2.accuracy
        assert result1.correct == result2.correct
        assert result1.total_tasks == result2.total_tasks
        assert result1.per_task_results == result2.per_task_results

    def test_ablation_impact_varies_by_module(self):
        """Test that different modules have different impact when disabled."""
        benchmark = ReasoningBenchmark()

        # Get deltas for all modules
        deltas = {}
        for module in Config.ABLATION_MODULES:
            ablation_result = benchmark.run_ablation(module)
            deltas[module] = ablation_result['delta']

        # At least some modules should have measurable impact
        significant_impacts = [delta for delta in deltas.values() if delta < -0.05]
        assert len(significant_impacts) > 0, "At least one module should have significant impact"

    def test_config_integration(self):
        """Test that benchmark integrates with Config correctly."""
        # Check that config values are accessible
        assert Config.REASONING_BASELINE_ACCURACY == 0.75
        assert Config.REASONING_SUCCESS_THRESHOLD == 0.80
        assert len(Config.ABLATION_MODULES) == 3

        # Check that benchmark uses config
        benchmark = ReasoningBenchmark()
        assert benchmark.baseline_accuracy == Config.REASONING_BASELINE_ACCURACY


class TestReasoningTask:
    """Test suite for ReasoningTask dataclass."""

    def test_task_creation(self):
        """Test creating a reasoning task."""
        task = ReasoningTask(
            id="test_001",
            question="Test question?",
            answer="test answer",
            category="symbolic",
            difficulty="easy",
            requires_modules=["symbolic_reasoning"]
        )

        assert task.id == "test_001"
        assert task.question == "Test question?"
        assert task.answer == "test answer"
        assert task.category == "symbolic"
        assert task.difficulty == "easy"
        assert task.requires_modules == ["symbolic_reasoning"]

    def test_task_default_modules(self):
        """Test that requires_modules defaults to empty list."""
        task = ReasoningTask(
            id="test_002",
            question="Test?",
            answer="answer",
            category="math",
            difficulty="medium"
        )

        assert task.requires_modules == []


class TestBenchmarkResult:
    """Test suite for BenchmarkResult dataclass."""

    def test_result_creation(self):
        """Test creating a benchmark result."""
        result = BenchmarkResult(
            total_tasks=10,
            correct=8,
            accuracy=0.8,
            per_task_results={"task1": True, "task2": False},
            per_category_accuracy={"math": 0.85}
        )

        assert result.total_tasks == 10
        assert result.correct == 8
        assert result.accuracy == 0.8
        assert result.per_task_results == {"task1": True, "task2": False}
        assert result.per_category_accuracy == {"math": 0.85}
        assert result.baseline_comparison is None
        assert result.ablation_delta is None

    def test_result_with_optional_fields(self):
        """Test result with baseline comparison and ablation delta."""
        result = BenchmarkResult(
            total_tasks=10,
            correct=8,
            accuracy=0.8,
            per_task_results={},
            per_category_accuracy={},
            baseline_comparison=0.05,
            ablation_delta=-0.10
        )

        assert result.baseline_comparison == 0.05
        assert result.ablation_delta == -0.10
