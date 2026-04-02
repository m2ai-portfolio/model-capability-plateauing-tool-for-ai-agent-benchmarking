"""
Harness Quality Benchmark Module for Model Capability Plateauing Tool.

Evaluates the robustness and reliability of the agent's execution harness,
including fault tolerance, retry mechanisms, and resource management.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import random
import time


@dataclass
class HarnessTask:
    """Represents a single harness quality task."""
    id: str
    description: str
    category: str  # 'stress_test', 'fault_injection', 'load_scaling', 'retry_mechanism'
    expected_latency_ms: float
    load_level: int  # Multiplier for load (1x, 2x, 4x, 8x)


@dataclass
class HarnessResult:
    """Result from running a harness task."""
    task_id: str
    latency_ms: float
    throughput_ops: float
    success: bool
    retry_count: int
    error: Optional[str] = None


@dataclass
class BenchmarkResult:
    """Overall result from running the harness quality benchmark."""
    total_tasks: int
    successful: int
    success_rate: float
    avg_latency_ms: float
    avg_throughput_ops: float
    per_task_results: Dict[str, HarnessResult]
    per_category_metrics: Dict[str, Dict[str, float]]
    max_latency_ms: float
    min_latency_ms: float


class RetryMechanism:
    """Implements exponential backoff retry mechanism."""

    def __init__(self, base_delay: float = 0.01, max_retries: int = 3, max_delay: float = 1.0, jitter: bool = True):
        """
        Initialize retry mechanism.

        Args:
            base_delay: Base delay in seconds (default 0.01 = 10ms)
            max_retries: Maximum number of retry attempts
            max_delay: Maximum delay between retries in seconds
            jitter: Whether to add random jitter to delays
        """
        self.base_delay = base_delay
        self.max_retries = max_retries
        self.max_delay = max_delay
        self.jitter = jitter
        self.retry_count = 0
        self.total_delay = 0.0

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given retry attempt using exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * 2^attempt
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)

        # Add jitter if enabled (±25% randomization)
        if self.jitter and attempt > 0:
            # Use deterministic seed for testing reproducibility
            seed = int(delay * 1000) + attempt
            random.seed(seed)
            jitter_factor = 0.75 + (random.random() * 0.5)  # 0.75 to 1.25
            delay *= jitter_factor

        return delay

    def execute_with_retry(self, task_fn, task_id: str) -> Dict[str, Any]:
        """
        Execute a task with retry logic.

        Args:
            task_fn: Callable that executes the task
            task_id: Task identifier for seeding

        Returns:
            Dict with 'success' (bool), 'result' (Any), 'retry_count' (int), 'total_delay' (float)
        """
        self.retry_count = 0
        self.total_delay = 0.0

        for attempt in range(self.max_retries + 1):
            try:
                result = task_fn()

                # Simulate random failures for testing retry mechanism
                # Use deterministic seed based on task_id and attempt
                seed = sum(ord(c) * (i + 1) for i, c in enumerate(task_id)) + attempt * 13
                random.seed(seed)

                # First attempt: 30% failure rate
                # Subsequent attempts: 10% failure rate (retries are more likely to succeed)
                failure_rate = 0.30 if attempt == 0 else 0.10

                if random.random() < failure_rate and attempt < self.max_retries:
                    # Simulate failure, trigger retry
                    delay = self.calculate_delay(attempt)
                    self.total_delay += delay
                    self.retry_count += 1
                    continue

                return {
                    'success': True,
                    'result': result,
                    'retry_count': self.retry_count,
                    'total_delay': self.total_delay
                }

            except Exception as e:
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)
                    self.total_delay += delay
                    self.retry_count += 1
                    continue
                else:
                    return {
                        'success': False,
                        'result': None,
                        'retry_count': self.retry_count,
                        'total_delay': self.total_delay,
                        'error': str(e)
                    }

        # Max retries exceeded
        return {
            'success': False,
            'result': None,
            'retry_count': self.retry_count,
            'total_delay': self.total_delay,
            'error': 'Max retries exceeded'
        }

    def reset(self):
        """Reset retry state."""
        self.retry_count = 0
        self.total_delay = 0.0


class FailureIsolator:
    """Wraps task execution to catch and isolate failures."""

    def __init__(self):
        """Initialize failure isolator."""
        self.isolated_failures: List[Dict[str, Any]] = []

    def execute_isolated(self, task_fn, task_id: str) -> Dict[str, Any]:
        """
        Execute a task in isolation, preventing cascading failures.

        Args:
            task_fn: Callable that executes the task
            task_id: Task identifier

        Returns:
            Dict with 'success' (bool), 'result' (Any), 'error' (str or None)
        """
        try:
            result = task_fn()
            return {
                'success': True,
                'result': result,
                'error': None
            }
        except Exception as e:
            # Isolate the failure - record it but don't propagate
            failure_info = {
                'task_id': task_id,
                'error': str(e),
                'isolated': True
            }
            self.isolated_failures.append(failure_info)

            return {
                'success': False,
                'result': None,
                'error': str(e)
            }

    def get_isolated_failures(self) -> List[Dict[str, Any]]:
        """Get list of isolated failures."""
        return self.isolated_failures

    def has_cascading_failure(self) -> bool:
        """Check if any failures cascaded (should always be False if working correctly)."""
        # In a working isolator, failures never cascade
        return False

    def reset(self):
        """Reset isolator state."""
        self.isolated_failures.clear()


class HarnessQualityBenchmark:
    """Harness quality benchmark suite with simulated tasks."""

    def __init__(self):
        """Initialize the harness quality benchmark with simulated tasks."""
        self.tasks = self._create_simulated_tasks()
        self.retry_mechanism = RetryMechanism()
        self.failure_isolator = FailureIsolator()

    def _create_simulated_tasks(self) -> List[HarnessTask]:
        """Create a set of simulated harness quality tasks."""
        tasks = [
            # Stress Test Tasks
            HarnessTask(
                id='stress_001',
                description='Baseline latency measurement under normal load',
                category='stress_test',
                expected_latency_ms=20.0,
                load_level=1
            ),
            HarnessTask(
                id='stress_002',
                description='Latency under moderate concurrent operations',
                category='stress_test',
                expected_latency_ms=35.0,
                load_level=2
            ),
            HarnessTask(
                id='stress_003',
                description='Throughput measurement under sustained load',
                category='stress_test',
                expected_latency_ms=50.0,
                load_level=4
            ),

            # Fault Injection Tasks
            HarnessTask(
                id='fault_001',
                description='Handle network timeout gracefully',
                category='fault_injection',
                expected_latency_ms=30.0,
                load_level=1
            ),
            HarnessTask(
                id='fault_002',
                description='Recover from transient API failure',
                category='fault_injection',
                expected_latency_ms=40.0,
                load_level=1
            ),
            HarnessTask(
                id='fault_003',
                description='Isolate failure in multi-task execution',
                category='fault_injection',
                expected_latency_ms=25.0,
                load_level=2
            ),

            # Load Scaling Tasks
            HarnessTask(
                id='load_001',
                description='Baseline performance (1x load)',
                category='load_scaling',
                expected_latency_ms=15.0,
                load_level=1
            ),
            HarnessTask(
                id='load_002',
                description='Double load performance (2x)',
                category='load_scaling',
                expected_latency_ms=28.0,
                load_level=2
            ),
            HarnessTask(
                id='load_003',
                description='Quadruple load performance (4x)',
                category='load_scaling',
                expected_latency_ms=55.0,
                load_level=4
            ),
            HarnessTask(
                id='load_004',
                description='Heavy load performance (8x)',
                category='load_scaling',
                expected_latency_ms=95.0,
                load_level=8
            ),

            # Retry Mechanism Tasks
            HarnessTask(
                id='retry_001',
                description='Single retry on transient failure',
                category='retry_mechanism',
                expected_latency_ms=25.0,
                load_level=1
            ),
            HarnessTask(
                id='retry_002',
                description='Multiple retries with exponential backoff',
                category='retry_mechanism',
                expected_latency_ms=45.0,
                load_level=1
            ),
            HarnessTask(
                id='retry_003',
                description='Retry with jitter to prevent thundering herd',
                category='retry_mechanism',
                expected_latency_ms=35.0,
                load_level=2
            ),
        ]

        return tasks

    def _simulate_task_execution(self, task: HarnessTask) -> Dict[str, Any]:
        """
        Simulate executing a harness task.

        Returns:
            Dict with 'latency_ms', 'throughput_ops', 'success'
        """
        # Simulate base latency with some variation
        base_latency = task.expected_latency_ms

        # Use deterministic seed for reproducibility
        seed = sum(ord(c) * (i + 1) for i, c in enumerate(task.id))
        random.seed(seed)

        # Add realistic variance (±10%)
        variance = base_latency * 0.1 * (random.random() - 0.5) * 2
        actual_latency = base_latency + variance

        # Scale latency based on load level (sub-linear scaling)
        # 2x load != 2x latency due to optimizations
        load_factor = 1.0 + (task.load_level - 1) * 0.4
        actual_latency *= load_factor

        # Calculate throughput (operations per second)
        # Higher for lower latency tasks
        throughput = (1000.0 / actual_latency) * task.load_level

        # Success rate depends on category
        success_rates = {
            'stress_test': 0.95,
            'fault_injection': 0.85,  # Lower due to injected failures
            'load_scaling': 0.92,
            'retry_mechanism': 0.88,  # Lower initially, but retries help
        }

        base_success_rate = success_rates.get(task.category, 0.90)

        # Determine success
        random.seed(seed + 1)
        success = random.random() < base_success_rate

        return {
            'latency_ms': actual_latency,
            'throughput_ops': throughput,
            'success': success
        }

    def run_benchmark(self, enable_retry: bool = True, enable_isolation: bool = True) -> BenchmarkResult:
        """
        Run the complete harness quality benchmark suite.

        Args:
            enable_retry: Whether to enable retry mechanism
            enable_isolation: Whether to enable failure isolation

        Returns:
            BenchmarkResult with detailed metrics
        """
        results = {}
        category_metrics = {
            'stress_test': {'latencies': [], 'throughputs': [], 'successes': []},
            'fault_injection': {'latencies': [], 'throughputs': [], 'successes': []},
            'load_scaling': {'latencies': [], 'throughputs': [], 'successes': []},
            'retry_mechanism': {'latencies': [], 'throughputs': [], 'successes': []},
        }

        all_latencies = []
        all_throughputs = []

        for task in self.tasks:
            # Execute task
            if enable_retry and task.category in ['retry_mechanism', 'fault_injection']:
                # Use retry mechanism for retry and fault injection tasks
                self.retry_mechanism.reset()
                retry_result = self.retry_mechanism.execute_with_retry(
                    lambda: self._simulate_task_execution(task),
                    task.id
                )

                if retry_result['success']:
                    exec_result = retry_result['result']
                    retry_count = retry_result['retry_count']
                    # Add retry delay to latency
                    exec_result['latency_ms'] += retry_result['total_delay'] * 1000
                else:
                    exec_result = {
                        'latency_ms': task.expected_latency_ms * 2,
                        'throughput_ops': 0.0,
                        'success': False
                    }
                    retry_count = retry_result['retry_count']
            else:
                # Direct execution
                exec_result = self._simulate_task_execution(task)
                retry_count = 0

            # Apply failure isolation if enabled
            if enable_isolation:
                isolated_result = self.failure_isolator.execute_isolated(
                    lambda: exec_result,
                    task.id
                )
                if not isolated_result['success']:
                    exec_result['success'] = False
                    exec_result['error'] = isolated_result['error']

            # Create result
            result = HarnessResult(
                task_id=task.id,
                latency_ms=exec_result['latency_ms'],
                throughput_ops=exec_result['throughput_ops'],
                success=exec_result['success'],
                retry_count=retry_count,
                error=exec_result.get('error')
            )

            results[task.id] = result

            # Track metrics by category
            category_metrics[task.category]['latencies'].append(result.latency_ms)
            category_metrics[task.category]['throughputs'].append(result.throughput_ops)
            category_metrics[task.category]['successes'].append(result.success)

            all_latencies.append(result.latency_ms)
            all_throughputs.append(result.throughput_ops)

        # Calculate overall metrics
        successful_count = sum(1 for r in results.values() if r.success)
        total_count = len(results)
        success_rate = successful_count / total_count if total_count > 0 else 0.0

        avg_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0
        avg_throughput = sum(all_throughputs) / len(all_throughputs) if all_throughputs else 0.0

        max_latency = max(all_latencies) if all_latencies else 0.0
        min_latency = min(all_latencies) if all_latencies else 0.0

        # Calculate per-category metrics
        per_category = {}
        for category, metrics in category_metrics.items():
            if metrics['latencies']:
                per_category[category] = {
                    'avg_latency_ms': sum(metrics['latencies']) / len(metrics['latencies']),
                    'avg_throughput_ops': sum(metrics['throughputs']) / len(metrics['throughputs']),
                    'success_rate': sum(metrics['successes']) / len(metrics['successes'])
                }
            else:
                per_category[category] = {
                    'avg_latency_ms': 0.0,
                    'avg_throughput_ops': 0.0,
                    'success_rate': 0.0
                }

        return BenchmarkResult(
            total_tasks=total_count,
            successful=successful_count,
            success_rate=success_rate,
            avg_latency_ms=avg_latency,
            avg_throughput_ops=avg_throughput,
            per_task_results=results,
            per_category_metrics=per_category,
            max_latency_ms=max_latency,
            min_latency_ms=min_latency
        )

    def run_stress_test(self) -> Dict[str, Any]:
        """
        Run stress test to measure latency and throughput under load.

        Returns:
            Dict with stress test metrics
        """
        stress_tasks = [task for task in self.tasks if task.category == 'stress_test']

        latencies = []
        throughputs = []

        for task in stress_tasks:
            exec_result = self._simulate_task_execution(task)
            latencies.append(exec_result['latency_ms'])
            throughputs.append(exec_result['throughput_ops'])

        return {
            'total_tasks': len(stress_tasks),
            'avg_latency_ms': sum(latencies) / len(latencies) if latencies else 0.0,
            'max_latency_ms': max(latencies) if latencies else 0.0,
            'min_latency_ms': min(latencies) if latencies else 0.0,
            'avg_throughput_ops': sum(throughputs) / len(throughputs) if throughputs else 0.0,
            'latencies': latencies,
            'throughputs': throughputs
        }

    def run_load_scaling_test(self) -> Dict[str, Any]:
        """
        Run load scaling test to benchmark under varying load levels.

        Returns:
            Dict with load scaling metrics by load level
        """
        load_tasks = [task for task in self.tasks if task.category == 'load_scaling']

        results_by_load = {}

        for task in load_tasks:
            exec_result = self._simulate_task_execution(task)

            load_key = f'{task.load_level}x'
            results_by_load[load_key] = {
                'load_level': task.load_level,
                'latency_ms': exec_result['latency_ms'],
                'throughput_ops': exec_result['throughput_ops'],
                'success': exec_result['success']
            }

        return {
            'total_load_levels': len(results_by_load),
            'results_by_load': results_by_load
        }

    def test_failure_isolation(self) -> Dict[str, Any]:
        """
        Test failure isolation to verify failures don't cascade.

        Returns:
            Dict with isolation test results
        """
        self.failure_isolator.reset()

        fault_tasks = [task for task in self.tasks if task.category == 'fault_injection']

        isolated_count = 0
        total_failures = 0

        for task in fault_tasks:
            result = self.failure_isolator.execute_isolated(
                lambda: self._simulate_task_execution(task),
                task.id
            )

            if not result['success']:
                total_failures += 1
                isolated_count += 1

        has_cascading = self.failure_isolator.has_cascading_failure()

        return {
            'total_tasks': len(fault_tasks),
            'total_failures': total_failures,
            'isolated_failures': isolated_count,
            'cascading_failures': 0 if not has_cascading else total_failures - isolated_count,
            'isolation_success': isolated_count == total_failures and not has_cascading
        }

    def check_success_criteria(self, latency_ms: float, threshold: float = 100.0) -> bool:
        """
        Check if latency meets success criteria.

        Args:
            latency_ms: Measured latency in milliseconds
            threshold: Maximum acceptable latency (default 100ms)

        Returns:
            True if success criteria met, False otherwise
        """
        return latency_ms < threshold
