# deploy-diff

Generates human-readable changelogs between two Docker image layers.

---

## Installation

```bash
pip install deploy-diff
```

Or install from source:

```bash
git clone https://github.com/youruser/deploy-diff.git && cd deploy-diff && pip install .
```

---

## Usage

Compare two Docker images and generate a changelog:

```bash
deploy-diff myapp:1.2.0 myapp:1.3.0
```

Use the Python API directly:

```python
from deploy_diff import compare_images

changelog = compare_images("myapp:1.2.0", "myapp:1.3.0")
print(changelog)
```

Example output:

```
## Changes from myapp:1.2.0 → myapp:1.3.0

+ Added:   /app/config/feature_flags.json
~ Modified: /app/src/server.py
- Removed: /app/legacy/old_handler.py

Package changes:
  requests  2.28.1 → 2.31.0
  flask     2.2.0  → 3.0.1
```

### Options

| Flag | Description |
|------|-------------|
| `--format json` | Output changelog as JSON |
| `--output FILE` | Write results to a file |
| `--ignore-env` | Exclude environment variable changes |

---

## Requirements

- Python 3.8+
- Docker daemon running locally

---

## License

MIT © 2024 deploy-diff contributors