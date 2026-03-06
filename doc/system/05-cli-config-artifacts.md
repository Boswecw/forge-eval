# §5 - CLI, Config, and Artifacts

## CLI Commands

```bash
forge-eval run --repo /path/to/repo --base <base> --head <head> --config config.yaml --out artifacts/
forge-eval validate --artifacts artifacts/
```

## Config Loading and Normalization

- Accepted formats: `.json`, `.yaml`, `.yml`
- Unknown keys are rejected.
- Stage list is validated against known stage set.
- Risk weights are normalized to a deterministic unit sum.
- File-extension and excluded-path lists are normalized and sorted.

Default stage order and enabled set:

1. `risk_heatmap`
2. `context_slices`

## Pack F Config Keys (Current)

- `context_radius_lines` (int, >=0)
- `merge_gap_lines` (int, >=0)
- `max_slices_per_target` (int, >=1)
- `max_lines_per_slice` (int, >=1)
- `max_total_lines` (int, >=1)
- `fail_on_slice_truncation` (bool)
- `include_file_extensions` (normalized unique list)
- `exclude_paths` (normalized unique list, trailing `/`)
- `binary_file_policy` (`fail` or `ignore`)

## Artifacts Written by `run`

- `config.resolved.json`
- `risk_heatmap.json` (if enabled)
- `context_slices.json` (if enabled)

All Python-written artifacts use deterministic JSON encoding:

- sorted keys
- compact separators
- single trailing newline
