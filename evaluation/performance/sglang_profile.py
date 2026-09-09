#!/usr/bin/env python3
"""SGLang profiling entry; shares diagnostic lifecycle and failure checks.

Set SGLANG_TORCH_PROFILER_DIR on the server and provide its locally visible
trace directory via --profile-dir. See evaluation/performance/README.md.
"""
from vllm_profile import main


if __name__ == '__main__':
    main(engine='sglang')
