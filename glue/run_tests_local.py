"""
Run Property-Based Tests Locally

This script runs all property-based tests in a local environment
without needing AWS infrastructure.

Usage:
    python run_tests_local.py
    python run_tests_local.py --test roundtrip
    python run_tests_local.py --test acid
    python run_tests_local.py --test timetravel
"""

import sys
import subprocess
import argparse


def check_localstack():
    """Check if LocalStack is running."""
    import requests
    try:
        response = requests.get("http://localhost:4566/_localstack/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def run_pytest(test_file=None, verbose=True):
    """Run pytest with appropriate configuration."""
    cmd = ["pytest"]
    
    if test_file:
        cmd.append(f"tests/property/{test_file}")
    else:
        cmd.append("tests/property/")
    
    if verbose:
        cmd.append("-v")
    
    # Add hypothesis statistics
    cmd.append("--hypothesis-show-statistics")
    
    # Add coverage
    cmd.extend(["--cov=modules", "--cov-report=term-missing"])
    
    print(f"🧪 Running: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd, cwd=".")
    
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run local property-based tests")
    parser.add_argument(
        "--test",
        choices=["roundtrip", "acid", "timetravel", "all"],
        default="all",
        help="Which test suite to run"
    )
    parser.add_argument(
        "--no-localstack-check",
        action="store_true",
        help="Skip LocalStack health check"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧪 Local Property-Based Test Runner")
    print("=" * 60)
    
    # Check LocalStack
    if not args.no_localstack_check:
        print("\n🔍 Checking LocalStack...")
        if check_localstack():
            print("✅ LocalStack is running")
        else:
            print("❌ LocalStack is not running!")
            print("   Start it with: docker-compose -f docker-compose.localstack.yml up -d")
            sys.exit(1)
    
    # Map test names to files
    test_files = {
        "roundtrip": "test_iceberg_roundtrip.py",
        "acid": "test_iceberg_acid.py",
        "timetravel": "test_iceberg_timetravel.py",
        "all": None
    }
    
    test_file = test_files.get(args.test)
    
    print(f"\n🚀 Running {args.test} tests...\n")
    
    # Run tests
    exit_code = run_pytest(test_file)
    
    if exit_code == 0:
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed")
        print("=" * 60)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
