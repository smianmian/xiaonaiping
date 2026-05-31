# Backend Gate

没有 `Docs/04_BackendInfrastructure/BACKEND_DECISION.md` 的明确结论，不允许创建后端、数据库、API、管理后台、对象存储或部署脚本。

如果后端被证明第一版必须做，默认部署基线是后端部署方案，并且必须先完成：

- `Docs/04_BackendInfrastructure/BACKEND_ARCHITECTURE.md`
- `Docs/04_BackendInfrastructure/API_DESIGN.md`
- `Docs/04_BackendInfrastructure/DATABASE_SCHEMA.md`
- `Docs/04_BackendInfrastructure/AUTH_AND_ACCOUNT.md`
- `Docs/04_BackendInfrastructure/FILE_STORAGE.md`
- `Docs/04_BackendInfrastructure/SERVER_DEPLOYMENT.md`
- `Docs/04_BackendInfrastructure/SERVER_MONITORING.md`

禁止把任何生产密钥、服务器地址、运维入口或数据库密码写入文档示例、代码、日志或提示词。
