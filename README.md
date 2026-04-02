# Model Capability Plateauing Tool

A benchmarking suite to measure AI agent capabilities across reasoning, tool use, and harness quality. Helps teams detect performance plateaus and guide model selection.

## Tech Stack
- Python 3.11+
- Click (CLI framework)
- Pytest (testing)

## Features
- **Reasoning Benchmark**: Measures logical inference, planning, and decision-making
- **Tool Use Benchmark**: Assesses tool invocation and utilization effectiveness
- **Harness Quality Benchmark**: Evaluates fault tolerance, retry mechanisms, and performance

## Setup
```bash
chmod +x init.sh
./init.sh
```

## Usage
```bash
python -m benchmarks.cli --help
```

## Success Criteria
- Reasoning accuracy > 80%
- Tool use success rate > 70%
- Harness quality latency < 100ms
