# diag-011-startup-attention-cache-collision

Read-only startup diagnosis on mx-59 / qwen36-27b-fa-opt-20261012. No source/config/cache/service changes, no inference, restart or compile probe.

## Findings

The first failure occurs in native MetaX Attention FULL decode graph capture, not GDN numerical checking: `/workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/metax/impl/attention/flash_attn.py:884` expects `[64,12,256]` but receives `[64,2,256]`. EngineCore initialization and semaphore cleanup messages follow this error. Weights loaded and mixed PIECEWISE capture completed. GDN FP32 V-major prefill and FG packed decode dispatch were reached.

Current user script omits `attention_backend` from the whitelist (20 entries); both ranks log `vendor.metax`. The script has no VLLM_CACHE_ROOT override, and the log shows direct compiled graph load from `/tmp/qwen-fa-vllm-cache/torch_compile_cache/96868c4236/rank_0_0/backbone`.

The used graph equals retained historical FG graph exactly (SHA1b846d24...). Its submod7 inputs are `(key[*,2,256], sym, value[*,2,256], query[*,12,256], output)` and it performs unified_kv_cache_update separately. Historical native-clean graph SHA7336617b... has `(query[*,12,256], sym, key[*,2,256], value[*,2,256], output)` with no separate KV dependency. All3 cache_key_factors.json have identical SHA653731a6... and omit FlagOS whitelist/backend policy. Switching dispatch while reusing compiled producers/inline callees crosses this argument-layout contract; the2-vs12 head failure matches the prior diag005 cache collision, where a separate native cache restored correct query heads.

No fresh-cache launch or live tensor instrumentation was executed this turn. The static/cache/log evidence identifies the incompatible reuse; recovery of this exact user startup remains unverified. Existing FP32 wheel and Plugin source fingerprints match retained originals. Removing PYTHONPATH did not prevent imports; this traceback does not indicate a GDN FP32 numerical failure.

## Remediation boundary

Use a new dedicated VLLM_CACHE_ROOT for the current backend and let startup compile it; preserve old caches. Different dispatch sets must not share compilation artifacts without a backend/graph contract in the key. If returning to full21 FG, re-add attention_backend and use a dedicated FG cache. Neither option was applied; user currently requested analysis only. No old formal gate is rebound to the new user20/native configuration.

## Evidence

Log: `/public-flash/jinghao/qwen3.6-27B/service.log` SHA `9e22141ee4b5838ab7239d93d858cc63021707daf3842d82adf939f6f56479e4`.

Script: `/public-flash/jinghao/qwen3.6-27B/start-model-flagos.sh` SHA `49f5bdd16917afeb040f04608c7fa5c442f3de84169a64bdbdb7a539ea2a9a05`.

used: `/tmp/qwen-fa-vllm-cache/torch_compile_cache/96868c4236/rank_0_0/backbone/computation_graph.py` SHA `1b846d2407959e57ad54b6b7df72c53b64b798346a0c8e557b51d3a12fb579d3`; factorsSHA `653731a65bd7f904b08fe87765c453a55cd53ac8e41cc8a0dbbb5f7cdba9be06`.

native_clean_historical: `/tmp/qwen-fa-native-clean-vllm-cache/torch_compile_cache/96868c4236/rank_0_0/backbone/computation_graph.py` SHA `7336617b4b7156116e0f2e183636c4a866b9217a132bfd14f88ed530f60f95fc`; factorsSHA `653731a65bd7f904b08fe87765c453a55cd53ac8e41cc8a0dbbb5f7cdba9be06`.

FG_revert_historical: `/tmp/op010r2-revert-vllm-cache/torch_compile_cache/96868c4236/rank_0_0/backbone/computation_graph.py` SHA `1b846d2407959e57ad54b6b7df72c53b64b798346a0c8e557b51d3a12fb579d3`; factorsSHA `653731a65bd7f904b08fe87765c453a55cd53ac8e41cc8a0dbbb5f7cdba9be06`.

Prior hardware isolation: [diag-005](diag-005-attention-blacklist.md), startup cache diagnosis. Full trace/graphs remain at their original remote paths; only compact facts and hashes retained locally.

## Confirmed cache path origin

Read-only docker inspect shows container Config.Env has `VLLM_CACHE_ROOT=/tmp/qwen-fa-vllm-cache` and `TRITON_CACHE_DIR=/tmp/qwen-fa-triton-cache`. A fresh docker exec Python process inherits both; HOME=/root and XDG_CACHE_HOME unset. vllm/envs.py:566 reads VLLM_CACHE_ROOT first; absent that override it uses XDG_CACHE_HOME/vllm or ~/.cache/vllm (default root path /root/.cache/vllm). Removing export from a shell script does not unset its inherited container environment. No container, script, cache or service changes made.
