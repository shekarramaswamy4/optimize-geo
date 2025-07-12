#!/usr/bin/env python3
"""Script to run tests with various configurations."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd: list[str], env: dict | None = None) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    return result.returncode


def main():
    """Run tests based on command line arguments."""
    parser = argparse.ArgumentParser(description="Run website analyzer tests")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "performance", "all"],
        default="all",
        help="Type of tests to run",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage reporting",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--failfast",
        "-x",
        action="store_true",
        help="Stop on first failure",
    )
    parser.add_argument(
        "--parallel",
        "-n",
        type=int,
        help="Number of parallel workers",
    )
    parser.add_argument(
        "--markers",
        "-m",
        help="Pytest markers to run",
    )
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ["poetry", "run", "pytest"]
    
    # Add test directory based on type
    if args.type == "unit":
        cmd.append("tests/unit")
    elif args.type == "integration":
        cmd.append("tests/integration")
    elif args.type == "performance":
        cmd.extend(["tests/test_performance.py", "-m", "benchmark"])
    elif args.type == "all":
        cmd.append("tests")
    
    # Add options
    if args.coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-report=html"])
    
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")
    
    if args.failfast:
        cmd.append("-x")
    
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    # Set test environment
    env = os.environ.copy()
    env["ENVIRONMENT"] = "testing"
    env["OPENAI_API_KEY"] = "test-key"
    
    # Run tests
    exit_code = run_command(cmd, env)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
        
        if args.coverage:
            print("\n📊 Coverage report generated in htmlcov/index.html")
    else:
        print("\n❌ Tests failed!")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())