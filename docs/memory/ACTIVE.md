# 当前项目记忆

- 项目：SRE Agent（Python 包位于 `src/sre_agent`）。
- 依赖与开发命令以根目录 `pyproject.toml`、`README.md` 和 `docs/DEVELOPMENT_GUIDE.md` 为准。
- `.env`、虚拟环境、依赖缓存、日志、运行数据和构建缓存不进入版本库。
- 运行环境配置通过 `../../.env` 提供模板；真实凭据只保存在本地或受控密钥系统。
- 修改核心业务代码前先阅读 `docs/PRD.md` 与 `docs/task/implementation.md`，保持状态模型、证据模型和工作流阶段定义一致。

## 记忆同步规则

只同步经过脱敏、对本项目有长期复用价值的结论。全局记忆中的本地路径、账号密码、访问令牌和其他敏感笔记不上传。
