# volume-backups

这个目录在提交版快照中只保留索引，不直接保存 `.tgz` 备份文件本体。

原因：

- `Hermes` volume 备份中可能包含运行态认证与会话文件
- 这类文件允许在本机长期保存，但不应进入 git 历史

当前本机私有备份位置：

- `D:\CODE\hermes-agent\private-local\agentbridge-volume-backups\hermes-data-20260627-214819.tgz`
- `D:\CODE\hermes-agent\private-local\agentbridge-volume-backups\hermes-data-20260628-000717.tgz`

当前已记录的校验值：

- `hermes-data-20260627-214819.tgz`
  - `sha256 = 23097028D59D41A974E489CAB3481E8A5CE7285BFBE0AA1B1470E95D4483B46A`
- `hermes-data-20260628-000717.tgz`
  - `sha256 = 53E35CD4285AD980D941DB20AA071945ACBB8F688B01F45D1A34DCE9D8F269C2`

相关快照元数据见：

- [../known-good-20260627-214819.json](D:/CODE/hermes-agent/snapshots/agentbridge-20260628/docs/known-good-20260627-214819.json)
- [../known-good-20260628-000717.json](D:/CODE/hermes-agent/snapshots/agentbridge-20260628/docs/known-good-20260628-000717.json)
