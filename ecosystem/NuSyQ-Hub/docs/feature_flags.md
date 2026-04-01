# Feature Flags

The repository uses JSON-based feature flags to progressively roll out new
capabilities. Flags are defined in [`config/feature_flags.json`](../config/feature_flags.json)
and evaluated by `src.system.feature_flags`.

## Available Flags

| Flag | Default | Staging | Description |
| ---- | ------- | ------- | ----------- |
| `chatdev_autofix` | `false` | `true` | Enable ChatDev auto-fix capabilities. Roll out begins in staging environments. |

## Environment Selection

Set the `NUSYQ_ENV` environment variable to switch environments:

```bash
export NUSYQ_ENV=staging  # enable staging overrides
```

Unrecognised environments fall back to the `default` value for each flag.
