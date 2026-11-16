# Reports

`warpalign.benchmark.save_report` writes raw JSON, CSV and an SVG runtime plot. It preserves individual repeat timings and hardware metadata. The JSON is the canonical machine-readable record. Null GPU fields mean unmeasured, not zero. Wavefront bytes are accounted algorithm storage, not process peak memory.
