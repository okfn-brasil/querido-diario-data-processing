#!/usr/bin/env python3
"""
Instrumented test runner that logs test execution details.
Helps debug slow or hanging tests in CI.
"""

import sys
import time
import unittest


class InstrumentedTestResult(unittest.TextTestResult):
    """Test result that logs detailed timing and progress."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_times = []
        self.current_test_start = None

    def startTest(self, test):
        self.current_test_start = time.time()
        test_name = self.getDescription(test)
        print(f"\n{'=' * 70}", flush=True)
        print(f"▶ STARTING: {test_name}", flush=True)
        print(f"  Time: {time.strftime('%H:%M:%S')}", flush=True)
        print(f"{'=' * 70}", flush=True)
        super().startTest(test)

    def stopTest(self, test):
        duration = time.time() - self.current_test_start
        test_name = self.getDescription(test)
        self.test_times.append((test_name, duration))

        print(f"\n{'-' * 70}", flush=True)
        print(f"✓ FINISHED: {test_name}", flush=True)
        print(f"  Duration: {duration:.2f}s", flush=True)
        print(f"{'-' * 70}\n", flush=True)
        super().stopTest(test)

    def addSuccess(self, test):
        print("✅ SUCCESS", flush=True)
        super().addSuccess(test)

    def addError(self, test, err):
        print("❌ ERROR", flush=True)
        super().addError(test, err)

    def addFailure(self, test, err):
        print("❌ FAILURE", flush=True)
        super().addFailure(test, err)

    def addSkip(self, test, reason):
        print(f"⏭️  SKIP: {reason}", flush=True)
        super().addSkip(test, reason)

    def printErrors(self):
        super().printErrors()

        # Print timing summary
        if self.test_times:
            print(f"\n\n{'=' * 70}", flush=True)
            print("⏱️  TEST TIMING SUMMARY", flush=True)
            print(f"{'=' * 70}", flush=True)

            # Sort by duration
            sorted_times = sorted(self.test_times, key=lambda x: x[1], reverse=True)

            print("\nSlowest tests:", flush=True)
            for test_name, duration in sorted_times[:10]:
                print(f"  {duration:6.2f}s - {test_name}", flush=True)

            total_time = sum(d for _, d in self.test_times)
            print(
                f"\nTotal test time: {total_time:.2f}s ({total_time / 60:.1f} minutes)",
                flush=True,
            )
            print(f"{'=' * 70}\n", flush=True)


class InstrumentedTestRunner(unittest.TextTestRunner):
    """Test runner that uses our instrumented result class."""

    resultclass = InstrumentedTestResult


if __name__ == "__main__":
    print("=" * 70, flush=True)
    print("🔍 INSTRUMENTED TEST RUNNER STARTING", flush=True)
    print(f"   Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 70, flush=True)

    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = "tests"
    pattern = "*_tests.py"

    print(f"\n📁 Discovering tests in: {start_dir}", flush=True)
    print(f"   Pattern: {pattern}", flush=True)

    suite = loader.discover(start_dir, pattern=pattern)

    # Count tests
    def count_tests(suite):
        count = 0
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                count += count_tests(test)
            else:
                count += 1
        return count

    test_count = count_tests(suite)
    print(f"   Found: {test_count} tests\n", flush=True)

    print("=" * 70, flush=True)
    print("🚀 RUNNING TESTS", flush=True)
    print("=" * 70, flush=True)

    runner = InstrumentedTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 70, flush=True)
    print("📊 FINAL RESULTS", flush=True)
    print("=" * 70, flush=True)
    print(f"Tests run: {result.testsRun}", flush=True)
    print(
        f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}",
        flush=True,
    )
    print(f"Failures: {len(result.failures)}", flush=True)
    print(f"Errors: {len(result.errors)}", flush=True)
    print(f"Skipped: {len(result.skipped)}", flush=True)
    print("=" * 70, flush=True)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
