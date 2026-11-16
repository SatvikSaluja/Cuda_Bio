# Contributing

Use a focused branch and describe the behavior changed, scoring implications and checks performed. Run CTest, pytest and frontend build/tests. Changes to exact alignment must preserve optimality against independent DP and CIGAR replay. Do not compare CIGAR strings when alternative optimal paths are valid.

GPU changes require actual GPU execution, toolkit/driver/architecture details and Compute Sanitizer checks. Mark unavailable hardware checks explicitly. Benchmark changes need seeds, raw repeats, hardware, scoring conventions and baseline versions. Never substitute published speedups for measurements of this code.

Keep dependencies optional across C++/Python/Studio boundaries. Use synthetic, licensed fixtures and never submit private sequencing data, credentials or generated binaries. Contributions are accepted under the MIT license. See docs/limitations.md for prioritized unfinished work.
