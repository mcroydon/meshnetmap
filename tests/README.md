# meshnetmap Test Suite

This directory contains the pytest test suite for meshnetmap.

## Test Structure

- `conftest.py` - Pytest fixtures and shared test data
- `test_inference.py` - Tests for connection inference module
- `test_visualizer.py` - Tests for visualization components
- `test_cli.py` - Tests for CLI commands

## Running Tests

### Run all tests
```bash
uv run pytest
```

### Run specific test file
```bash
uv run pytest tests/test_inference.py
```

### Run specific test class
```bash
uv run pytest tests/test_inference.py::TestCoLocationDetection
```

### Run specific test
```bash
uv run pytest tests/test_inference.py::TestCoLocationDetection::test_find_colocated_nodes_basic
```

### Run with coverage
```bash
uv run pytest --cov=meshnetmap --cov-report=html
```

### Run tests matching a pattern
```bash
uv run pytest -k "colocated"
```

## Test Fixtures

The test suite provides several fixtures for testing:

- `sample_node` - A single test node
- `simple_topology` - Basic 3-node topology
- `colocated_topology` - Topology with co-located nodes
- `routing_evidence_topology` - Topology with routing path data
- `multi_hop_topology` - Large topology with multiple hop levels
- `topology_without_gps` - Topology where nodes lack GPS coordinates

## Test Categories

### Unit Tests
Test individual functions and methods in isolation.

### Integration Tests
Test interactions between components and end-to-end workflows.

## Writing New Tests

When adding new tests:

1. Use descriptive test names that explain what is being tested
2. Use fixtures from `conftest.py` when possible
3. Keep tests independent - don't rely on test execution order
4. Clean up any files created during tests
5. Use pytest markers for test categorization

Example:
```python
def test_my_feature(simple_topology):
    """Test description here"""
    # Arrange
    data = simple_topology

    # Act
    result = my_function(data)

    # Assert
    assert result is not None
```
