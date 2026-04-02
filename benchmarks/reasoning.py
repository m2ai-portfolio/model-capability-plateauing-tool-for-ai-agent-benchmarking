"""
Reasoning Benchmark Module for Model Capability Plateauing Tool.

Provides simulated reasoning tasks covering symbolic reasoning, multi-step planning,
and GSM8K-style mathematical reasoning.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import re
import random


@dataclass
class ReasoningTask:
    """Represents a single reasoning task."""
    id: str
    question: str
    answer: str
    category: str  # 'symbolic', 'planning', 'math'
    difficulty: str  # 'easy', 'medium', 'hard'
    requires_modules: List[str] = field(default_factory=list)


@dataclass
class BenchmarkResult:
    """Result from running the benchmark."""
    total_tasks: int
    correct: int
    accuracy: float
    per_task_results: Dict[str, bool]
    per_category_accuracy: Dict[str, float]
    baseline_comparison: Optional[float] = None
    ablation_delta: Optional[float] = None


class ReasoningBenchmark:
    """Reasoning benchmark suite with simulated tasks."""

    def __init__(self):
        """Initialize the reasoning benchmark with simulated tasks."""
        self.tasks = self._create_simulated_tasks()
        self.baseline_accuracy = 0.75  # 75% baseline

    def _create_simulated_tasks(self) -> List[ReasoningTask]:
        """Create a set of simulated reasoning tasks."""
        tasks = [
            # Symbolic Reasoning Tasks
            ReasoningTask(
                id="symbolic_001",
                question="If all A are B, and all B are C, then are all A also C?",
                answer="yes",
                category="symbolic",
                difficulty="easy",
                requires_modules=["symbolic_reasoning"]
            ),
            ReasoningTask(
                id="symbolic_002",
                question="Given: P -> Q, Q -> R. If P is true, is R true?",
                answer="yes",
                category="symbolic",
                difficulty="medium",
                requires_modules=["symbolic_reasoning"]
            ),
            ReasoningTask(
                id="symbolic_003",
                question="If some X are Y, and no Y are Z, can we conclude that no X are Z?",
                answer="no",
                category="symbolic",
                difficulty="hard",
                requires_modules=["symbolic_reasoning"]
            ),

            # Multi-step Planning Tasks
            ReasoningTask(
                id="planning_001",
                question="You need to paint a room. You must: buy paint, prepare walls, apply primer, paint. What is the second step?",
                answer="prepare walls",
                category="planning",
                difficulty="easy",
                requires_modules=["planning", "multi_step"]
            ),
            ReasoningTask(
                id="planning_002",
                question="To make coffee: grind beans, heat water, brew coffee, add milk. If you want milk coffee and water takes 3 min to heat, beans take 1 min to grind, brewing takes 4 min, what's the minimum total time?",
                answer="7",
                category="planning",
                difficulty="medium",
                requires_modules=["planning", "multi_step"]
            ),
            ReasoningTask(
                id="planning_003",
                question="You have tasks A(2h), B(1h), C(3h). A must finish before B. B must finish before C. What is the minimum total time?",
                answer="6",
                category="planning",
                difficulty="medium",
                requires_modules=["planning", "multi_step"]
            ),

            # GSM8K-style Math Reasoning Tasks
            ReasoningTask(
                id="math_001",
                question="Sarah has 15 apples. She gives 3 to John and 4 to Mary. How many apples does Sarah have left?",
                answer="8",
                category="math",
                difficulty="easy",
                requires_modules=["multi_step"]
            ),
            ReasoningTask(
                id="math_002",
                question="A train travels 60 km in 45 minutes. What is its speed in km/h?",
                answer="80",
                category="math",
                difficulty="medium",
                requires_modules=["multi_step"]
            ),
            ReasoningTask(
                id="math_003",
                question="If 3 workers can build 3 widgets in 3 days, how many widgets can 6 workers build in 6 days?",
                answer="12",
                category="math",
                difficulty="hard",
                requires_modules=["multi_step", "symbolic_reasoning"]
            ),
            ReasoningTask(
                id="math_004",
                question="A store sells apples at $2 each. If you buy 10 or more, you get 20% off. How much do 12 apples cost?",
                answer="19.2",
                category="math",
                difficulty="medium",
                requires_modules=["multi_step"]
            ),

            # Additional Complex Reasoning Tasks
            ReasoningTask(
                id="mixed_001",
                question="Alice is taller than Bob. Bob is taller than Charlie. Who is the shortest?",
                answer="charlie",
                category="symbolic",
                difficulty="easy",
                requires_modules=["symbolic_reasoning"]
            ),
            ReasoningTask(
                id="mixed_002",
                question="You have a 5L jug and a 3L jug. How can you measure exactly 4L? State the number of steps needed.",
                answer="6",
                category="planning",
                difficulty="hard",
                requires_modules=["planning", "multi_step", "symbolic_reasoning"]
            ),
        ]
        return tasks

    def _simulate_agent_answer(self, task: ReasoningTask, disabled_modules: Optional[List[str]] = None) -> str:
        """
        Simulate an AI agent answering a task.

        With all modules enabled, the agent achieves high accuracy (>80%).
        With modules disabled, accuracy drops proportionally.
        """
        disabled_modules = disabled_modules or []

        # Check if any required module is disabled
        modules_disabled = any(module in disabled_modules for module in task.requires_modules)

        # Base accuracy by category and difficulty
        accuracy_map = {
            ('symbolic', 'easy'): 0.95,
            ('symbolic', 'medium'): 0.90,
            ('symbolic', 'hard'): 0.75,
            ('planning', 'easy'): 0.95,
            ('planning', 'medium'): 0.85,
            ('planning', 'hard'): 0.70,
            ('math', 'easy'): 0.95,
            ('math', 'medium'): 0.88,
            ('math', 'hard'): 0.80,
        }

        base_accuracy = accuracy_map.get((task.category, task.difficulty), 0.80)

        # If critical modules are disabled, reduce accuracy significantly
        if modules_disabled:
            base_accuracy *= 0.5

        # Simulate answering based on accuracy
        # Use a deterministic seed based on task ID (avoiding Python's hash randomization)
        seed = sum(ord(c) * (i + 1) for i, c in enumerate(task.id))
        random.seed(seed)

        if random.random() < base_accuracy:
            return task.answer
        else:
            # Return a plausible wrong answer
            wrong_answers = {
                'symbolic_001': 'no',
                'symbolic_002': 'no',
                'symbolic_003': 'yes',
                'planning_001': 'buy paint',
                'planning_002': '8',
                'planning_003': '5',
                'math_001': '7',
                'math_002': '75',
                'math_003': '6',
                'math_004': '24',
                'mixed_001': 'bob',
                'mixed_002': '4',
            }
            return wrong_answers.get(task.id, 'unknown')

    def _normalize_answer(self, answer: str) -> str:
        """Normalize answer for comparison."""
        answer = answer.lower().strip()
        # Remove common punctuation
        answer = re.sub(r'[.,!?;:]', '', answer)
        return answer

    def _check_answer(self, given_answer: str, correct_answer: str) -> bool:
        """Check if the given answer matches the correct answer."""
        given = self._normalize_answer(given_answer)
        correct = self._normalize_answer(correct_answer)

        # Try exact match
        if given == correct:
            return True

        # Try numeric match (for math problems)
        try:
            given_num = float(given)
            correct_num = float(correct)
            return abs(given_num - correct_num) < 0.01
        except (ValueError, TypeError):
            pass

        # Check if answer is contained in response
        return correct in given

    def run_benchmark(self, disabled_modules: Optional[List[str]] = None) -> BenchmarkResult:
        """
        Run the complete reasoning benchmark suite.

        Args:
            disabled_modules: List of modules to disable for ablation testing.

        Returns:
            BenchmarkResult with detailed metrics.
        """
        disabled_modules = disabled_modules or []

        results = {}
        category_results = {'symbolic': [], 'planning': [], 'math': []}

        for task in self.tasks:
            agent_answer = self._simulate_agent_answer(task, disabled_modules)
            is_correct = self._check_answer(agent_answer, task.answer)
            results[task.id] = is_correct
            category_results[task.category].append(is_correct)

        # Calculate overall accuracy
        correct_count = sum(results.values())
        total_count = len(results)
        accuracy = correct_count / total_count if total_count > 0 else 0.0

        # Calculate per-category accuracy
        per_category_accuracy = {}
        for category, category_res in category_results.items():
            if category_res:
                per_category_accuracy[category] = sum(category_res) / len(category_res)
            else:
                per_category_accuracy[category] = 0.0

        return BenchmarkResult(
            total_tasks=total_count,
            correct=correct_count,
            accuracy=accuracy,
            per_task_results=results,
            per_category_accuracy=per_category_accuracy
        )

    def evaluate_gsm8k_style(self) -> BenchmarkResult:
        """
        Evaluate on GSM8K-style reasoning tasks and compare to baseline.

        Returns:
            BenchmarkResult with baseline comparison.
        """
        # Filter for math tasks (GSM8K-style)
        math_tasks = [task for task in self.tasks if task.category == 'math']

        results = {}
        for task in math_tasks:
            agent_answer = self._simulate_agent_answer(task)
            is_correct = self._check_answer(agent_answer, task.answer)
            results[task.id] = is_correct

        correct_count = sum(results.values())
        total_count = len(results)
        accuracy = correct_count / total_count if total_count > 0 else 0.0

        # Calculate baseline comparison
        baseline_comparison = accuracy - self.baseline_accuracy

        return BenchmarkResult(
            total_tasks=total_count,
            correct=correct_count,
            accuracy=accuracy,
            per_task_results=results,
            per_category_accuracy={'math': accuracy},
            baseline_comparison=baseline_comparison
        )

    def run_ablation(self, module_to_disable: str) -> Dict[str, Any]:
        """
        Perform ablation study by disabling specific reasoning modules.

        Args:
            module_to_disable: Name of module to disable ('symbolic_reasoning', 'planning', 'multi_step')

        Returns:
            Dict with baseline and ablated results, including delta.
        """
        # Run baseline (all modules enabled)
        baseline_result = self.run_benchmark(disabled_modules=[])

        # Run with module disabled
        ablated_result = self.run_benchmark(disabled_modules=[module_to_disable])

        # Calculate delta
        delta = ablated_result.accuracy - baseline_result.accuracy

        return {
            'module_disabled': module_to_disable,
            'baseline_accuracy': baseline_result.accuracy,
            'ablated_accuracy': ablated_result.accuracy,
            'delta': delta,
            'baseline_result': baseline_result,
            'ablated_result': ablated_result
        }

    def check_success_criteria(self, accuracy: float, threshold: float = 0.80) -> bool:
        """
        Check if accuracy meets success criteria.

        Args:
            accuracy: Achieved accuracy score
            threshold: Required threshold (default 0.80 = 80%)

        Returns:
            True if success criteria met, False otherwise
        """
        return accuracy > threshold
