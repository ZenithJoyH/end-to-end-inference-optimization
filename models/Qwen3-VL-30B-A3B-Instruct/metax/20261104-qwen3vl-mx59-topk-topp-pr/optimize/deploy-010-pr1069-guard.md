# deploy-010-pr1069-guard

Current: completed; 3filesexact039f03ed, installedhookgraphpassed, sourcepreserved, disk-onlysync(no restart).

User explicitly authorizes syncing mx-59/qwen3vl with latest PR1069. Latestfixedhead039f03ed. Only3top-k/top-p files need changes; caller already uses publicnewAPI and returnedtensor. Other6PR feature integration files remain semantically aligned; unrelated main exports cannot be wholesale copied onto existing customized environment. Preserve MoE/Plugin/Gems/engine source, dependencies, launch/environment/config and runningmodel/cache. No gitpull/reset/reinstall.

{
  "id": "deploy-010-pr1069-guard",
  "status": "prepared",
  "host": "mx-59",
  "container": "qwen3vl",
  "head": "039f03ed143914ec3a80a21394bf732118a13cf2",
  "remote_root": "/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/deploy010-pr1069-guard-20261106",
  "files": [
    {
      "asset": "backend.py",
      "path": "src/flaggems_vllm/runtime/backend/_metax/ops/top_k_top_p.py",
      "before_sha256": "0f3f4eeb160032a6832e0ac214e947bb9fe435570f4de22eb1791f63d4befbb4",
      "target_sha256": "8e34b2921baadc8c619288027f9ed1e8e14155b176b24d79edcedd671ba06f13"
    },
    {
      "asset": "tests.py",
      "path": "tests/test_top_k_top_p_metax.py",
      "before_sha256": "ea99f9209a9601a4842cf7b41fa8850a8fa5438e15e38a49c9be6f9351fe45ec",
      "target_sha256": "abb9e0f980b4dd64460e40100e82b8c830dbf9bea65d8e9d1e1f7adc63d6845b"
    },
    {
      "asset": "benchmark.py",
      "path": "benchmark/test_top_k_top_p_metax.py",
      "before_sha256": "f54b766dc2e95b6042ec97a7e06a580b76e3ff0817639af9002644be8aa1e311",
      "target_sha256": "68961c3dd85a7e24f4406b31a18a7410f08802bcfc95ac15e9f088dd6e99fcb2"
    }
  ],
  "authorization": "User explicitly requests syncing current container to PR1069; retain unrelated source/config/customizations and preserve live model",
  "scope": "only changed PR top-k/top-p backend, test, benchmark; public interfaces already aligned, no main checkout/merge/dependency change or MoE/Plugin edit",
  "preconditions": "exact current container ID/expected old3SHA/privateunmountedworkspace/live service identity, GPU3free",
  "install": "backupall3 and permissions; expectedSHA guard; atomicperfile os.replace; rollback3 on any validationerror",
  "validation": "publishedbyteSHA + installedpublicactualPlugin12capture/36changed-inputreplay/inputRNG/kwargs/idempotence/fallback/errorpropagation; identical134UT/44perf evidence from op009 retained, no repeated fullperf/GPQA",
  "preserved": "no restart/stop/modelrequests/cacheclear; sourcePID/ticks/argv/env/models200/config unchanged; only declaredbackend differs in sourcepackage tree",
  "effective_state": "disknew for next process; existing loaded opt17 remains olduntiluserrestart",
  "commands_sha256": {
    "backend.py": "8e34b2921baadc8c619288027f9ed1e8e14155b176b24d79edcedd671ba06f13",
    "controller.py": "8470715a77d36aed3f341175888cb82af77650ff7ad1619ffca06b67c73998f9",
    "benchmark.py": "68961c3dd85a7e24f4406b31a18a7410f08802bcfc95ac15e9f088dd6e99fcb2",
    "integration.py": "29a3f04287620f4e26368c0085deec630ec2d8d64cc02a4e9195ffc6da7f73bb",
    "files.json": "e6e67b0e155c1f7ec40ee3ca00677d9ad2b8a5672fc5567a4446f9b57fade65b",
    "install.py": "d198458f5bcb251330b1de2b746ad70aea9e4fb3d2e42cc153b585a016de658b",
    "tests.py": "abb9e0f980b4dd64460e40100e82b8c830dbf9bea65d8e9d1e1f7adc63d6845b",
    "identity.py": "f9e69f7ce528028349fc65e1ca7200f872cbde7ef1f619bb5975ee55a8f73ab5"
  }
}

