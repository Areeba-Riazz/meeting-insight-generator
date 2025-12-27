"""Script to run tests with coverage reporting."""

import subprocess
import sys
from pathlib import Path


def main():
    """Run pytest with coverage reporting."""
    backend_dir = Path(__file__).parent.parent
    
    # Run tests with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml",
        "-v",
        "--tb=short"
    ]
    
    # Add markers if specified
    if len(sys.argv) > 1:
        markers = sys.argv[1:]
        for marker in markers:
            cmd.extend(["-m", marker])
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=backend_dir)
    
    if result.returncode == 0:
        print("\n✅ All tests passed!")
        print(f"\n📊 Coverage report generated:")
        print(f"   - HTML: {backend_dir}/htmlcov/index.html")
        print(f"   - XML: {backend_dir}/coverage.xml")
    else:
        print("\n❌ Some tests failed.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()

