# Lightweight Python Profiler

A sampling-free call profiler using `sys.setprofile` and `perf_counter_ns`. It aggregates elapsed nanoseconds by folded call stack and renders an SVG flame view. Use it on a module or a Python script:

```sh
python profiler.py examples/workload.py --folded trace.folded --svg flame.svg
python -m unittest discover -s tests -v
```

The folded output is compatible with flame graph tooling. Width represents inclusive time aggregated at each stack. Python trace hooks add overhead, so measurements are best for comparing broad call paths rather than microbenchmarks. The included renderer escapes labels and supports hover tooltips.

