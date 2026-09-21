#!/usr/bin/env python3
"""Remove a non-schema field accidentally added to the targeted performance plan."""

from __future__ import annotations

import json
from pathlib import Path


path = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e/results/performance/"
    "20260920-p4k-d128-c64-n64-native-decode-02/config/plan.json"
)
data = json.loads(path.read_text())
data.pop("experiment_id", None)
path.write_text(json.dumps(data, indent=2) + "\n")
print(path)
