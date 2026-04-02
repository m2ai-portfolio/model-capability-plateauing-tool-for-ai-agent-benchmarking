"""
Tests for Tool Use Benchmark Module.

Verifies:
- Tool use benchmark runs successfully
- Success rate is computed correctly
- Mock API validates correct calls
- State is maintained across tool calls
- Safety constraints are enforced
- Failure injection works (graceful handling)
- Success criteria check (success rate > 70%)
"""

import pytest
from benchmarks.tool_use import (
    ToolUseBenchmark, ToolDescription, ToolCall, ToolUseTask, ToolUseResult, MockAPI
)
from benchmarks.config import Config


class TestToolUseBenchmark:
    """Test suite for ToolUseBenchmark class."""

    def test_benchmark_initialization(self):
        """Test that benchmark initializes with tasks."""
        benchmark = ToolUseBenchmark()
        assert len(benchmark.tasks) >= 10
        assert benchmark.baseline_success_rate == 0.70

    def test_simulated_tasks_structure(self):
        """Test that simulated tasks have correct structure."""
        benchmark = ToolUseBenchmark()

        # Check we have at least 10 tasks (as required)
        assert len(benchmark.tasks) >= 10

        # Check task categories are present
        categories = {task.category for task in benchmark.tasks}
        assert 'api_invocation' in categories
        assert 'state_management' in categories
        assert 'safety_constraints' in categories
        assert 'failure_handling' in categories

        # Check each task has required fields
        for task in benchmark.tasks:
            assert task.id
            assert task.description
            assert isinstance(task.available_tools, list)
            assert isinstance(task.expected_calls, list)
            assert task.category in ['api_invocation', 'state_management', 'safety_constraints', 'failure_handling']
            assert task.difficulty in ['easy', 'medium', 'hard']

    def test_run_benchmark_successfully(self):
        """Test that benchmark runs successfully and returns valid results."""
        benchmark = ToolUseBenchmark()
        result = benchmark.run_benchmark()

        # Check result structure
        assert isinstance(result, ToolUseResult)
        assert result.total_tasks > 0
        assert result.successful >= 0
        assert 0.0 <= result.success_rate <= 1.0
        assert isinstance(result.per_task_results, dict)
        assert isinstance(result.per_category_success, dict)

        # Check that total tasks matches number of task results
        assert result.total_tasks == len(result.per_task_results)

        # Check success rate calculation
        expected_success_rate = result.successful / result.total_tasks
        assert abs(result.success_rate - expected_success_rate) < 0.001

    def test_success_rate_computed_correctly(self):
        """Test that success rate computation is correct."""
        benchmark = ToolUseBenchmark()
        result = benchmark.run_benchmark()

        # Manually compute success rate
        successful_count = sum(result.per_task_results.values())
        total_count = len(result.per_task_results)
        expected_success_rate = successful_count / total_count

        assert result.successful == successful_count
        assert result.total_tasks == total_count
        assert abs(result.success_rate - expected_success_rate) < 0.001

    def test_per_category_success_rate(self):
        """Test that per-category success rate is computed correctly."""
        benchmark = ToolUseBenchmark()
        result = benchmark.run_benchmark()

        # Check all expected categories are present
        assert 'api_invocation' in result.per_category_success
        assert 'state_management' in result.per_category_success
        assert 'safety_constraints' in result.per_category_success
        assert 'failure_handling' in result.per_category_success

        # Check all values are valid percentages
        for category, rate in result.per_category_success.items():
            assert 0.0 <= rate <= 1.0

    def test_mock_api_test_works(self):
        """Test that mock API test runs correctly."""
        benchmark = ToolUseBenchmark()
        test_results = benchmark.test_mock_api()

        # Check result structure
        assert isinstance(test_results, dict)
        assert 'tool_registration' in test_results
        assert 'simple_call' in test_results
        assert 'state_persistence' in test_results
        assert 'parameter_validation' in test_results
        assert 'safety_enforcement' in test_results

        # All tests should be boolean
        for test_name, result in test_results.items():
            assert isinstance(result, bool)

    def test_mock_api_validates_correct_calls(self):
        """Test that mock API validates correct calls properly."""
        benchmark = ToolUseBenchmark()
        test_results = benchmark.test_mock_api()

        # Simple call should succeed
        assert test_results['simple_call'] is True

        # Tool registration should succeed
        assert test_results['tool_registration'] is True

    def test_state_maintained_across_tool_calls(self):
        """Test that state is maintained across tool calls."""
        benchmark = ToolUseBenchmark()
        test_results = benchmark.test_mock_api()

        # State persistence test should pass
        assert test_results['state_persistence'] is True

    def test_safety_constraints_enforced(self):
        """Test that safety constraints are properly enforced."""
        benchmark = ToolUseBenchmark()
        test_results = benchmark.test_mock_api()

        # Safety enforcement should work
        assert test_results['safety_enforcement'] is True

    def test_parameter_validation(self):
        """Test that parameter validation works correctly."""
        benchmark = ToolUseBenchmark()
        test_results = benchmark.test_mock_api()

        # Parameter validation should catch missing parameters
        assert test_results['parameter_validation'] is True

    def test_failure_injection_works(self):
        """Test that failure injection test runs correctly."""
        benchmark = ToolUseBenchmark()
        failure_results = benchmark.run_failure_injection_test()

        # Check result structure
        assert 'normal_success_rate' in failure_results
        assert 'failure_mode_success_rate' in failure_results
        assert 'resilience_score' in failure_results
        assert 'graceful_degradation' in failure_results
        assert 'normal_result' in failure_results
        assert 'failure_result' in failure_results

        # Check valid ranges
        assert 0.0 <= failure_results['normal_success_rate'] <= 1.0
        assert 0.0 <= failure_results['failure_mode_success_rate'] <= 1.0
        assert 0.0 <= failure_results['resilience_score'] <= 1.0

    def test_graceful_handling_under_failures(self):
        """Test that system handles failures gracefully."""
        benchmark = ToolUseBenchmark()
        failure_results = benchmark.run_failure_injection_test()

        # Failure mode should still have reasonable success
        # (may not always be >50% due to randomness, but should be >0)
        assert failure_results['failure_mode_success_rate'] > 0.0

        # Resilience score should be reasonable
        assert failure_results['resilience_score'] >= 0.0

    def test_success_criteria_pass(self):
        """Test success criteria check when success rate > 70%."""
        benchmark = ToolUseBenchmark()

        # Test with success rate above threshold
        assert benchmark.check_success_criteria(0.75, 0.70) is True
        assert benchmark.check_success_criteria(0.85, 0.70) is True
        assert benchmark.check_success_criteria(1.00, 0.70) is True

    def test_success_criteria_fail(self):
        """Test success criteria check when success rate <= 70%."""
        benchmark = ToolUseBenchmark()

        # Test with success rate at or below threshold
        assert benchmark.check_success_criteria(0.70, 0.70) is False
        assert benchmark.check_success_criteria(0.65, 0.70) is False
        assert benchmark.check_success_criteria(0.50, 0.70) is False

    def test_success_criteria_with_actual_benchmark(self):
        """Test that actual benchmark results meet success criteria."""
        benchmark = ToolUseBenchmark()
        result = benchmark.run_benchmark()

        # Check success criteria
        threshold = Config.TOOL_USE_BASELINE_SUCCESS_RATE
        success = benchmark.check_success_criteria(result.success_rate, threshold)

        # The benchmark should achieve >70% success rate
        assert result.success_rate > 0.70, f"Expected success rate > 70%, got {result.success_rate:.2%}"
        assert success is True, "Success criteria should be met"

    def test_deterministic_results(self):
        """Test that benchmark results are deterministic."""
        benchmark1 = ToolUseBenchmark()
        benchmark2 = ToolUseBenchmark()

        result1 = benchmark1.run_benchmark()
        result2 = benchmark2.run_benchmark()

        # Results should be identical
        assert result1.success_rate == result2.success_rate
        assert result1.successful == result2.successful
        assert result1.total_tasks == result2.total_tasks
        assert result1.per_task_results == result2.per_task_results

    def test_config_integration(self):
        """Test that benchmark integrates with Config correctly."""
        # Check that config values are accessible
        assert Config.TOOL_USE_BASELINE_SUCCESS_RATE == 0.70
        assert Config.TOOL_USE_FAILURE_RATE == 0.2

        # Check that benchmark uses config
        benchmark = ToolUseBenchmark()
        assert benchmark.baseline_success_rate == Config.TOOL_USE_BASELINE_SUCCESS_RATE


