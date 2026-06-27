# private-local

这个目录用于保存只适合本机私存、不应进入 git 的运行态数据。

当前典型内容：

- Hermes volume 备份
- 任何可能包含运行态认证信息、会话状态或供应商密钥的数据

为什么不提交：

- `Hermes` volume 备份中可能包含 `auth.json` 等运行态文件
- 这类文件不适合进入长期公开提交历史

所以当前策略是：

- 可以保存在 `D:\CODE\hermes-agent\private-local\...`
- 但默认由 `.gitignore` 排除
