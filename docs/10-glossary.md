# 术语表

本文档统一项目内所有核心术语，确保文档、代码、接口命名一致。

## 采集与样本

| 术语 | 英文 | 定义 | 使用场景 |
| --- | --- | --- | --- |
| 采集 | Collect | 通过自动化程序从平台获取内容 | `collection_task`、`collector` |
| 录入 | Import | 人工手动补充样本内容 | `manual_import`、`POST /posts/manual-import` |
| 样本 | Post | 采集或录入的原始内容单元 | `posts` 表、样本列表页 |

## 事实与审核

| 术语 | 英文 | 定义 | 使用场景 |
| --- | --- | --- | --- |
| 事实风险 | Fact Risk | AI 识别出的潜在不实表述 | `fact_risk_level`、`fact_risk_items` |
| 事实确认 | Fact Check | 人工对事实风险进行核实并标记状态 | `fact_check_status`、`POST /analysis-results/{id}/fact-check` |
| 审核 | Review | 对生成内容的质量、合规性进行人工判定 | `review_records`、`POST /reviews` |

## 模板与生成

| 术语 | 英文 | 定义 | 使用场景 |
| --- | --- | --- | --- |
| 模板 | Template | 从高表现样本中抽象出的可复用结构 | `templates` 表 |
| 模板分类 | Template Category | 模板的颗粒度类型，如开头钩子、叙事框架 | `template_category` 枚举 |
| 生成 | Generation | 基于模板和主题产出新内容的过程 | `generation_jobs`、`generated_contents` |

## 通用状态

| 术语 | 英文 | 定义 |
| --- | --- | --- |
| 状态 | Status | 对象在当前生命周期中的阶段 |
| 启用 | Active | 模板或配置处于可用状态 |
| 归档 | Archived | 对象已不再使用但保留记录 |

## 命名约定

1. 代码中采集相关一律使用 `collect` 而非 `crawl` 或 `fetch`。
2. 人工补录样本一律使用 `import` 而非 `create` 或 `add`。
3. 事实确认流程使用 `fact_check` 而非 `fact_verify` 或 `fact_confirm`。
4. 状态字段统一命名为 `status`，类型为字符串枚举。
