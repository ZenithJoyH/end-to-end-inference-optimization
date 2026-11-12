# FGV GDN local tuning rollback

Scope: user requested mx59 qwen36-35b FGV gdn_chunk.py local diff only. Restore e1a02b6 HEAD; preserve Plugin GDN registration, MoE2267, sampler49e9 and all other source files. No inference, GPU test or service operation.

Archive scripts before execution. Exact container/image/private-file guard, no model process, original SHA CAS, original bytes/diff backup and complete source manifests. Automatic byte restoration on post-write failure.

Script SHA256: {'rollback-host-001.py': '2627099cb3fdff37abff2533289801c2691c9424613e1e79d037c93f18aa6729', 'rollback-container-001.py': '39e85df5b15a89f09ccc5cf50567a311b7769e8699c2acd79ebc459322134e64'}

## Completed

Native exit0. Restored gdn_chunk.py to HEAD e1a02b6, Git blob5a506d20b8251c0fd3b949434dd3eea3cf340ccc. Current target SHA256 f4a6bd6cf6db191439fa3bdc1e6b25d432b739c1a0700b85a2da78e427a3d75a; original SHA109a6f92 retained in the backup. Only this file changed in the complete6559-file map; all other6558 files equal before. Plugin GDN registration, MoE2267 and sampler49e9 preserved.

AST syntax passes, original function signatures unchanged; target git diff empty, mode/owner preserved. No model process at action, no service start/restart, no GPU/model requests. This is unused-path source cleanup, not a GPU numerical test or a new full-model/Graph/performance gate. Historical performance evidence remains bound to its original source snapshot; it is not silently rebound to the cleaned package.

Artifacts: /public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/gdn-cleanup-20261105-001 . Includes commands, original/restored bytes, original diff, full before/after source manifests and native receipts. result.json SHA25614fb5644046c3ce250dfeedc8d1b15106ba2de3da46f9d7df17121d631d982a4. Backup: gdn_chunk.before.py.
