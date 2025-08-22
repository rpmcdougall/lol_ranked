#!/usr/bin/env python3
"""
Test runner script for League of Legends ETL unit tests
Provides easy ways to run tests with different options.
"""

import sys
import os
import subprocess
import argparse

def run_tests_with_pytest():
    """Run tests using pytest with coverage"""
    try:
        # Run pytest with coverage
        cmd = [
            sys.executable, "-m", "pytest",
            "test_etl.py",
            "-v",
            "--cov=etl",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running pytest: {e}")
        return False

def run_tests_with_unittest():
    """Run tests using unittest"""
    try:
        # Run unittest
        cmd = [sys.executable, "-m", "unittest", "test_etl", "-v"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running unittest: {e}")
        return False

def run_specific_test(test_name):
    """Run a specific test"""
    try:
        cmd = [
            sys.executable, "-m", "pytest",
            f"test_etl.py::{test_name}",
            "-v"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running specific test: {e}")
        return False

def main():
    """Main function to parse arguments and run tests"""
    parser = argparse.ArgumentParser(description="Run League of Legends ETL unit tests")
    parser.add_argument(
        "--framework", 
        choices=["pytest", "unittest"], 
        default="pytest",
        help="Testing framework to use (default: pytest)"
    )
    parser.add_argument(
        "--test", 
        type=str,
        help="Run a specific test (e.g., TestLoLDataETL.test_init_with_api_key_parameter)"
    )
    parser.add_argument(
        "--no-coverage", 
        action="store_true",
        help="Disable coverage reporting (only for pytest)"
    )
    
    args = parser.parse_args()
    
    print("League of Legends ETL Unit Tests")
    print("=" * 40)
    
    # Check if test file exists
    if not os.path.exists("test_etl.py"):
        print("Error: test_etl.py not found in current directory")
        return 1
    
    # Run specific test if requested
    if args.test:
        print(f"Running specific test: {args.test}")
        success = run_specific_test(args.test)
    else:
        # Run all tests
        if args.framework == "pytest":
            print("Running tests with pytest...")
            success = run_tests_with_pytest()
        else:
            print("Running tests with unittest...")
            success = run_tests_with_unittest()
    
    if success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 