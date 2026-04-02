"""
CLI interface for Model Capability Plateauing Tool.

Provides commands for running benchmarks and viewing results.
"""

import click
import json
from benchmarks.reasoning import ReasoningBenchmark
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


if __name__ == '__main__':
    cli()
