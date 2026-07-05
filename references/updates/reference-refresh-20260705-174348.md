# 参考仓刷新摘要

生成时间（UTC）：`2026-07-05T17:44:01Z`
模式：`pull --ff-only`
根目录：`D:\CODE\external\local-ai-dev-orchestrator-references`
manifest：`D:\CODE\local-ai-dev-orchestrator\references\reference-shelf.manifest.json`
集合：`manifest-default`
仓列表：`codex, plugins, modelcontextprotocol, servers`

## codex

- 路径：`D:\CODE\external\local-ai-dev-orchestrator-references\codex`
- 分支：`main`
- 状态：`updated`
- 更新前：`328e95110c`
- 更新后：`be33f80bc6`
- ahead/behind：`0	0`
- 说明：pull --ff-only completed
- 本次更新 commit：
  - `be33f80bc6 (HEAD -> main, origin/main, origin/HEAD) [codex] Read buffering metadata from response events (#31064)`
  - `98d28aab54 chore: remove unused git-cliff configuration (#31066)`
  - `d206a5d68f [codex] expose remote plugin versions (#30981)`
  - `319d03056e fix(install): reuse GitHub release metadata (#31056)`
  - `1f17e7512f Fix MIME types for path-backed feedback attachments (#30796)`
  - `da4c8ca57d [codex] Add configurable multi-agent mode hint text (#30493)`
  - `beca198b8a telemetry: log structured direct tool-call timing (#30334)`
  - `b35d4b6b9d fix(websockets) ignore metadata for incremental requests (#30770)`
  - `0ccb676dd0 fix: address quick-xml security advisories (#30941)`
  - `cbdd7f0047 Fix inherited availability metadata for Bedrock models (#30897)`
  - `6ff670bd03 [codex] emit per-request TTFT completion telemetry (#30883)`
  - `129ea2aaf5 (origin/iceweasel/windows-sandbox-helper-rename-29771) Log multi-agent communication lifecycle (#30872)`
  - `a98a21798c Consolidate multi-agent v2 communication sends (#30867)`
  - `042e61726d [codex] bound Rendezvous WebSocket liveness (#30643)`
  - `d059658ad1 docs: add tag to fenced code block (#30851)`
  - `db887d03e1 fix(core) Remove full text websocket trace (#30757)`
  - `020828170f [codex] Update safety notice wording (#30645)`
  - `cfead68e5d [codex] disable Nagle on Rendezvous WebSockets (#30269)`
  - `4808c162ee [codex] auto-label AWS Bedrock issues (#30607)`
  - `9d13291955 Update safety check links (#30491)`
  - `80f54d1266 [codex] Treat max as a first-class reasoning effort (#30467)`
  - `ccdfb4f342 Revert "Make auto-review on-request prompt more proactive" (#30508)`
  - `8dac605901 [codex] Restore v1 delegation guidance (#30511)`
  - `6b5f5743b3 [codex] Use model metadata for skills usage instructions (#29740)`
  - `850da19dc4 fix(tui): clear completed safety buffering prompt (#30490)`
  - `e428a12d22 [codex] Enable remote plugins by default (#30297)`
  - `bdd282f3bb [app-server] increase currentTime/read timeout (#30384)`
  - `9dbdb4e2c0 [plugins] Enforce marketplace source policy at runtime (#29691)`
  - `e2398d0b16 [app-server] expose environment info RPC (#30291)`
  - `d2885dc3cd core: stabilize synthesized call output IDs (#30327)`

## plugins

- 路径：`D:\CODE\external\local-ai-dev-orchestrator-references\plugins`
- 分支：`main`
- 状态：`pull`
- 更新前：`d6169bef12`
- 更新后：`d6169bef12`
- ahead/behind：`0	0`
- 说明：pull --ff-only completed

## modelcontextprotocol

- 路径：`D:\CODE\external\local-ai-dev-orchestrator-references\modelcontextprotocol`
- 分支：`main`
- 状态：`updated`
- 更新前：`ead35b59b4`
- 更新后：`60dc69e9a9`
- ahead/behind：`0	0`
- 说明：pull --ff-only completed
- 本次更新 commit：
  - `60dc69e9 (HEAD -> main, origin/main, origin/HEAD) Correct several claims in the SDK betas blog post (#2997)`
  - `936408a9 Add blog post announcing SDK betas for 2026-07-28 (#2988)`
  - `c87328cc Merge pull request #2972 from modelcontextprotocol/paulc/mcp-param-ttl-decouple`
  - `93671a3f build(deps-dev): bump prettier from 3.8.4 to 3.9.3 (#2987)`
  - `fdab8f53 build(deps-dev): bump eslint from 10.5.0 to 10.6.0 (#2986)`
  - `c0f97c9a build(deps-dev): bump typescript-eslint from 8.61.1 to 8.62.0 (#2985)`
  - `368e013c fix the ordering of the dprecated features table`
  - `dd42ebd0 Merge pull request #2937 from DaleSeo/fix/sep-2243-base64-case-sensitivity`
  - `66ad797f Update docs/seps/2243-http-standardization.mdx`
  - `88aaf16f Update seps/2243-http-standardization.md`
  - `8276fb6b Apply suggestions from code review`
  - `d43894d2 Merge branch 'main' into paulc/mcp-param-ttl-decouple`
  - `26dd54c0 spec: decouple Mcp-Param-* header emission from schema TTL`
  - `d7b917e4 docs: fix SEP-2243 base64 sentinel case-sensitivity contradiction`

## servers

- 路径：`D:\CODE\external\local-ai-dev-orchestrator-references\servers`
- 分支：`main`
- 状态：`updated`
- 更新前：`7b1170d1da`
- 更新后：`7097923966`
- ahead/behind：`0	0`
- 说明：pull --ff-only completed
- 本次更新 commit：
  - `7097923 (HEAD -> main, origin/main, origin/HEAD) ci(release): switch npm publishing to OIDC trusted publishing (#4466)`
  - `5850690 ci: don't cancel in-progress CI runs on main`
  - `3b9d38f ci: run CI on pushes to any branch, cancel superseded runs`
  - `7529857 ci(release): remove the daily release cron; dispatch-only`
  - `18f09ad docs(releasing): note per-registry guard placement precisely`
  - `06a8169 ci: remove dead release-triggered publish jobs; make RELEASING.md claims true`
  - `a714b63 docs(releasing): describe the process as it stands after this PR`
  - `f2450d7 docs(releasing): describe the go-forward release process`
  - `9e9dfb9 docs(releasing): clarify CalVer is current state, semver for TS is planned`
  - `1c0fdc3 docs: add RELEASING.md documenting OIDC publishing and retry process`
  - `f4c86ff fix(release): count .md changes in package matrix; use --frozen for pytest`
  - `dab3489 ci(release): run tests before publishing`
  - `4307b95 ci(release): enable provenance and pin npm version for OIDC publish`
  - `1a4ecb7 ci(release): switch npm publishing to OIDC trusted publishing`
  - `b2a94a2 fix(deps): bump python-multipart, cryptography, pyjwt to clear HIGH alerts (#4398)`