Installed graph/interface verification on freeGPU3 in a separateprocess inside targetcontainer, original modelGPU0/1 untouched. Existing code objects are not reloaded or model restarted; disk synchronization is not a claim currentmodel uses the newguard. No fullmodelgraph/accuracy/performance gate. Minimal correctness verification uses already validated code plus actual installedcaller path. Original134UT/48bitwise/44performance evidence in op009 bound by exactcodeSHA/stack; no repetition without changes. On failure automatically restore3backedup files, no service stop.

Immutable upload/unique controller launcher `/tmp/qwen3vl-pr1069-sync-20261106/upload.py` SHA256 `59ef6ff64c939a698a5a99f93d4c081c3916587a4d20ed7315f65c633f6912fd`.

Launcher pre-execution name audit: command is commands/controller.py, backupsdirectory included. Final launcherSHA256 `56cab241b11198a586c96f5d197a7605490a2b264dd42633573b7e7cd13b0440`.

Independent final read-only/CPU audit command commands/final_audit.py SHA256 `ce7602bc1d6fe64684ea4f5ea9d1a52de83cce09641826386136ea71bac2e053`; checks all3published fileSHA/currentfullsource/config/PIDmodels200, confirms12capture/36replay and untouchedotherpackages. No GPU/model requests.
Audit transport script SHA256 `0236f0ef481043be0237129bd81f3f92bff077197fe4324a406e5eeb69d7d5bb`.

## Completed

Latesthead039f03ed synchronized to mx-59/qwen3vl: backend, functionaltest andbenchmark all exactbyteSHA to publishedPR. Other PR feature integrations already aligned (publicsignature/export/nonATen dispatch/reference), so no wholesale main files or MoE/Plugin customizations replaced. Repository HEAD/branch intentionally unchanged; this is scopedfile synchronization, not claiming entire repo equals PRtree.

Actual installedPluginhook verification on physicalGPU3 passed12captures/36fresh-inputreplays, keywordp/k routing, returnedtensor, input/RNG preservation, idempotentregistration, unsupportedpreexecutionfallback and errorpropagationwithoutretry. TestedM1/V4096,M8/V151936,M31/V131072,M32/V131071,M32/V131072,M64/V151936 withBF16grid/FP32 distributions. Independentread-only auditpassed all3fileSHA/currentimports/currentfullsource/packagefingerprints/containerconfig/modeltokenizer/PIDticksargvenv/modelsHTTP200. Zero source stop/restart/modelrequests, prefixcache unchanged. GPU0/1runningopt17 untouched; GPU3validationwas separateprocess. This is operator/callergraph, not modelgraph/fullGPQA/ERQA/newperformancegate.

Current state: diskcode has guardedprefix m>=32 and n>=131072; currentlyrunningmodelprocesswas not restarted/reloaded and therefore not claimed to use newcode. Nextservice startloads latestdiskcode. No pipinstall/gitpull/reset or dependencychange. Backupsoriginal3filesunderremote backups/; restorecommand is dockerexec qwen3vl /opt/conda/bin/python <remote>/commands/install.py restore, with SHAguards against overwriting later changes. No rollbackneeded.

- `src/flaggems_vllm/runtime/backend/_metax/ops/top_k_top_p.py`: `8e34b2921baadc8c619288027f9ed1e8e14155b176b24d79edcedd671ba06f13`
- `tests/test_top_k_top_p_metax.py`: `abb9e0f980b4dd64460e40100e82b8c830dbf9bea65d8e9d1e1f7adc63d6845b`
- `benchmark/test_top_k_top_p_metax.py`: `68961c3dd85a7e24f4406b31a18a7410f08802bcfc95ac15e9f088dd6e99fcb2`

Evidence:
- `results/completed.json`: `781f55480b5057e107712271f364118fcdd6ccfdaa73732c029c7b7454fc7956`
- `results/install.json`: `853b0e909d1e066159d4e4a9b71e9cb4787cb66d3c1f30c022568522dd557181`
- `results/installed-hook-check.json`: `141db35f48216a9602360d511005af542e5e0b9213cea0fe404a0aa887de33bc`
- `results/source-preserved.json`: `a10369199151dfdaf4822c4629f35076fe4ff58ea1cc2500917daa893e45aca7`
- `results/runtime-mapping.json`: `357264f7b91d357ba6078951231d46876dab83ed024f33ac0d634ebd20eabe09`
- final-audit.json (canonical remote JSON serialization): `1e336ba7847a79b19afdc22d97b36bcc29c1886eafa0a1562a9d91742670bf76`
- captured audit stdout (including transport newlines): `8117dcf59f12dc3977ef90bd47ff56622ed347111d7bd8acc5f21f48c2fb70c1`
