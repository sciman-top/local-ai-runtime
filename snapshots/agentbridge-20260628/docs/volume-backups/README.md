# volume-backups

这个目录在提交版快照中只保留索引，不直接保存 `.tgz` 备份文件本体。

原因：

- `Hermes` volume 备份中可能包含运行态认证与会话文件
- 这类文件允许在本机长期保存，但不应进入 git 历史

当前本机私有备份位置：

- `D:\CODE\local-ai-dev-orchestrator\private-local\agentbridge-volume-backups\hermes-data-20260627-214819.tgz`
- `D:\CODE\local-ai-dev-orchestrator\private-local\agentbridge-volume-backups\hermes-data-20260628-000717.tgz`
- `C:\Users\sciman\Documents\AgentBridge\docs\volume-backups\hermes-data-20260628-124819-747.tgz`

当前已记录的校验值：

- `hermes-data-20260627-214819.tgz`
  - `bytes = 165`
  - `sha256 = 23097028D59D41A974E489CAB3481E8A5CE7285BFBE0AA1B1470E95D4483B46A`
- `hermes-data-20260628-000717.tgz`
  - `bytes = 2068369`
  - `sha256 = 53E35CD4285AD980D941DB20AA071945ACBB8F688B01F45D1A34DCE9D8F269C2`
- `hermes-data-20260628-124819-747.tgz`
  - `bytes = 11574721`
  - `sha256 = 7E3A3D0F2356A4FDF04F2A7B3864F024A0EB25887F63E8484D42BC0B05778090`
- `hermes-data-20260628-131518-032.tgz`
  - `bytes = 11616648`
  - `sha256 = F5DA4F285AA6193AFBB526A6C8E3AC52F3314682D49F85D35A3B30B3E561849E`
- `hermes-data-20260628-225738-431.tgz`
  - `bytes = 12996274`
  - `sha256 = 4AC3AD7EF7AA608902BB91ADBF3BB18CA2E0C39E35D2F65DD55195E064C115EC`

相关快照元数据见：

- [../known-good-20260627-214819.json](D:/CODE/local-ai-dev-orchestrator/snapshots/agentbridge-20260628/docs/known-good-20260627-214819.json)
- [../known-good-20260628-000717.json](D:/CODE/local-ai-dev-orchestrator/snapshots/agentbridge-20260628/docs/known-good-20260628-000717.json)
- [../known-good-20260628-124819-747.json](D:/CODE/local-ai-dev-orchestrator/snapshots/agentbridge-20260628/docs/known-good-20260628-124819-747.json)
- [../known-good-20260628-131518-032.json](D:/CODE/local-ai-dev-orchestrator/snapshots/agentbridge-20260628/docs/known-good-20260628-131518-032.json)
- [../known-good-20260628-225738-431.json](D:/CODE/local-ai-dev-orchestrator/snapshots/agentbridge-20260628/docs/known-good-20260628-225738-431.json)
