"""
CLI interface for Model Capability Plateauing Tool.

Provides commands for running benchmarks and viewing results.
"""

import click
import json
from benchmarks.reasoning import ReasoningBenchmark
from benchmarks.tool_use import ToolUseBenchmark
from benchmarks.harness_quality import HarnessQualityBenchmark
from benchmarks.config import Config


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Model Capability Plateauing Tool - AI Agent Benchmarking Suite."""
    pass


@cli.command()
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed per-task results')
def reasoning(format, verbose):
    """Run the reasoning benchmark suite and record accuracy score."""
    click.echo("Running Reasoning Benchmark Suite...")
    click.echo("=" * 60)

    benchmark = ReasoningBenchmark()
    result = benchmark.run_benchmark()

    if format == 'json':
        output = {
            'total_tasks': result.total_tasks,
            'correct': result.correct,
            'accuracy': result.accuracy,
            'per_category_accuracy': result.per_category_accuracy,
            'success_criteria_met': benchmark.check_success_criteria(result.accuracy)
        }
        if verbose:
            output['per_task_results'] = result.per_task_results
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"\nTotal Tasks: {result.total_tasks}")
        click.echo(f"Correct: {result.correct}")
        click.echo(f"Accuracy: {result.accuracy:.2%}")
        click.echo(f"\nPer-Category Accuracy:")
        for category, acc in result.per_category_accuracy.items():
            click.echo(f"  {category.capitalize()}: {acc:.2%}")

        threshold = Config.REASONING_SUCCESS_THRESHOLD
        success = benchmark.check_success_criteria(result.accuracy, threshold)
        click.echo(f"\nSuccess Criteria (>{threshold:.0%}): {'✓ PASS' if success else '✗ FAIL'}")

        if verbose:
            click.echo(f"\nPer-Task Results:")
            for task_id, correct in result.per_task_results.items():
                status = "✓" if correct else "✗"
                click.echo(f"  {status} {task_id}")

    click.echo("\n" + "=" * 60)


@cli.command()
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
def gsm8k(format):
    """Evaluate on GSM8K-style reasoning tasks and compare to baseline."""
    click.echo("Evaluating GSM8K-Style Reasoning Tasks...")
    click.echo("=" * 60)

    benchmark = ReasoningBenchmark()
    result = benchmark.evaluate_gsm8k_style()

    if format == 'json':
        output = {
            'total_tasks': result.total_tasks,
            'correct': result.correct,
            'accuracy': result.accuracy,
            'baseline_accuracy': benchmark.baseline_accuracy,
            'baseline_comparison': result.baseline_comparison,
            'improvement': result.baseline_comparison > 0
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"\nTotal GSM8K-style Tasks: {result.total_tasks}")
        click.echo(f"Correct: {result.correct}")
        click.echo(f"Accuracy: {result.accuracy:.2%}")
        click.echo(f"Baseline: {benchmark.baseline_accuracy:.2%}")
        click.echo(f"Comparison: {result.baseline_comparison:+.2%}")

        if result.baseline_comparison > 0:
            click.echo(f"\n✓ Performance ABOVE baseline by {result.baseline_comparison:.2%}")
        elif result.baseline_comparison < 0:
            click.echo(f"\n✗ Performance BELOW baseline by {abs(result.baseline_comparison):.2%}")
        else:
            click.echo(f"\n= Performance MATCHES baseline")

    click.echo("\n" + "=" * 60)


@cli.command()
@click.option('--module', type=click.Choice(['symbolic_reasoning', 'planning', 'multi_step']),
              required=True, help='Module to disable for ablation')
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
def ablation(module, format):
    """Perform ablation on reasoning modules and report delta."""
    click.echo(f"Running Ablation Study: Disabling '{module}' module...")
    click.echo("=" * 60)

    benchmark = ReasoningBenchmark()
    ablation_result = benchmark.run_ablation(module)

    if format == 'json':
        output = {
            'module_disabled': ablation_result['module_disabled'],
            'baseline_accuracy': ablation_result['baseline_accuracy'],
            'ablated_accuracy': ablation_result['ablated_accuracy'],
            'delta': ablation_result['delta'],
            'performance_impact': 'negative' if ablation_result['delta'] < 0 else 'neutral/positive'
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"\nModule Disabled: {ablation_result['module_disabled']}")
        click.echo(f"Baseline Accuracy (all modules): {ablation_result['baseline_accuracy']:.2%}")
        click.echo(f"Ablated Accuracy (module off): {ablation_result['ablated_accuracy']:.2%}")
        click.echo(f"Delta: {ablation_result['delta']:+.2%}")

        if ablation_result['delta'] < 0:
            impact = abs(ablation_result['delta'])
            click.echo(f"\n⚠ Module '{module}' contributes {impact:.2%} to overall accuracy")
        else:
            click.echo(f"\nℹ Module '{module}' has minimal/no impact on accuracy")

    click.echo("\n" + "=" * 60)


@cli.command()
def benchmark_all():
    """Run all benchmarks and display comprehensive results."""
    click.echo("=" * 60)
    click.echo("COMPREHENSIVE BENCHMARK SUITE")
    click.echo("=" * 60)

    benchmark = ReasoningBenchmark()

    # 1. Full reasoning benchmark
    click.echo("\n1. REASONING BENCHMARK")
    click.echo("-" * 60)
    result = benchmark.run_benchmark()
    click.echo(f"Accuracy: {result.accuracy:.2%}")
    click.echo(f"Tasks: {result.correct}/{result.total_tasks} correct")
    for category, acc in result.per_category_accuracy.items():
        click.echo(f"  {category.capitalize()}: {acc:.2%}")

    # 2. GSM8K evaluation
    click.echo("\n2. GSM8K EVALUATION")
    click.echo("-" * 60)
    gsm8k_result = benchmark.evaluate_gsm8k_style()
    click.echo(f"Accuracy: {gsm8k_result.accuracy:.2%}")
    click.echo(f"Baseline: {benchmark.baseline_accuracy:.2%}")
    click.echo(f"Delta: {gsm8k_result.baseline_comparison:+.2%}")

    # 3. Ablation studies
    click.echo("\n3. ABLATION STUDIES")
    click.echo("-" * 60)
    modules = Config.ABLATION_MODULES
    for module in modules:
        ablation_result = benchmark.run_ablation(module)
        delta = ablation_result['delta']
        click.echo(f"  {module}: {delta:+.2%}")

    # 4. Success criteria
    click.echo("\n4. SUCCESS CRITERIA")
    click.echo("-" * 60)
    threshold = Config.REASONING_SUCCESS_THRESHOLD
    success = benchmark.check_success_criteria(result.accuracy, threshold)
    click.echo(f"Threshold: >{threshold:.0%}")
    click.echo(f"Result: {'✓ PASS' if success else '✗ FAIL'} ({result.accuracy:.2%})")

    click.echo("\n" + "=" * 60)


@cli.command()
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed per-task results')
def tool_use(format, verbose):
    """Run the tool use benchmark suite and record success rate."""
    click.echo("Running Tool Use Benchmark Suite...")
    click.echo("=" * 60)

    benchmark = ToolUseBenchmark()
    result = benchmark.run_benchmark()

    if format == 'json':
        output = {
            'total_tasks': result.total_tasks,
            'successful': result.successful,
            'success_rate': result.success_rate,
            'per_category_success': result.per_category_success,
            'success_criteria_met': benchmark.check_success_criteria(result.success_rate)
        }
        if verbose:
            output['per_task_results'] = result.per_task_results
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"\nTotal Tasks: {result.total_tasks}")
        click.echo(f"Successful: {result.successful}")
        click.echo(f"Success Rate: {result.success_rate:.2%}")
        click.echo(f"\nPer-Category Success Rate:")
        for category, rate in result.per_category_success.items():
            click.echo(f"  {category.replace('_', ' ').title()}: {rate:.2%}")

        threshold = Config.TOOL_USE_BASELINE_SUCCESS_RATE
        success = benchmark.check_success_criteria(result.success_rate, threshold)
        click.echo(f"\nSuccess Criteria (>{threshold:.0%}): {'✓ PASS' if success else '✗ FAIL'}")

        if verbose:
            click.echo(f"\nPer-Task Results:")
            for task_id, succeeded in result.per_task_results.items():
                status = "✓" if succeeded else "✗"
                click.echo(f"  {status} {task_id}")

    click.echo("\n" + "=" * 60)


@cli.command()
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed test results')
def mock_api(format, verbose):
    """Test mock API interactions and validate tool calling mechanisms."""
    click.echo("Testing Mock API Interactions...")
    click.echo("=" * 60)

    benchmark = ToolUseBenchmark()
    test_results = benchmark.test_mock_api()

    if format == 'json':
        click.echo(json.dumps(test_results, indent=2))
    else:
        click.echo("\nMock API Test Results:")
        for test_name, passed in test_results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            test_label = test_name.replace('_', ' ').title()
            click.echo(f"  {status}: {test_label}")

        all_passed = all(test_results.values())
        click.echo(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")

        if verbose:
            click.echo("\nTest Descriptions:")
            click.echo("  - Tool Registration: All tools registered correctly")
            click.echo("  - Simple Call: Basic API call execution works")
            click.echo("  - State Persistence: State maintained across calls")
            click.echo("  - Parameter Validation: Missing parameters detected")
            click.echo("  - Safety Enforcement: Restricted tools blocked")

    click.echo("\n" + "=" * 60)


@cli.command()
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed failure analysis')
def failure_test(format, verbose):
    """Run failure injection tests to verify graceful handling."""
    click.echo("Running Failure Injection Tests...")
    click.echo("=" * 60)

    benchmark = ToolUseBenchmark()
    failure_results = benchmark.run_failure_injection_test()

    if format == 'json':
        output = {
            'normal_success_rate': failure_results['normal_success_rate'],
            'failure_mode_success_rate': failure_results['failure_mode_success_rate'],
            'resilience_score': failure_results['resilience_score'],
            'graceful_degradation': failure_results['graceful_degradation']
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"\nNormal Mode Success Rate: {failure_results['normal_success_rate']:.2%}")
        click.echo(f"Failure Mode Success Rate: {failure_results['failure_mode_success_rate']:.2%}")
        click.echo(f"Resilience Score: {failure_results['resilience_score']:.2%}")

        if failure_results['graceful_degradation']:
            click.echo(f"\n✓ Graceful Degradation: System maintains >50% success under failures")
        else:
            click.echo(f"\n✗ Graceful Degradation: System drops below 50% success under failures")

        if verbose:
            click.echo("\nDetailed Analysis:")
            normal = failure_results['normal_result']
            failure = failure_results['failure_result']

            click.echo("\n  Normal Mode - Per Category:")
            for category, rate in normal.per_category_success.items():
                click.echo(f"    {category.replace('_', ' ').title()}: {rate:.2%}")

            click.echo("\n  Failure Mode - Per Category:")
            for category, rate in failure.per_category_success.items():
                click.echo(f"    {category.replace('_', ' ').title()}: {rate:.2%}")

    click.echo("\n" + "=" * 60)


@cli.command()
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed per-task results')
def harness(format, verbose):
    """Run the harness quality benchmark suite and record metrics."""
    click.echo("Running Harness Quality Benchmark Suite...")
    click.echo("=" * 60)

    benchmark = HarnessQualityBenchmark()
    result = benchmark.run_benchmark()

    if format == 'json':
        output = {
            'total_tasks': result.total_tasks,
            'successful': result.successful,
            'success_rate': result.success_rate,
            'avg_latency_ms': result.avg_latency_ms,
            'max_latency_ms': result.max_latency_ms,
            'min_latency_ms': result.min_latency_ms,
            'avg_throughput_ops': result.avg_throughput_ops,
            'per_category_metrics': result.per_category_metrics,
            'success_criteria_met': benchmark.check_success_criteria(result.avg_latency_ms)
        }
        if verbose:
            output['per_task_results'] = {
                task_id: {
                    'latency_ms': r.latency_ms,
                    'throughput_ops': r.throughput_ops,
                    'success': r.success,
                    'retry_count': r.retry_count
                }
                for task_id, r in result.per_task_results.items()
            }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"\nTotal Tasks: {result.total_tasks}")
        click.echo(f"Successful: {result.successful}")
        click.echo(f"Success Rate: {result.success_rate:.2%}")
        click.echo(f"\nLatency Metrics:")
        click.echo(f"  Average: {result.avg_latency_ms:.2f}ms")
        click.echo(f"  Maximum: {result.max_latency_ms:.2f}ms")
        click.echo(f"  Minimum: {result.min_latency_ms:.2f}ms")
        click.echo(f"\nThroughput: {result.avg_throughput_ops:.2f} ops/sec")

        click.echo(f"\nPer-Category Metrics:")
        for category, metrics in result.per_category_metrics.items():
            click.echo(f"  {category.replace('_', ' ').title()}:")
            click.echo(f"    Latency: {metrics['avg_latency_ms']:.2f}ms")
            click.echo(f"    Throughput: {metrics['avg_throughput_ops']:.2f} ops/sec")
            click.echo(f"    Success Rate: {metrics['success_rate']:.2%}")

        threshold = Config.HARNESS_LATENCY_THRESHOLD
        success = benchmark.check_success_criteria(result.avg_latency_ms, threshold)
        click.echo(f"\nSuccess Criteria (<{threshold:.0f}ms): {'✓ PASS' if success else '✗ FAIL'}")

        if verbose:
            click.echo(f"\nPer-Task Results:")
            for task_id, r in result.per_task_results.items():
                status = "✓" if r.success else "✗"
                retry_info = f" (retries: {r.retry_count})" if r.retry_count > 0 else ""
                click.echo(f"  {status} {task_id}: {r.latency_ms:.2f}ms{retry_info}")

    click.echo("\n" + "=" * 60)


@cli.command()
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
def stress_test(format):
    """Run stress test to measure latency and throughput under load."""
    click.echo("Running Harness Stress Test...")
    click.echo("=" * 60)

    benchmark = HarnessQualityBenchmark()
    result = benchmark.run_stress_test()

    if format == 'json':
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"\nTotal Tasks: {result['total_tasks']}")
        click.echo(f"\nLatency Metrics:")
        click.echo(f"  Average: {result['avg_latency_ms']:.2f}ms")
        click.echo(f"  Maximum: {result['max_latency_ms']:.2f}ms")
        click.echo(f"  Minimum: {result['min_latency_ms']:.2f}ms")
        click.echo(f"\nThroughput: {result['avg_throughput_ops']:.2f} ops/sec")

        threshold = Config.HARNESS_LATENCY_THRESHOLD
        success = benchmark.check_success_criteria(result['avg_latency_ms'], threshold)
        click.echo(f"\nSuccess Criteria (<{threshold:.0f}ms): {'✓ PASS' if success else '✗ FAIL'}")

    click.echo("\n" + "=" * 60)


@cli.command()
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
def load_test(format):
    """Run load scaling test to benchmark under varying load levels."""
    click.echo("Running Load Scaling Test...")
    click.echo("=" * 60)

    benchmark = HarnessQualityBenchmark()
    result = benchmark.run_load_scaling_test()

    if format == 'json':
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"\nTotal Load Levels Tested: {result['total_load_levels']}")
        click.echo(f"\nResults by Load Level:")

        for load_key in sorted(result['results_by_load'].keys(), key=lambda x: int(x[:-1])):
            metrics = result['results_by_load'][load_key]
            click.echo(f"\n  {load_key} Load:")
            click.echo(f"    Latency: {metrics['latency_ms']:.2f}ms")
            click.echo(f"    Throughput: {metrics['throughput_ops']:.2f} ops/sec")
            click.echo(f"    Success: {'✓' if metrics['success'] else '✗'}")

        # Check if any load level exceeds threshold
        threshold = Config.HARNESS_LATENCY_THRESHOLD
        max_latency = max(m['latency_ms'] for m in result['results_by_load'].values())
        success = benchmark.check_success_criteria(max_latency, threshold)
        click.echo(f"\nSuccess Criteria - Max Latency (<{threshold:.0f}ms): {'✓ PASS' if success else '✗ FAIL'}")

    click.echo("\n" + "=" * 60)


if __name__ == '__main__':
    cli()
