# Comprehensive Test Suite

This directory contains a comprehensive test suite for the Agent Personality System, covering all aspects of functionality, performance, security, and user experience.

## Test Structure

```
tests/
├── unit/                   # Unit tests for individual components
├── integration/            # Integration tests for component interactions
├── e2e/                   # End-to-end tests with Playwright
├── performance/           # Performance benchmarks and load tests
├── security/              # Security and vulnerability tests
├── load/                  # Load testing with Locust
├── conftest.py           # Global test configuration
└── README.md             # This file
```

## Test Types

### 1. Unit Tests (`tests/unit/`)
- Test individual functions and classes in isolation
- Mock external dependencies
- Fast execution (< 1 second per test)
- High code coverage target (90%+)

**Run with:**
```bash
python -m pytest tests/unit/ -v --cov=src/covibe
```

### 2. Integration Tests (`tests/integration/`)
- Test component interactions
- Use real dependencies where appropriate
- Test API endpoints end-to-end
- Validate data flow between services

**Run with:**
```bash
python -m pytest tests/integration/ -v
```

### 3. End-to-End Tests (`tests/e2e/`)
- Test complete user workflows using Playwright
- Cross-browser compatibility testing
- Accessibility compliance testing
- Real user interaction simulation

**Run with:**
```bash
python -m pytest tests/e2e/ -v
```

**Prerequisites:**
```bash
pip install playwright
python -m playwright install
```

### 4. Performance Tests (`tests/performance/`)
- Benchmark critical operations
- Memory usage profiling
- Scalability testing
- Performance regression detection

**Run with:**
```bash
python -m pytest tests/performance/ -v --benchmark-only
```

### 5. Security Tests (`tests/security/`)
- Input validation testing
- SQL injection prevention
- XSS prevention
- Path traversal protection
- Authentication bypass attempts

**Run with:**
```bash
python -m pytest tests/security/ -v
```

### 6. Load Tests (`tests/load/`)
- API load testing with Locust
- Concurrent user simulation
- Performance under stress
- Resource utilization monitoring

**Run with:**
```bash
python tests/load/load_test_config.py smoke_test
```

## Test Execution

### Quick Test Run
```bash
# Run all tests
python run_tests.py --all

# Run specific test types
python run_tests.py --unit --integration
python run_tests.py --e2e
python run_tests.py --performance
python run_tests.py --security
python run_tests.py --load
```

### Detailed Test Options
```bash
# Unit tests with coverage
python -m pytest tests/unit/ --cov=src/covibe --cov-report=html

# Integration tests with verbose output
python -m pytest tests/integration/ -v -s

# E2E tests with specific browser
python -m pytest tests/e2e/ --browser=firefox

# Performance tests with benchmarking
python -m pytest tests/performance/ --benchmark-sort=mean

# Security tests with detailed output
python -m pytest tests/security/ -v --tb=long

# Load tests with custom scenario
python tests/load/load_test_config.py peak_load
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)
- Test discovery settings
- Coverage configuration
- Marker definitions
- Timeout settings

### Coverage Configuration (`.coveragerc`)
- Source code paths
- Exclusion patterns
- Report formats
- Minimum coverage thresholds

### Environment Variables
```bash
# Test environment
export TESTING=true
export DATABASE_URL=sqlite:///test.db

# API testing
export API_BASE_URL=http://localhost:8000
export TEST_API_KEY=test_key_123

# E2E testing
export FRONTEND_URL=http://localhost:3000
export HEADLESS=true
```

## Test Data and Fixtures

### Global Fixtures (`conftest.py`)
- Database setup/teardown
- Test client creation
- Temporary directories
- Sample data generation

### Test Data
- Sample personality configurations
- Mock API responses
- Test user accounts
- IDE project structures

## Continuous Integration

### GitHub Actions (`.github/workflows/test.yml`)
- Automated test execution on push/PR
- Multi-Python version testing
- Cross-platform compatibility
- Test result reporting
- Coverage tracking

### Test Stages
1. **Static Analysis** - Linting, type checking, security scanning
2. **Unit Tests** - Fast, isolated component tests
3. **Integration Tests** - Component interaction validation
4. **Frontend Tests** - React component and integration tests
5. **Security Tests** - Vulnerability and input validation tests
6. **Performance Tests** - Benchmarking and performance regression
7. **E2E Tests** - Full user workflow validation
8. **Load Tests** - Stress testing and scalability validation

## Test Metrics and Reporting

### Coverage Reports
- HTML coverage report: `htmlcov/index.html`
- XML coverage report: `coverage.xml`
- Terminal coverage summary

### Performance Reports
- Benchmark results with statistical analysis
- Memory usage profiling
- Performance trend tracking

### Load Test Reports
- HTML reports with graphs and statistics
- CSV data for analysis
- Resource utilization metrics

### Security Reports
- Vulnerability scan results
- Input validation test results
- Security compliance status

## Best Practices

### Writing Tests
1. **Arrange-Act-Assert** pattern
2. **Descriptive test names** that explain the scenario
3. **Independent tests** that don't rely on each other
4. **Appropriate mocking** to isolate units under test
5. **Edge case coverage** including error conditions

### Test Organization
1. **Group related tests** in classes
2. **Use fixtures** for common setup
3. **Parameterize tests** for multiple scenarios
4. **Mark tests appropriately** (slow, integration, etc.)

### Performance Testing
1. **Establish baselines** for performance metrics
2. **Test realistic scenarios** with appropriate data volumes
3. **Monitor resource usage** (CPU, memory, I/O)
4. **Set performance thresholds** and fail on regressions

### Security Testing
1. **Test all input vectors** (API, forms, files)
2. **Validate authentication** and authorization
3. **Check for common vulnerabilities** (OWASP Top 10)
4. **Test error handling** doesn't expose sensitive data

## Troubleshooting

### Common Issues

**Tests failing locally but passing in CI:**
- Check environment variables
- Verify dependency versions
- Check file permissions
- Review test isolation

**Slow test execution:**
- Use pytest-xdist for parallel execution
- Optimize database operations
- Mock expensive external calls
- Profile test execution

**Flaky E2E tests:**
- Add explicit waits for elements
- Use stable selectors
- Handle async operations properly
- Increase timeouts for slow operations

**Memory issues in performance tests:**
- Use memory profiling tools
- Check for memory leaks
- Optimize data structures
- Clean up resources properly

### Debug Commands
```bash
# Run tests with debugging
python -m pytest tests/unit/ -v -s --pdb

# Profile test execution
python -m pytest tests/performance/ --profile

# Run specific test with verbose output
python -m pytest tests/integration/test_api_endpoints.py::TestPersonalityAPI::test_create_personality -v -s

# Check test coverage for specific module
python -m pytest tests/unit/test_research.py --cov=src.covibe.services.research --cov-report=term-missing
```

## Contributing

When adding new features:
1. **Write tests first** (TDD approach)
2. **Ensure all test types** are covered
3. **Update test documentation** as needed
4. **Verify CI passes** before merging
5. **Maintain coverage thresholds**

For test improvements:
1. **Identify gaps** in current coverage
2. **Add missing test scenarios**
3. **Improve test performance** where possible
4. **Enhance test reliability**
5. **Update documentation**