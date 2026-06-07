# Contributing

## 中文

欢迎贡献改进。为了让这个项目保持可审计、可离线运行、可测试，请优先遵循以下原则：

- 保持离线优先，不引入强制联网依赖
- 对输入格式和边界条件补充测试
- 保持报告格式稳定，避免破坏下游自动化
- 对涉及资金计算的逻辑改动，附带测试与变更说明

建议流程：

1. 创建分支
2. 修改代码或文档
3. 运行 `python -m unittest discover -s tests -v`
4. 更新 `CHANGELOG.md`
5. 发起评审

## English

Contributions are welcome. To keep this project auditable, offline-first, and easy to automate, please follow these guidelines:

- Prefer offline workflows and avoid mandatory network dependencies
- Add tests for input validation and edge cases
- Keep report schemas stable for downstream tooling
- Document any behavior change that affects cash, fees, weights, or dividends

Suggested workflow:

1. Create a branch
2. Make your changes
3. Run `python -m unittest discover -s tests -v`
4. Update `CHANGELOG.md`
5. Open a review or pull request in your own hosting workflow

