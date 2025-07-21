#!/usr/bin/env python3
"""Comprehensive test runner for the Agent Personality System."""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any


class TestRunner:
    """Comprehensive test runner with multiple test types."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results: Dict[str, Any] = {}
    
    def run_unit_tests(self, coverage: bool = True) -> bool:
        """Run unit tests with optional coverage."""
        print("🧪 Running unit tests...")
        
        cmd = ["python", "-m", "pytest", "tests/unit/", "-v"]
        
        if coverage:
            cmd.extend(["--cov=src/covibe", "--cov-report=html", "--cov-report=term"])
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        self.results["unit_tests"] = {
            "success": success,
            "command": " ".join(cmd)
        }
        
        return success
    
    def run_integration_tests(self) -> bool:
        """Run integration tests."""
        print("🔗 Running integration tests...")
        
        cmd = ["python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        self.results["integration_tests"] = {
            "success": success,
            "command": " ".join(cmd)
        }
        
        return success
    
    def run_e2e_tests(self) -> bool:
        """Run end-to-end tests with Playwright."""
        print("🌐 Running end-to-end tests...")
        
        # Install Playwright browsers if needed
        print("Installing Playwright browsers...")
        subprocess.run(["python", "-m", "playwright", "install"], cwd=self.project_root)
        
        cmd = ["python", "-m", "pytest", "tests/e2e/", "-v", "--tb=short"]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        self.results["e2e_tests"] = {
            "success": success,
            "command": " ".join(cmd)
        }
        
        return success
    
    def run_performance_tests(self) -> bool:
        """Run performance benchmarks."""
        print("⚡ Running performance tests...")
        
        cmd = [
            "python", "-m", "pytest", "tests/performance/", 
            "-v", "--benchmark-only", "--benchmark-sort=mean"
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        self.results["performance_tests"] = {
            "success": success,
            "command": " ".join(cmd)
        }
        
        return success
    
    def run_security_tests(self) -> bool:
        """Run security tests."""
        print("🔒 Running security tests...")
        
        cmd = ["python", "-m", "pytest", "tests/security/", "-v", "--tb=short"]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        self.results["security_tests"] = {
            "success": success,
            "command": " ".join(cmd)
        }
        
        return success
    
    def run_load_tests(self, scenario: str = "smoke_test") -> bool:
        """Run load tests with Locust."""
        print(f"📈 Running load tests (scenario: {scenario})...")
        
        # Start the backend server for load testing
        print("Starting backend server...")
        server_process = subprocess.Popen([
            "python", "-m", "uvicorn", "src.covibe.api.main:app",
            "--host", "127.0.0.1", "--port", "8000"
        ], cwd=self.project_root)
        
        # Wait for server to start
        time.sleep(3)
        
        try:
            # Run load test
            cmd = ["python", "tests/load/load_test_config.py", scenario]
            result = subprocess.run(cmd, cwd=self.project_root)
            success = result.returncode == 0
            
            self.results["load_tests"] = {
                "success": success,
                "scenario": scenario,
                "command": " ".join(cmd)
            }
            
            return success
        
        finally:
            # Stop the server
            server_process.terminate()
            server_process.wait()
    
    def run_static_analysis(self) -> bool:
        """Run static analysis tools."""
        print("🔍 Running static analysis...")
        
        success = True
        
        # Run ruff for linting
        print("Running ruff...")
        result = subprocess.run(["ruff", "check", "src/", "tests/"], cwd=self.project_root)
        if result.returncode != 0:
            success = False
        
        # Run mypy for type checking
        print("Running mypy...")
        result = subprocess.run(["mypy", "src/"], cwd=self.project_root)
        if result.returncode != 0:
            success = False
        
        # Run bandit for security analysis
        print("Running bandit...")
        result = subprocess.run(["bandit", "-r", "src/"], cwd=self.project_root)
        if result.returncode != 0:
            success = False
        
        self.results["static_analysis"] = {"success": success}
        
        return success
    
    def run_frontend_tests(self) -> bool:
        """Run frontend tests."""
        print("⚛️ Running frontend tests...")
        
        web_dir = self.project_root / "web"
        
        # Install dependencies
        subprocess.run(["npm", "install"], cwd=web_dir)
        
        # Run tests
        cmd = ["npm", "run", "test:run"]
        result = subprocess.run(cmd, cwd=web_dir)
        success = result.returncode == 0
        
        self.results["frontend_tests"] = {
            "success": success,
            "command": " ".join(cmd)
        }
        
        return success
    
    def generate_report(self) -> None:
        """Generate a comprehensive test report."""
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r["success"])
        
        for test_type, result in self.results.items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"{test_type.replace('_', ' ').title():<20} {status}")
        
        print("-" * 60)
        print(f"Total: {passed_tests}/{total_tests} test suites passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
            return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run comprehensive tests for Agent Personality System")
    
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--security", action="store_true", help="Run security tests")
    parser.add_argument("--load", action="store_true", help="Run load tests")
    parser.add_argument("--frontend", action="store_true", help="Run frontend tests")
    parser.add_argument("--static", action="store_true", help="Run static analysis")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    parser.add_argument("--load-scenario", default="smoke_test", help="Load test scenario")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # If no specific tests selected, run all
    if not any([args.unit, args.integration, args.e2e, args.performance, 
                args.security, args.load, args.frontend, args.static]):
        args.all = True
    
    success = True
    
    if args.all or args.static:
        success &= runner.run_static_analysis()
    
    if args.all or args.unit:
        success &= runner.run_unit_tests(coverage=not args.no_coverage)
    
    if args.all or args.integration:
        success &= runner.run_integration_tests()
    
    if args.all or args.frontend:
        success &= runner.run_frontend_tests()
    
    if args.all or args.security:
        success &= runner.run_security_tests()
    
    if args.all or args.performance:
        success &= runner.run_performance_tests()
    
    if args.all or args.e2e:
        success &= runner.run_e2e_tests()
    
    if args.load:
        success &= runner.run_load_tests(args.load_scenario)
    
    # Generate final report
    overall_success = runner.generate_report()
    
    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()