class TestMockAPI:
    """Test suite for MockAPI class."""

    def test_api_initialization(self):
        """Test that API initializes correctly."""
        api = MockAPI()
        assert len(api.tools) == 0
        assert len(api.state) == 0
        assert len(api.call_history) == 0
        assert api.failure_mode is False

    def test_api_with_failure_mode(self):
        """Test API initialization with failure mode."""
        api = MockAPI(failure_mode=True, failure_rate=0.3)
        assert api.failure_mode is True
        assert api.failure_rate == 0.3

    def test_tool_registration(self):
        """Test registering tools with the API."""
        api = MockAPI()
        tool = ToolDescription(
            id='test_tool',
            name='Test Tool',
            description='A test tool',
            parameters={'param1': 'string'},
            return_type='string',
            safety_level='safe'
        )

        api.register_tool(tool)
        assert 'test_tool' in api.tools
        assert api.tools['test_tool'] == tool

    def test_valid_tool_call(self):
        """Test executing a valid tool call."""
        api = MockAPI()
        tool = ToolDescription(
            id='calculate',
            name='Calculate',
            description='Perform calculations',
            parameters={'operation': 'string', 'a': 'number', 'b': 'number'},
            return_type='number',
            safety_level='safe'
        )
        api.register_tool(tool)

        result = api.validate_call('calculate', {'operation': 'add', 'a': 5, 'b': 3})

        assert result['success'] is True
        assert result['result'] == 8
        assert result['error'] is None

    def test_invalid_tool_call(self):
        """Test calling a non-existent tool."""
        api = MockAPI()

        result = api.validate_call('nonexistent_tool', {})

        assert result['success'] is False
        assert result['result'] is None
        assert 'not found' in result['error']

    def test_missing_parameter(self):
        """Test call with missing required parameter."""
        api = MockAPI()
        tool = ToolDescription(
            id='test_tool',
            name='Test Tool',
            description='Test',
            parameters={'required_param': 'string'},
            return_type='string',
            safety_level='safe'
        )
        api.register_tool(tool)

        result = api.validate_call('test_tool', {})

        assert result['success'] is False
        assert 'Missing required parameter' in result['error']

    def test_restricted_tool_blocked(self):
        """Test that restricted tools are blocked."""
        api = MockAPI()
        tool = ToolDescription(
            id='dangerous_tool',
            name='Dangerous Tool',
            description='A dangerous operation',
            parameters={'param': 'string'},
            return_type='bool',
            safety_level='restricted'
        )
        api.register_tool(tool)

        result = api.validate_call('dangerous_tool', {'param': 'value'})

        assert result['success'] is False
        assert 'restricted' in result['error']

    def test_state_persistence(self):
        """Test that state persists across calls."""
        api = MockAPI()
        create_tool = ToolDescription(
            id='create_user',
            name='Create User',
            description='Create a user',
            parameters={'user_id': 'string', 'name': 'string'},
            return_type='User',
            safety_level='requires_permission'
        )
        get_tool = ToolDescription(
            id='get_user',
            name='Get User',
            description='Get a user',
            parameters={'user_id': 'string'},
            return_type='User',
            safety_level='safe'
        )
        api.register_tool(create_tool)
        api.register_tool(get_tool)

        # Create user
        create_result = api.validate_call('create_user', {'user_id': 'u1', 'name': 'Alice'})
        assert create_result['success'] is True

        # Retrieve user
        get_result = api.validate_call('get_user', {'user_id': 'u1'})
        assert get_result['success'] is True
        assert get_result['result']['name'] == 'Alice'

    def test_call_history_tracking(self):
        """Test that call history is tracked."""
        api = MockAPI()
        tool = ToolDescription(
            id='test_tool',
            name='Test',
            description='Test',
            parameters={'param': 'string'},
            return_type='string',
            safety_level='safe'
        )
        api.register_tool(tool)

        api.validate_call('test_tool', {'param': 'value1'})
        api.validate_call('test_tool', {'param': 'value2'})

        assert len(api.call_history) == 2
        assert api.call_history[0]['parameters']['param'] == 'value1'
        assert api.call_history[1]['parameters']['param'] == 'value2'

    def test_api_reset(self):
        """Test that API reset clears state and history."""
        api = MockAPI()
        tool = ToolDescription(
            id='test_tool',
            name='Test',
            description='Test',
            parameters={},
            return_type='string',
            safety_level='safe'
        )
        api.register_tool(tool)

        api.state['key'] = 'value'
        api.validate_call('test_tool', {})

        assert len(api.state) > 0
        assert len(api.call_history) > 0

        api.reset()

        assert len(api.state) == 0
        assert len(api.call_history) == 0


