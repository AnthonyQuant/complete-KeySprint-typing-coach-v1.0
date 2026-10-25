"""Automated Test Runner for KeySprint Personal Typing Coach."""

import sys
import subprocess
import os

def run_suite():
    print("=" * 65)
    print("      KeySprint - Full Unit & Integration Test Suite      ")
    print("=" * 65 + "\n")

    # Command to run pytest across the tests/ directory
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]

    result = subprocess.run(cmd, text=True)

    print("\n" + "=" * 65)
    if result.returncode == 0:
        print("RESULT: ALL TESTS PASSED SUCCESSFULLY! (Core Logic Verified)")
    else:
        print(f"RESULT: TEST SUITE FAILED (Exit Code {result.returncode})")
    print("=" * 65)

    sys.exit(result.returncode)

if __name__ == "__main__":
    run_suite()