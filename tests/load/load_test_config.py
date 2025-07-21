"""Load testing configuration and utilities."""

import json
import time
from typing import Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class LoadTestConfig:
    """Configuration for load testing scenarios."""
    name: str
    users: int
    spawn_rate: int
    duration: int  # seconds
    host: str
    description: str


# Predefined load testing scenarios
LOAD_TEST_SCENARIOS = [
    LoadTestConfig(
        name="smoke_test",
        users=5,
        spawn_rate=1,
        duration=60,
        host="http://localhost:8000",
        description="Basic smoke test with minimal load"
    ),
    LoadTestConfig(
        name="normal_load",
        users=50,
        spawn_rate=5,
        duration=300,
        host="http://localhost:8000", 
        description="Normal usage load test"
    ),
    LoadTestConfig(
        name="peak_load",
        users=200,
        spawn_rate=10,
        duration=600,
        host="http://localhost:8000",
        description="Peak usage load test"
    ),
    LoadTestConfig(
        name="stress_test",
        users=500,
        spawn_rate=20,
        duration=900,
        host="http://localhost:8000",
        description="Stress test to find breaking points"
    ),
    LoadTestConfig(
        name="endurance_test",
        users=100,
        spawn_rate=5,
        duration=3600,
        host="http://localhost:8000",
        description="Long-running endurance test"
    )
]


class LoadTestReporter:
    """Utility class for generating load test reports."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
    
    def add_result(self, scenario: str, metrics: Dict[str, Any]):
        """Add test results for a scenario."""
        result = {
            "scenario": scenario,
            "timestamp": time.time(),
            "metrics": metrics
        }
        self.results.append(result)
    
    def generate_report(self, output_file: str = "load_test_report.json"):
        """Generate a comprehensive load test report."""
        report = {
            "test_run_timestamp": time.time(),
            "scenarios": self.results,
            "summary": self._generate_summary()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics across all scenarios."""
        if not self.results:
            return {}
        
        total_requests = sum(r["metrics"].get("total_requests", 0) for r in self.results)
        total_failures = sum(r["metrics"].get("total_failures", 0) for r in self.results)
        
        return {
            "total_scenarios": len(self.results),
            "total_requests": total_requests,
            "total_failures": total_failures,
            "overall_failure_rate": total_failures / total_requests if total_requests > 0 else 0,
            "scenarios_tested": [r["scenario"] for r in self.results]
        }


def run_load_test_scenario(scenario: LoadTestConfig) -> Dict[str, Any]:
    """Run a specific load test scenario."""
    import subprocess
    import tempfile
    import os
    
    # Create temporary stats file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        stats_file = f.name
    
    try:
        # Run locust with the specified configuration
        cmd = [
            "locust",
            "-f", "tests/load/locustfile.py",
            "--host", scenario.host,
            "--users", str(scenario.users),
            "--spawn-rate", str(scenario.spawn_rate),
            "--run-time", f"{scenario.duration}s",
            "--headless",
            "--csv", stats_file.replace('.csv', ''),
            "--html", f"load_test_report_{scenario.name}.html"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse results from CSV files
        metrics = _parse_locust_results(stats_file.replace('.csv', ''))
        
        return {
            "success": result.returncode == 0,
            "metrics": metrics,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    finally:
        # Cleanup temporary files
        for ext in ['_stats.csv', '_failures.csv', '_exceptions.csv']:
            try:
                os.unlink(stats_file.replace('.csv', ext))
            except FileNotFoundError:
                pass


def _parse_locust_results(base_filename: str) -> Dict[str, Any]:
    """Parse Locust CSV results into metrics dictionary."""
    import csv
    
    metrics = {
        "total_requests": 0,
        "total_failures": 0,
        "average_response_time": 0,
        "requests_per_second": 0,
        "endpoints": {}
    }
    
    # Parse stats file
    stats_file = f"{base_filename}_stats.csv"
    try:
        with open(stats_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Type'] == 'Aggregated':
                    metrics["total_requests"] = int(row['Request Count'])
                    metrics["total_failures"] = int(row['Failure Count'])
                    metrics["average_response_time"] = float(row['Average Response Time'])
                    metrics["requests_per_second"] = float(row['Requests/s'])
                else:
                    metrics["endpoints"][row['Name']] = {
                        "requests": int(row['Request Count']),
                        "failures": int(row['Failure Count']),
                        "avg_response_time": float(row['Average Response Time']),
                        "min_response_time": float(row['Min Response Time']),
                        "max_response_time": float(row['Max Response Time'])
                    }
    except FileNotFoundError:
        pass
    
    return metrics


if __name__ == "__main__":
    """Run load tests from command line."""
    import sys
    
    if len(sys.argv) > 1:
        scenario_name = sys.argv[1]
        scenario = next((s for s in LOAD_TEST_SCENARIOS if s.name == scenario_name), None)
        if scenario:
            print(f"Running load test scenario: {scenario.name}")
            result = run_load_test_scenario(scenario)
            print(f"Test completed. Success: {result['success']}")
            if result['metrics']:
                print(f"Total requests: {result['metrics']['total_requests']}")
                print(f"Total failures: {result['metrics']['total_failures']}")
                print(f"Average response time: {result['metrics']['average_response_time']}ms")
        else:
            print(f"Unknown scenario: {scenario_name}")
            print("Available scenarios:", [s.name for s in LOAD_TEST_SCENARIOS])
    else:
        print("Available load test scenarios:")
        for scenario in LOAD_TEST_SCENARIOS:
            print(f"  {scenario.name}: {scenario.description}")
        print("\nUsage: python load_test_config.py <scenario_name>")