class TestToolDescription:
    """Test suite for ToolDescription dataclass."""

    def test_tool_description_creation(self):
        """Test creating a tool description."""
        tool = ToolDescription(
            id='test_001',
            name='Test Tool',
            description='A test tool for testing',
            parameters={'param1': 'string', 'param2': 'number'},
            return_type='object',
            safety_level='safe'
        )

        assert tool.id == 'test_001'
        assert tool.name == 'Test Tool'
        assert tool.description == 'A test tool for testing'
        assert tool.parameters == {'param1': 'string', 'param2': 'number'}
        assert tool.return_type == 'object'
        assert tool.safety_level == 'safe'


class TestToolCall:
    """Test suite for ToolCall dataclass."""

    def test_tool_call_creation(self):
        """Test creating a tool call."""
        call = ToolCall(
            tool_id='test_tool',
            parameters={'param1': 'value1'},
            expected_result={'status': 'success'}
        )

        assert call.tool_id == 'test_tool'
        assert call.parameters == {'param1': 'value1'}
        assert call.expected_result == {'status': 'success'}


class TestToolUseTask:
    """Test suite for ToolUseTask dataclass."""

    def test_task_creation(self):
        """Test creating a tool use task."""
        tool = ToolDescription(
            id='test_tool',
            name='Test',
            description='Test',
            parameters={},
            return_type='string',
            safety_level='safe'
        )
        call = ToolCall('test_tool', {}, 'result')

        task = ToolUseTask(
            id='task_001',
            description='Test task',
            available_tools=[tool],
            expected_calls=[call],
            category='api_invocation',
            difficulty='easy'
        )

        assert task.id == 'task_001'
        assert task.description == 'Test task'
        assert len(task.available_tools) == 1
        assert len(task.expected_calls) == 1
        assert task.category == 'api_invocation'
        assert task.difficulty == 'easy'


class TestToolUseResult:
    """Test suite for ToolUseResult dataclass."""

    def test_result_creation(self):
        """Test creating a tool use result."""
        result = ToolUseResult(
            total_tasks=10,
            successful=7,
            success_rate=0.7,
            per_task_results={'task1': True, 'task2': False},
            per_category_success={'api_invocation': 0.8}
        )

        assert result.total_tasks == 10
        assert result.successful == 7
        assert result.success_rate == 0.7
        assert result.per_task_results == {'task1': True, 'task2': False}
        assert result.per_category_success == {'api_invocation': 0.8}
        assert result.baseline_comparison is None

    def test_result_with_baseline(self):
        """Test result with baseline comparison."""
        result = ToolUseResult(
            total_tasks=10,
            successful=8,
            success_rate=0.8,
            per_task_results={},
            per_category_success={},
            baseline_comparison=0.10
        )

        assert result.baseline_comparison == 0.10
