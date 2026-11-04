# cleanup-001: obsolete examples and test consolidation

User authorized current mx-103/deepseekV4-flash Plugin cleanup on 2026-10-27, prioritizing examples/tests. This is auxiliary deployment/test cleanup with no production, launch or performance change. Active private editable source is /opt/vllm-plugin-fl, HEAD a696859b9, branch upgrade/20261020-main; not shared through bind mounts. Three repository revisions/status and the exact service PID/start ticks/arguments will be saved in before/snapshot.json.

The 11 files under examples/deepseek_v4_metax implement the obsolete serve.py/bootstrap path, duplicate policy/tuning JSON, cache environment setup, old dependency locks and Docker build instructions. No production code references this directory. The external start-model.sh uses installed package initialization and package resources. Archive and verify this directory before removing it from the Plugin diff. Keep all production JSON resources and pyproject package-data.

Two tests total 652 lines (273+379); most cover the old launcher/pins/cache or source structure. Retain five existing behavioral checks in test_deepseek_v4_layer_boundaries.py: local launch metadata isolation, tuner isolation, invalid wrapper rejection, non-MetaX native indexer fallback/MetaX FP4 guard, and idempotent/typed/immutable framework policy. Change the last test to read the actual installed package JSON. The retained file has 136 lines. Mock checks do not prove other-platform hardware execution.

Before mutation, archive all original examples/tests and preserve the entire current patch, index and runtime identity. Remove only the twelve deleted intent-to-add entries, after proving no HEAD/staged content exists; preserve all other index entries. commands/rollback.py restores archived files and original intent-to-add state, guarded against later edits.

Validation: five retained CPU tests; build wheel in a private disposable source copy without reinstalling or changing live _version.py; verify all production Python bytes and four JSON resources in the wheel. Verify every live vllm_fl file, pyproject/setup and external start-model.sh unchanged, plus exact same API process/args/start ticks and health. Do not restart services or send model requests. No new accuracy/performance claim; existing runtime-bound scores retain their original scope. pr_readiness remains experimental.

Remote artifact root: `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-01`. Complete backups/patches/logs stay remote.

Pre-execution command SHA registration:
- commands/apply.py `4c0fc9cbe9eeb4eb64965b647e406ceec21cc293c7c744b160e3ada27d0938ce`
- commands/rollback.py `b0a80c69e73cf1b44a1aa2897877e93aad3f7957fd32ee09a2da187c646ee8b8`
- commands/test_deepseek_v4_layer_boundaries.py `a7fecbe551d9bd265af35f4263074947d9d764ec79bb39fe3f9b64ebb3d8dd75`
- commands/validate.py `612adad12dc48c97f591343f4c46b7fbfc004a6674db29dd88343e6a5fd8d708`
- Local stage.py SHA `7d66d801cc2769b01c6f72ae9be98e6771d71d7a14447781a81a4752467f2e80` (creates new case directory, saves verified commands before apply/validate).

## Result

Completed 2026-10-27 15:59:50 Asia/Shanghai. All validation passed.

- Full changed-file inventory, including five untracked production config/resource files: **48 -> 36**. Tracked diff only: 43 -> 31 files, final 8167 insertions / 8 deletions. Counts refer to the existing main HEAD, not a new PR #427 baseline.
- Eleven obsolete example files and the obsolete packaging test removed; five behavior tests retained in one 136-line file, down from two files / 652 lines. No remaining new examples or stale deleted intent-to-add entries.
- All five CPU regressions passed. Private-copy wheel built without reinstalling the active package. All 315 non-generated production Python files and four MetaX JSON resources match the active source bytes. `_version.py` is generated only in the disposable build copy; every file in the live runtime package, including its current version file, remains byte-identical.
- pyproject.toml/setup.py and the user's external start-model.sh unchanged. Existing editable import remains `/opt/vllm-plugin-fl/vllm_fl/__init__.py`. Exact same service PID/start time/arguments, health200; no service restart or model requests. No new accuracy or performance claim. Other-platform hardware and full repository CI not run; the retained non-MetaX test is a CPU routing mock.

Result: `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-01/result.json`, SHA `a6b3f0455e9d7a825e56e394f0d6c544e279d4e550c380a0f7c75253cd196dd5`.
Verified archive: `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-01/before/examples-tests.tar.gz`, SHA `632286babba739bf3e7835b4c67713e1bf4a0cf0c2c6368f331f467885238093`. Entire original patch/index and repository/runtime snapshot remain under before/.
Wheel SHA `ef588481b41dfa44fa74a21185c0383e7effdada07f91485b9214041f5494e5e`; build copy `/opt/dsv4-plugin-cleanup-build-20261027-01`, no actual install mutation.

Rollback from mx-103 host, only when no later edits to the touched paths need preserving:

```sh
docker exec -i deepseekV4-flash /opt/conda/bin/python - < /public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-01/commands/rollback.py
```

No commits, pushes or PR creation. pr_readiness remains experimental because this cleanup does not establish upstream or cross-platform acceptance.
