#!/usr/bin/env python3
"""Validation script to ensure comprehensive test suite is properly implemented."""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any


class TestSuiteValidator:
    """Validates that the comprehensive test suite is properly implemented."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.validation_results: Dict[str, Any] = {}
    
    def validate_directory_structure(self) -> bool:
        """Validate that all required test directories exist."""
        required_dirs = [
            "tests/unit",
            "tests/integration", 
            "tests/e2e",
            "tests/performance",
            "tests/security",
            "tests/load"
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        self.validation_results["directory_structure"] = {
            "success": len(missing_dirs) == 0,
            "missing_dirs": missing_dirs
        }
        
        return len(missing_dirs) == 0
    
    def validate_test_files(self) -> bool:
        """Validate that all required test files exist."""
        required_files = [
            # E2E tests
            "tests/e2e/conftest.py",
            "tests/e2e/test_personality_workflow.py",
            
            # Load tests
            "tests/load/locustfile.py",
            "tests/load/load_test_config.py",
            
            # Performance tests
            "tests/performance/test_personality_benchmarks.py",
            
            # Security tests
            "tests/security/test_input_validation.py",
            
            # IDE integration tests
            "tests/integration/test_ide_integration.py",
            
            # Configuration files
            "tests/conftest.py",
            "tests/README.md",
            "run_tests.py",
            "pytest.ini",
            ".coveragerc",
            ".github/workflows/test.yml"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        self.validation_results["test_files"] = {
            "success": len(missing_files) == 0,
            "missing_files": missing_files
        }
        
        return len(missing_files) == 0
    
    def validate_dependencies(self) -> bool:
        """Validate that all required test dependencies are configured."""
        pyproject_path = self.project_root / "pyproject.toml"
        
        if not pyproject_path.exists():
            self.validation_results["dependencies"] = {
                "success": False,
                "error": "pyproject.toml not found"
            }
            return False
        
        content = pyproject_path.read_text()
        
        required_deps = [
            "pytest",
            "pytest-asyncio", 
            "pytest-cov",
            "pytest-mock",
            "pytest-benchmark",
            "playwright",
            "locust",
            "memory-profiler",
            "bandit"
        ]
        
        missing_deps = []
        for dep in required_deps:
            if dep not in content:
                missing_deps.append(dep)
        
        self.validation_results["dependencies"] = {
            "success": len(missing_deps) == 0,
            "missing_deps": missing_deps
        }
        
        return len(missing_deps) == 0
    
    def validate_test_content(self) -> bool:
        """Validate that test files contain expected content."""
        validations = []
        
        # Check E2E test has Playwright imports
        e2e_test = self.project_root / "tests/e2e/test_personality_workflow.py"
        if e2e_test.exists():
            content = e2e_test.read_text()
            has_playwright = "playwright" in content.lower()
            validations.append(("E2E Playwright integration", has_playwright))
        
        # Check load test has Locust classes
        load_test = self.project_root / "tests/load/locustfile.py"
        if load_test.exists():
            content = load_test.read_text()
            has_locust = "HttpUser" in content and "task" in content
            validations.append(("Load test Locust integration", has_locust))
        
        # Check performance test has benchmarks
        perf_test = self.project_root / "tests/performance/test_personality_benchmarks.py"
        if perf_test.exists():
            content = perf_test.read_text()
            has_benchmark = "benchmark" in content.lower()
            validations.append(("Performance benchmarking", has_benchmark))
        
        # Check security test has security validations
        sec_test = self.project_root / "tests/security/test_input_validation.py"
        if sec_test.exists():
            content = sec_test.read_text()
            has_security = "sql_injection" in content.lower() and "xss" in content.lower()
            validations.append(("Security test coverage", has_security))
        
        all_valid = all(valid for _, valid in validations)
        
        self.validation_results["test_content"] = {
            "success": all_valid,
            "validations": validations
        }
        
        return all_valid
    
    def validate_configuration(self) -> bool:
        """Validate test configuration files."""
        validations = []
        
        # Check pytest.ini
        pytest_ini = self.project_root / "pytest.ini"
        if pytest_ini.exists():
            content = pytest_ini.read_text()
            has_markers = "markers" in content
            has_coverage = "cov" in content
            validations.append(("pytest.ini markers", has_markers))
            validations.append(("pytest.ini coverage", has_coverage))
        
        # Check .coveragerc
        coveragerc = self.project_root / ".coveragerc"
        if coveragerc.exists():
            content = coveragerc.read_text()
            has_source = "source" in content
            has_omit = "omit" in content
            validations.append((".coveragerc source", has_source))
            validations.append((".coveragerc omit", has_omit))
        
        # Check GitHub Actions workflow
        workflow = self.project_root / ".github/workflows/test.yml"
        if workflow.exists():
            content = workflow.read_text()
            has_jobs = "jobs:" in content
            has_pytest = "pytest" in content
            validations.append(("GitHub Actions jobs", has_jobs))
            validations.append(("GitHub Actions pytest", has_pytest))
        
        all_valid = all(valid for _, valid in validations)
        
        self.validation_results["configuration"] = {
            "success": all_valid,
            "validations": validations
        }
        
        return all_valid
    
    def validate_test_runner(self) -> bool:
        """Validate the comprehensive test runner."""
        runner_path = self.project_root / "run_tests.py"
        
        if not runner_path.exists():
            self.validation_results["test_runner"] = {
                "success": False,
                "error": "run_tests.py not found"
            }
            return False
        
        content = runner_path.read_text()
        
        required_features = [
            ("Unit tests", "run_unit_tests"),
            ("Integration tests", "run_integration_tests"),
            ("E2E tests", "run_e2e_tests"),
            ("Performance tests", "run_performance_tests"),
            ("Security tests", "run_security_tests"),
            ("Load tests", "run_load_tests"),
            ("Static analysis", "run_static_analysis"),
            ("Frontend tests", "run_frontend_tests")
        ]
        
        missing_features = []
        for feature_name, feature_method in required_features:
            if feature_method not in content:
                missing_features.append(feature_name)
        
        self.validation_results["test_runner"] = {
            "success": len(missing_features) == 0,
            "missing_features": missing_features
        }
        
        return len(missing_features) == 0
    
    def run_validation(self) -> bool:
        """Run all validations and return overall success."""
        print("🔍 Validating comprehensive test suite...")
        
        validations = [
            ("Directory Structure", self.validate_directory_structure),
            ("Test Files", self.validate_test_files),
            ("Dependencies", self.validate_dependencies),
            ("Test Content", self.validate_test_content),
            ("Configuration", self.validate_configuration),
            ("Test Runner", self.validate_test_runner)
        ]
        
        all_passed = True
        
        for validation_name, validation_func in validations:
            print(f"\n📋 {validation_name}:")
            success = validation_func()
            
            if success:
                print(f"  ✅ {validation_name} validation passed")
            else:
                print(f"  ❌ {validation_name} validation failed")
                result = self.validation_results.get(validation_name.lower().replace(" ", "_"))
                if result:
                    if "missing_dirs" in result:
                        print(f"     Missing directories: {result['missing_dirs']}")
                    if "missing_files" in result:
                        print(f"     Missing files: {result['missing_files']}")
                    if "missing_deps" in result:
                        print(f"     Missing dependencies: {result['missing_deps']}")
                    if "missing_features" in result:
                        print(f"     Missing features: {result['missing_features']}")
                    if "error" in result:
                        print(f"     Error: {result['error']}")
                    if "validations" in result:
                        for val_name, val_success in result["validations"]:
                            status = "✅" if val_success else "❌"
                            print(f"     {status} {val_name}")
            
            all_passed &= success
        
        return all_passed
    
    def generate_summary(self) -> None:
        """Generate a summary of the validation results."""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE TEST SUITE VALIDATION SUMMARY")
        print("="*60)
        
        total_validations = len(self.validation_results)
        passed_validations = sum(1 for r in self.validation_results.values() if r.get("success", False))
        
        print(f"Total validations: {total_validations}")
        print(f"Passed validations: {passed_validations}")
        print(f"Failed validations: {total_validations - passed_validations}")
        
        if passed_validations == total_validations:
            print("\n🎉 All validations passed! Comprehensive test suite is properly implemented.")
            print("\n📝 Test suite includes:")
            print("   • End-to-end testing with Playwright")
            print("   • API load testing with Locust")
            print("   • IDE integration tests")
            print("   • Performance benchmarks")
            print("   • Security testing")
            print("   • Comprehensive test runner")
            print("   • CI/CD integration")
            print("\n🚀 You can now run tests with: python run_tests.py --all")
        else:
            print("\n⚠️  Some validations failed. Please address the issues above.")
            return False
        
        return True


def main():
    """Main validation function."""
    validator = TestSuiteValidator()
    success = validator.run_validation()
    validator.generate_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()