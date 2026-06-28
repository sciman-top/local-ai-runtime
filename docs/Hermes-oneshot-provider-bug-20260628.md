# Hermes `--oneshot` provider 误判缺陷记录

更新时间：`2026-06-28`

## 1. 短结论

`AgentBridge` 侧已经把默认 `--oneshot` bring-up 修通，但这次暴露出的核心缺陷属于 `Hermes upstream + 当前发布镜像漂移`：

- 当前 live 使用镜像：`nousresearch/hermes-agent@sha256:9f367c7756ef087661a361536a89f438d57a122b958dc23d82d456b1433e6e9e`
- 该镜像内 `hermes -z/--oneshot` 在 custom OpenAI-compatible provider + `HERMES_INFERENCE_MODEL=gpt-5.4` 场景下，会把 provider 自动识别成不可路由分组别名 `openai`
- 最终报错：`Unknown provider 'openai'`
- `D:\CODE\external\hermes-agent-references\hermes-agent` 当前参考源码 HEAD 已经包含避免 custom provider 误判的修复逻辑，说明 live 镜像落后于参考源码

所以当前状态是：

- `live 主链已恢复`
- `upstream 镜像版本仍带旧缺陷`

## 2. 最小复现

环境前提：

- `config.yaml` 里主 provider 是命名 custom provider，例如：
  - `model.provider: custom:primary-gateway`
  - `providers.primary-gateway.base_url: https://ai.input.im/v1`
  - `providers.primary-gateway.key_env: OPENAI_API_KEY`
- 环境变量中存在：
  - `HERMES_INFERENCE_MODEL=gpt-5.4`
  - `HERMES_INFERENCE_PROVIDER=openai-api`

最小复现命令：

```powershell
& 'C:\Users\sciman\Documents\AgentBridge\scripts\start-hermes.ps1' --oneshot 'Reply with exactly OK.'
```

旧行为：

- Hermes 输出：
  - `hermes -z: agent failed: Unknown provider 'openai'`

对照命令：

```powershell
& 'C:\Users\sciman\Documents\AgentBridge\scripts\start-hermes.ps1' chat -Q -q 'Reply with exactly OK.'
```

该路径可成功返回 `OK`。

## 3. 根因链

当前镜像内 `hermes_cli/oneshot.py::_run_agent()` 有一段逻辑：

- 先取 `env_model = os.getenv("HERMES_INFERENCE_MODEL", "").strip()`
- `effective_model = explicit_arg or env_model or config_default`
- 当 `effective_provider is None and (model or env_model)` 时，会把 `env_model` 当成“显式模型选择”
- 然后调用：
  - `detect_provider_for_model(explicit_model, current_provider)`

在当前发布镜像里，下面这个探针结果为真：

```python
from hermes_cli.models import detect_provider_for_model
print(detect_provider_for_model('gpt-5.4', 'custom:primary-gateway'))
```

输出：

```python
('openai', 'gpt-5.4')
```

这里的 `openai` 只是 provider group / vendor family，不是可路由 provider id。

后续 `resolve_runtime_provider(requested='openai', ...)` 进入 auth/provider 解析时，就会失败为：

- `Unknown provider 'openai'`

## 4. 关键证据

### A. 当前发布镜像内实测

容器内 Python 探针：

```python
from hermes_cli.models import detect_provider_for_model
print(detect_provider_for_model('gpt-5.4', 'custom:primary-gateway'))
print(detect_provider_for_model('gpt-5.4', 'openai-api'))
```

实测结果：

- `custom:primary-gateway` -> `('openai', 'gpt-5.4')`
- `openai-api` -> `None`

这正好解释了为什么：

- `--oneshot` 会炸
- `chat -Q -q` 不炸

### B. 参考源码 HEAD 已不同

在本机参考源码：

- `D:\CODE\external\hermes-agent-references\hermes-agent\hermes_cli\models.py`

当前 HEAD 中，`detect_static_provider_for_model()` 已包含：

- 对 `custom` / `custom:*` 当前 provider 的防误判保护
- blame 显示相关修复来自：
  - commit `1a435a6d5`
  - message: `fix(model-switch): prevent custom-provider misattribution in model picker (#48305)`

在参考源码工作树里直接运行同样探针：

```python
from hermes_cli.models import detect_provider_for_model
print(detect_provider_for_model('gpt-5.4', 'custom:primary-gateway'))
```

返回：

```python
None
```

这说明：

- 参考源码 HEAD 已修
- 当前 live 发布镜像仍旧

## 5. 当前 bridge 侧缓解

为了先修通主链，当前在：

- [run-hermes-wrapper.sh](C:/Users/sciman/Documents/AgentBridge/scripts/run-hermes-wrapper.sh)

加入了定向缓解：

- 仅当命令是 `--oneshot/-z`
- 且没有显式传 `--model`
- 且没有显式传 `--provider`

时：

- 清掉 `HERMES_INFERENCE_MODEL`
- 清掉 `HERMES_INFERENCE_PROVIDER`

这样 Hermes 会回退到 `config.yaml` 的持久化 provider/model，而不是把 env model 当作“显式选模”再去做错误自动识别。

这个缓解已验证能修通：

- `start-hermes.ps1 --oneshot 'Reply with exactly OK.'`
- `invoke-hermes-bringup-once.ps1 -EnvFilePath 'D:\CODE\qq-codex-bot\.env'`

## 6. 对上游的最小修复建议

更合理的上游修法有两种，推荐优先级如下：

### 方案 A：只把 CLI 显式 `--model` 当成“显式选模”

在 `hermes_cli/oneshot.py::_run_agent()` 中，把：

- `if effective_provider is None and (model or env_model):`

改成只在 `model` 明确传入时才触发 provider 自动识别。

原因：

- `HERMES_INFERENCE_MODEL` 在实际部署里常被当成“默认值投影”
- 不应等同于用户显式传了 `--model`

### 方案 B：即便走自动识别，也必须拒绝不可路由 provider group

即：

- 若 `detect_provider_for_model()` 返回的是 `openai` 这类 group/vendor alias
- 不应直接拿去喂 `resolve_runtime_provider()`

而应：

- 继续使用当前配置 provider
- 或只接受可路由 canonical provider id，例如 `openai-api` / `openai-codex`

## 7. 建议的上游回归测试

新增测试目标：

- `oneshot` 在 `config.model.provider = custom:primary-gateway`
- 且 `HERMES_INFERENCE_MODEL = gpt-5.4`
- 且未显式传 `--model/--provider`

时：

- 不应调用到 `requested='openai'`
- 应继续使用当前 custom provider

最简单断言可以是：

- mock `resolve_runtime_provider`
- 确认 `requested` 仍为 `None` 或 `custom:primary-gateway`
- 而不是 `openai`

## 8. 当前边界

当前这份记录的作用是：

- 证明问题真实存在于发布镜像
- 证明不是本地 provider key 或 `/v1` 配置错误
- 证明 bridge 侧缓解是必要且有边界的

但它不代表：

- upstream 已发布正式修复镜像

如果未来更换 Hermes 镜像，必须重新验证这一条是否仍需要保留。
