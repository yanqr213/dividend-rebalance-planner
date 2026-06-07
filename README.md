# dividend-rebalance-planner

`dividend-rebalance-planner` 是一个真正可离线运行的 Python CLI，用于根据本地持仓、目标权重、股息计划和现金流输入，生成股息/现金流再平衡规划。它面向个人投资者、家族办公室分析、量化开发者和研究环境，强调可审计、可重复、无需联网。

免责声明：本项目仅用于投资研究、教育和流程自动化，不构成任何投资建议、税务建议或交易指令。实际交易前请结合你的券商规则、税务居民身份、滑点、佣金与法律合规要求自行判断。

## 功能概览

- 读取本地 `holdings.csv`、`targets.csv`、`dividends.csv`
- 根据现有持仓价格和目标权重生成建议买入/卖出
- 支持现金注入、月度定投、固定费用、费率费用
- 支持最小交易单位约束
- 输出权重偏离、现金缺口、月度股息预测、税后股息估算
- 生成 JSON、CSV、Markdown 三种报告
- 完全离线，不联网抓价格，不依赖外部 API

## 快速开始

### 1. 安装

```bash
python -m pip install -e .
```

### 2. 使用示例数据运行

```bash
dividend-rebalance-planner plan \
  --holdings examples/holdings.csv \
  --targets examples/targets.csv \
  --dividends examples/dividends.csv \
  --cash 1500 \
  --monthly-contribution 500 \
  --fee-rate 0.001 \
  --fee-fixed 1 \
  --output-dir outputs \
  --prefix example-plan
```

### 3. 产出文件

- `outputs/example-plan.json`
- `outputs/example-plan-trades.csv`
- `outputs/example-plan-monthly-dividends.csv`
- `outputs/example-plan.md`

## 输入格式

### `holdings.csv`

必填列：

- `ticker`: 证券代码，大小写不敏感
- `shares`: 当前持有数量
- `price`: 本地提供的当前价格

可选列：

- `min_trade_unit`: 最小交易单位，默认 `1`

示例：

```csv
ticker,shares,price,min_trade_unit
SCHD,45,78.50,1
VTI,30,255.20,1
O,80,54.10,1
```

### `targets.csv`

必填列：

- `ticker`
- `target_weight`: 目标权重，可写小数，也可不严格加总为 1，程序会自动归一化

### `dividends.csv`

必填列：

- `ticker`
- `annual_dividend_per_share`: 每股年度股息
- `payout_months`: 派息月份，支持 `3,6,9,12`、`1;4;7;10`、`1|2|3` 等格式

可选列：

- `withholding_tax_rate`: 预扣税率，范围 `0` 到 `<1`

## 命令行参数

```text
dividend-rebalance-planner plan --holdings HOLDINGS --targets TARGETS --dividends DIVIDENDS
```

常用参数：

- `--cash`: 当前可投入现金
- `--monthly-contribution`: 本月或规划期内追加定投金额
- `--fee-rate`: 比例费用，例如 `0.001`
- `--fee-fixed`: 每笔固定费用
- `--no-sells`: 禁止卖出，只给出买入建议
- `--output-dir`: 报告输出目录
- `--prefix`: 输出文件名前缀

## 报告说明

- JSON：适合被脚本、回测系统或下游自动化程序消费
- Trades CSV：适合导入表格工具或自定义订单检查流程
- Monthly Dividends CSV：适合现金流预测和收入计划
- Markdown：适合投委会 memo、个人复盘和变更审计

## 测试

```bash
python -m unittest discover -s tests -v
```

当前项目包含：

- 计算逻辑测试
- 边界条件测试
- CLI 测试
- 报告生成测试

## 设计假设

- 价格完全来自本地 `holdings.csv`
- 目标权重自动归一化
- 月度股息预测按 `annual_dividend_per_share / payout_months_count` 均分
- 税后股息按 `withholding_tax_rate` 估算
- 不处理滑点、分红再投资税务细节、汇率和多账户撮合

## 适用场景

- 每月工资到账后规划 ETF/REIT/债券基金再平衡
- 离线环境下评估“只买不卖”与“允许卖出”的差异
- 构建可测试、可脚本化的投资研究工作流
- 为更复杂的优化器提供前置资金分配结果

## English

### Overview

`dividend-rebalance-planner` is an offline Python CLI for planning portfolio rebalancing with dividend-aware cashflow forecasting. It consumes only local CSV files and produces actionable reports for investors, analysts, and quantitative developers who need reproducible workflows without relying on external market APIs.

Disclaimer: This project is provided for research, education, and operational automation only. It is not investment advice, tax advice, legal advice, or a trade recommendation.

### Features

- Read local holdings, target weights, and dividend schedule CSV files
- Generate buy and sell suggestions from current prices supplied by the user
- Include available cash, monthly contributions, variable fees, and fixed fees
- Respect minimum trade units
- Estimate weight drift, cash shortfall, and monthly gross/net dividends
- Export JSON, CSV, and Markdown reports
- Run fully offline

### Quick Start

```bash
python -m pip install -e .
python -m dividend_rebalance_planner plan \
  --holdings examples/holdings.csv \
  --targets examples/targets.csv \
  --dividends examples/dividends.csv \
  --cash 1500 \
  --monthly-contribution 500 \
  --fee-rate 0.001 \
  --fee-fixed 1 \
  --output-dir outputs \
  --prefix example-plan
```

### Input Files

- `holdings.csv`: `ticker`, `shares`, `price`, optional `min_trade_unit`
- `targets.csv`: `ticker`, `target_weight`
- `dividends.csv`: `ticker`, `annual_dividend_per_share`, `payout_months`, optional `withholding_tax_rate`

### Testing

```bash
python -m unittest discover -s tests -v
```

### Typical Users

- Individual investors planning monthly contributions
- Quant developers building offline allocation pipelines
- Analysts preparing reproducible investment committee notes

