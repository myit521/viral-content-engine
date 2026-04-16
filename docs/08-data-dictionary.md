# 数据字典

## 1. 文档目标

本文档定义第一阶段 MVP 的核心数据对象、字段约束、状态枚举和读写边界。

适用范围：

1. 知乎单平台采集
2. AI 分析与人工事实确认
3. 模板沉淀
4. 内容生成、审核、版本留存、发布回填

## 2. 字段设计原则

1. 核心检索字段必须结构化，不放进 JSON。
2. 原始平台响应和不稳定扩展字段优先放 `raw_json`。
3. 会用于筛选、排序、统计、联表的字段必须拆出独立列。
4. 每张核心表都要标明“系统写入 / 人工可改 / 只读展示”。
5. 第一阶段删除语义优先映射为状态归档，不默认设计物理删除流程。

## 3. 主表清单

第一阶段核心表：

1. `platform_sources`
2. `collection_tasks`
3. `authors`
4. `posts`
5. `analysis_results`
6. `templates`
7. `generation_jobs`
8. `generated_contents`
9. `generated_content_versions`
10. `review_records`
11. `publish_records`
12. `performance_snapshots`

辅助表或扩展表：

1. `post_segments`
2. `template_examples`
3. `extracted_features`
4. `prompt_specs`

## 4. 表级数据字典

### 4.1 `platform_sources`

| 字段 | 类型 | 长度 | 必填 | 默认值 | 说明 | 写入方 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | bigint | - | 是 | 自增 | 主键 | 系统 | 自增 |
| `code` | varchar | 32 | 是 | - | 平台编码 | 系统 | 第一阶段固定 `zhihu` |
| `name` | varchar | 64 | 是 | - | 平台名称 | 系统 | 如 `知乎` |
| `enabled` | boolean | - | 是 | `true` | 是否启用 | 系统 | 控制开关 |
| `mvp_enabled` | boolean | - | 是 | `true` | 是否在 MVP 中启用 | 系统 | 第一阶段仅知乎为 `true` |
| `created_at` | datetime | - | 是 | 当前时间 | 创建时间 | 系统 | 只读 |

### 4.2 `collection_tasks`

| 字段 | 类型 | 长度 | 必填 | 默认值 | 说明 | 写入方 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | varchar | 64 | 是 | - | 任务 ID | 系统 | 如 `ct_001` |
| `platform_id` | bigint | - | 是 | - | 平台 ID | 系统 | FK |
| `task_type` | varchar | 32 | 是 | - | 任务类型 | 系统 | `historical_hot` / `keyword_search` |
| `query_keyword` | varchar | 255 | 否 | `null` | 检索关键词 | 人工输入 | 可为空 |
| `date_range_start` | date | - | 否 | `null` | 起始日期 | 人工输入 |  |
| `date_range_end` | date | - | 否 | `null` | 结束日期 | 人工输入 |  |
| `trigger_mode` | varchar | 32 | 是 | `manual` | 触发方式 | 系统 | `manual` / `scheduled` |
| `status` | varchar | 32 | 是 | `pending` | 状态 | 系统 | 见全局状态枚举 |
| `success_count` | int | - | 否 | `0` | 成功条数 | 系统 |  |
| `failed_count` | int | - | 否 | `0` | 失败条数 | 系统 |  |
| `error_message` | text | - | 否 | `null` | 错误摘要 | 系统 | 失败时填充 |
| `raw_output_path` | varchar | 255 | 否 | `null` | 原始文件目录 | 系统 | 如 `data/raw/...` |
| `started_at` | datetime | - | 否 | `null` | 开始时间 | 系统 |  |
| `finished_at` | datetime | - | 否 | `null` | 结束时间 | 系统 |  |
| `created_at` | datetime | - | 是 | 当前时间 | 创建时间 | 系统 |  |
| `updated_at` | datetime | - | 是 | 当前时间 | 更新时间 | 系统 |  |

### 4.3 `authors`

| 字段 | 类型 | 长度 | 必填 | 默认值 | 说明 | 写入方 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | bigint | - | 是 | 自增 | 主键 | 系统 | 自增 |
| `platform_id` | bigint | - | 是 | - | 平台 ID | 系统 | FK |
| `platform_author_id` | varchar | 128 | 是 | - | 平台作者 ID | 系统 | 幂等键之一 |
| `name` | varchar | 255 | 是 | - | 作者名 | 系统 |  |
| `profile_url` | varchar | 500 | 否 | `null` | 作者主页 | 系统 |  |
| `follower_count` | int | - | 否 | `null` | 关注量 | 系统 | 可为空 |
| `bio` | text | - | 否 | `null` | 简介 | 系统 |  |
| `raw_json` | json | - | 否 | `null` | 原始作者数据 | 系统 | 非稳定字段 |
| `created_at` | datetime | - | 是 | 当前时间 | 创建时间 | 系统 |  |
| `updated_at` | datetime | - | 是 | 当前时间 | 更新时间 | 系统 |  |

### 4.4 `posts`

| 字段 | 类型 | 长度 | 必填 | 默认值 | 说明 | 写入方 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | varchar | 64 | 是 | - | 样本 ID | 系统 | 如 `post_001` |
| `platform_id` | bigint | - | 是 | - | 平台 ID | 系统 | FK |
| `author_id` | bigint | - | 否 | `null` | 作者 ID | 系统 | FK |
| `platform_post_id` | varchar | 128 | 否 | `null` | 平台内容 ID | 系统 | 手动录入可为空 |
| `source_type` | varchar | 32 | 是 | `collector` | 来源类型 | 系统 | `collector` / `manual_import` |
| `post_type` | varchar | 32 | 是 | `answer` | 内容类型 | 系统 | `answer` / `article` / `post` |
| `url` | varchar | 500 | 否 | `null` | 原始链接 | 人工或系统 | 手动录入也可填 |
| `title` | varchar | 500 | 否 | `null` | 标题 | 人工或系统 |  |
| `summary` | text | - | 否 | `null` | 摘要 | 系统 |  |
| `content_text` | longtext | - | 是 | - | 正文纯文本 | 人工或系统 | 核心检索字段 |
| `content_markdown` | longtext | - | 否 | `null` | Markdown 正文 | 系统 | 可为空 |
| `language` | varchar | 16 | 否 | `zh-CN` | 语言 | 系统 |  |
| `topic_keywords` | json | - | 否 | `[]` | 主题关键词数组 | 人工可改 | 推荐字符串数组 |
| `published_at` | datetime | - | 否 | `null` | 发布时间 | 人工或系统 |  |
| `like_count` | int | - | 否 | `0` | 点赞数 | 系统 |  |
| `comment_count` | int | - | 否 | `0` | 评论数 | 系统 |  |
| `favorite_count` | int | - | 否 | `0` | 收藏数 | 系统 |  |
| `share_count` | int | - | 否 | `0` | 分享数 | 系统 |  |
| `view_count` | int | - | 否 | `0` | 播放或阅读量 | 系统 |  |
| `engagement_score` | decimal(10,4) | - | 否 | `0` | 综合互动分 | 系统 | 计算字段 |
| `is_hot` | boolean | - | 是 | `false` | 是否热门 | 系统 |  |
| `is_historical_hot` | boolean | - | 是 | `false` | 是否历史高赞 | 人工可改 |  |
| `status` | varchar | 32 | 是 | `raw` | 状态 | 系统 | 见全局状态枚举 |
| `note` | text | - | 否 | `null` | 备注 | 人工可改 | 手动录入时常用 |
| `raw_json` | json | - | 否 | `null` | 平台原始数据 | 系统 | 手动录入可为空 |
| `created_at` | datetime | - | 是 | 当前时间 | 创建时间 | 系统 |  |
| `updated_at` | datetime | - | 是 | 当前时间 | 更新时间 | 系统 |  |

### 4.5 `analysis_results`

| 字段 | 类型 | 长度 | 必填 | 默认值 | 说明 | 写入方 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | varchar | 64 | 是 | - | 分析 ID | 系统 |  |
| `post_id` | varchar | 64 | 是 | - | 样本 ID | 系统 | FK |
| `analysis_version` | varchar | 32 | 是 | `v1` | 分析规则版本 | 系统 | 如 `v1` |
| `model_name` | varchar | 128 | 是 | - | 模型名 | 系统 |  |
| `prompt_version` | varchar | 128 | 是 | - | Prompt 版本 | 系统 | 版本化字段 |
| `summary` | text | - | 否 | `null` | 摘要 | 系统 |  |
| `main_topic` | varchar | 255 | 否 | `null` | 主主题 | 系统 |  |
| `content_angle` | varchar | 255 | 否 | `null` | 内容角度 | 系统 |  |
| `hook_text` | text | - | 否 | `null` | 开头钩子 | 系统 |  |
| `narrative_structure` | json | - | 否 | `null` | 叙事结构 | 系统 | 建议 JSON |
| `emotional_driver` | varchar | 128 | 否 | `null` | 情绪驱动 | 系统 |  |
| `video_adaptability_score` | decimal(5,2) | - | 否 | `null` | 视频化评分 | 系统 |  |
| `fact_risk_level` | varchar | 32 | 否 | `medium` | 事实风险等级 | 系统 | `low` / `medium` / `high` |
| `fact_risk_items` | json | - | 否 | `[]` | 风险点数组 | 系统 | AI 提取 |
| `fact_check_status` | varchar | 32 | 是 | `pending` | 人工事实确认状态 | 人工可改 |  |
| `fact_check_reviewer` | varchar | 64 | 否 | `null` | 确认人 | 人工 |  |
| `fact_check_notes` | text | - | 否 | `null` | 事实确认说明 | 人工 |  |
| `reasoning_json` | json | - | 否 | `null` | 原始结构化输出 | 系统 |  |
| `created_at` | datetime | - | 是 | 当前时间 | 创建时间 | 系统 |  |

### 4.6 `templates`

| 字段 | 类型 | 长度 | 必填 | 默认值 | 说明 | 写入方 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | varchar | 64 | 是 | - | 模板 ID | 系统 |  |
| `template_type` | varchar | 32 | 是 | `script` | 模板类型 | 系统 | `title` / `script` / `storyboard` / `caption` |
| `template_category` | varchar | 32 | 是 | `narrative_frame` | 模板分类 | 人工或系统 | 见全局状态枚举 |
| `name` | varchar | 255 | 是 | - | 模板名称 | 人工或系统 |  |
| `applicable_platform` | varchar | 64 | 是 | `zhihu_to_video` | 适用平台场景 | 人工或系统 |  |
| `applicable_topic` | varchar | 64 | 是 | `history` | 适用主题 | 人工或系统 |  |
| `applicable_scene` | varchar | 128 | 否 | `null` | 适用场景 | 人工或系统 | 如 `人物争议` |
| `structure_json` | json | - | 是 | - | 模板结构 | 人工或系统 | 核心字段 |
| `prompt_template` | text | - | 否 | `null` | 关联提示词模板 | 人工或系统 | 可选 |
| `quality_score` | decimal(5,2) | - | 否 | `null` | 质量评分 | 系统 |  |
| `source_post_count` | int | - | 否 | `0` | 来源样本数 | 系统 |  |
| `status` | varchar | 32 | 是 | `draft` | 状态 | 人工可改 |  |
| `version` | varchar | 32 | 是 | `v1` | 模板版本 | 系统 | 如 `v1` |
| `created_at` | datetime | - | 是 | 当前时间 | 创建时间 | 系统 |  |
| `updated_at` | datetime | - | 是 | 当前时间 | 更新时间 | 系统 |  |

### 4.7 `generation_jobs`

| 字段 | 类型 | 长度 | 必填 | 默认值 | 说明 | 写入方 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | varchar | 64 | 是 | - | 生成任务 ID | 系统 |  |
| `job_type` | varchar | 32 | 是 | `script_generation` | 任务类型 | 系统 |  |
| `input_topic` | varchar | 255 | 是 | - | 输入主题 | 人工输入 |  |
| `input_brief` | text | - | 否 | `null` | 输入说明 | 人工输入 |  |
| `input_sources_json` | json | - | 否 | `[]` | 指定来源样本 | 人工输入 |  |
| `selected_template_id` | varchar | 64 | 否 | `null` | 选用模板 | 人工输入 | FK |
| `prompt_version` | varchar | 128 | 是 | - | Prompt 版本 | 系统 |  |
| `model_name` | varchar | 128 | 是 | - | 模型名 | 系统 |  |
| `status` | varchar | 32 | 是 | `pending` | 状态 | 系统 |  |
| `error_message` | text | - | 否 | `null` | 错误摘要 | 系统 |  |
| `created_at` | datetime | - | 是 | 当前时间 | 创建时间 | 系统 |  |
| `updated_at` | datetime | - | 是 | 当前时间 | 更新时间 | 系统 |  |

### 4.8 `generated_contents`

| 字段 | 类型 | 长度 | 必填 | 默认值 | 说明 | 写入方 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | varchar | 64 | 是 | - | 结果 ID | 系统 |  |
| `job_id` | varchar | 64 | 是 | - | 生成任务 ID | 系统 | FK |
| `template_id` | varchar | 64 | 否 | `null` | 模板 ID | 系统 | FK |
| `title` | varchar | 500 | 否 | `null` | 当前标题 | 人工或系统 | 当前生效版本字段 |
| `script_text` | longtext | - | 是 | - | 当前脚本文本 | 人工或系统 | 当前生效版本字段 |
| `storyboard_json` | json | - | 否 | `null` | 当前分镜 | 人工或系统 |  |
| `cover_text` | varchar | 255 | 否 | `null` | 当前封面文案 | 人工或系统 |  |
| `publish_caption` | text | - | 否 | `null` | 当前发布文案 | 人工或系统 |  |
| `hashtags` | json | - | 否 | `[]` | 标签数组 | 人工或系统 |  |
| `fact_check_status` | varchar | 32 | 是 | `pending` | 人工事实确认状态 | 人工可改 | 发布前必须为 `confirmed` |
| `fact_check_notes` | text | - | 否 | `null` | 事实确认说明 | 人工可改 |  |
| `source_trace_json` | json | - | 是 | - | 来源追踪 | 系统 | 模板和样本映射 |
| `current_version_no` | int | - | 是 | `1` | 当前版本号 | 系统 |  |
| `status` | varchar | 32 | 是 | `draft` | 状态 | 人工或系统 |  |
| `created_at` | datetime | - | 是 | 当前时间 | 创建时间 | 系统 |  |
| `updated_at` | datetime | - | 是 | 当前时间 | 更新时间 | 系统 |  |

### 4.9 `generated_content_versions`

| 字段 | 类型 | 长度 | 必填 | 默认值 | 说明 | 写入方 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | varchar | 64 | 是 | - | 版本 ID | 系统 |  |
| `generated_content_id` | varchar | 64 | 是 | - | 结果 ID | 系统 | FK |
| `version_no` | int | - | 是 | - | 版本号 | 系统 | 从 1 递增 |
| `title` | varchar | 500 | 否 | `null` | 该版本标题 | 人工或系统 |  |
| `script_text` | longtext | - | 是 | - | 该版本脚本 | 人工或系统 |  |
| `storyboard_json` | json | - | 否 | `null` | 该版本分镜 | 人工或系统 |  |
| `cover_text` | varchar | 255 | 否 | `null` | 该版本封面文案 | 人工或系统 |  |
| `publish_caption` | text | - | 否 | `null` | 该版本发布文案 | 人工或系统 |  |
| `edit_note` | text | - | 否 | `null` | 编辑说明 | 人工 |  |
| `editor` | varchar | 64 | 否 | `system` | 编辑人 | 人工或系统 | 初稿可为 `system` |
| `created_at` | datetime | - | 是 | 当前时间 | 创建时间 | 系统 |  |

### 4.10 `review_records`

| 字段 | 类型 | 长度 | 必填 | 默认值 | 说明 | 写入方 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | varchar | 64 | 是 | - | 审核记录 ID | 系统 |  |
| `generated_content_id` | varchar | 64 | 是 | - | 结果 ID | 系统 | FK |
| `reviewer` | varchar | 64 | 是 | - | 审核人 | 人工 |  |
| `decision` | varchar | 32 | 是 | - | 审核决定 | 人工 | `approve` / `reject` / `edit_required` |
| `comment` | text | - | 否 | `null` | 审核意见 | 人工 |  |
| `fact_check_status` | varchar | 32 | 否 | `null` | 人工事实确认状态 | 人工 |  |
| `selected_version_no` | int | - | 否 | `null` | 审核对应版本 | 人工 |  |
| `reviewed_at` | datetime | - | 是 | 当前时间 | 审核时间 | 系统 |  |

### 4.11 `publish_records`

| 字段 | 类型 | 长度 | 必填 | 默认值 | 说明 | 写入方 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | varchar | 64 | 是 | - | 发布记录 ID | 系统 |  |
| `generated_content_id` | varchar | 64 | 是 | - | 结果 ID | 系统 | FK |
| `platform_code` | varchar | 32 | 是 | - | 发布平台 | 人工输入 | 第一阶段允许回填其他平台 |
| `publish_channel` | varchar | 32 | 是 | `manual` | 发布方式 | 人工输入 |  |
| `published_url` | varchar | 500 | 否 | `null` | 已发布链接 | 人工输入 |  |
| `published_at` | datetime | - | 否 | `null` | 发布时间 | 人工输入 |  |
| `operator` | varchar | 64 | 是 | - | 操作人 | 人工输入 |  |
| `status` | varchar | 32 | 是 | `draft` | 状态 | 人工输入 | `draft` / `published` / `archived` |
| `notes` | text | - | 否 | `null` | 备注 | 人工输入 |  |
| `created_at` | datetime | - | 是 | 当前时间 | 创建时间 | 系统 |  |
| `updated_at` | datetime | - | 是 | 当前时间 | 更新时间 | 系统 |  |

### 4.12 `performance_snapshots`

| 字段 | 类型 | 长度 | 必填 | 默认值 | 说明 | 写入方 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | varchar | 64 | 是 | - | 快照 ID | 系统 |  |
| `publish_record_id` | varchar | 64 | 是 | - | 发布记录 ID | 系统 | FK |
| `like_count` | int | - | 否 | `0` | 点赞数 | 人工输入 |  |
| `comment_count` | int | - | 否 | `0` | 评论数 | 人工输入 |  |
| `favorite_count` | int | - | 否 | `0` | 收藏数 | 人工输入 |  |
| `share_count` | int | - | 否 | `0` | 分享数 | 人工输入 |  |
| `view_count` | int | - | 否 | `0` | 播放量 | 人工输入 |  |
| `retention_rate` | decimal(5,4) | - | 否 | `null` | 完播或留存率 | 人工输入 | 0 到 1 |
| `captured_at` | datetime | - | 是 | - | 采集时间 | 人工输入 |  |
| `created_at` | datetime | - | 是 | 当前时间 | 创建时间 | 系统 |  |

## 5. Prompt 版本规则

### 5.1 命名规范

统一格式：

`<biz>.<scenario>.v<major>`

示例：

1. `analysis.zhihu.history.v1`
2. `template.history.narrative.v1`
3. `generation.zhihu_to_video.v1`

### 5.2 变更规则

1. 仅修改措辞但不改变输出结构，可沿用同一主版本。
2. 修改输出 JSON 结构，必须升级主版本。
3. 接口文档和 JSON Schema 依赖的 Prompt 版本必须同步记录。

## 6. JSON 字段约定

适合使用 JSON 的字段：

1. `posts.topic_keywords`
2. `analysis_results.narrative_structure`
3. `analysis_results.fact_risk_items`
4. `templates.structure_json`
5. `generated_contents.source_trace_json`

不建议放入 JSON 的字段：

1. 状态字段
2. 平台字段
3. 时间字段
4. 会参与筛选和排序的标签字段
5. 人工审核与事实确认状态

## 7. 状态与枚举字典

### 7.1 `template_category`

1. `title_hook`
2. `opening_hook`
3. `narrative_frame`
4. `ending_cta`
5. `full_script`

### 7.2 `source_type`

1. `collector`
2. `manual_import`

### 7.3 `fact_check_status`

1. `pending`
2. `confirmed`
3. `needs_evidence`
4. `rejected`

## 8. 全局状态枚举汇总

所有状态字段的合法取值集中定义于此，各表引用时不再重复解释。

### 8.1 采集任务状态 (`collection_task.status`)

| 值 | 含义 | 流转说明 |
| --- | --- | --- |
| `pending` | 待执行 | 任务已创建，等待触发 |
| `running` | 执行中 | 采集器正在工作 |
| `succeeded` | 完全成功 | 所有目标内容采集完成 |
| `partial_failed` | 部分失败 | 部分内容采集成功，部分失败 |
| `failed` | 完全失败 | 任务无法执行或全部失败 |
| `cancelled` | 已取消 | 人工终止 |

### 8.2 样本状态 (`post.status`)

| 值 | 含义 | 流转说明 |
| --- | --- | --- |
| `raw` | 原始入库 | 刚采集或录入，未清洗 |
| `normalized` | 已规范化 | 完成清洗、去重、分段 |
| `analyzed` | 已分析 | 完成 AI 结构化分析 |
| `templated` | 已关联模板 | 被至少一个模板引用为示例 |
| `archived` | 已归档 | 不再参与后续处理 |

### 8.3 模板状态 (`template.status`)

| 值 | 含义 |
| --- | --- |
| `draft` | 草稿，仅创建者可见 |
| `active` | 启用，可被生成任务使用 |
| `disabled` | 停用，暂时不可用 |
| `archived` | 归档，仅保留历史记录 |

### 8.4 生成任务状态 (`generation_job.status`)

| 值 | 含义 |
| --- | --- |
| `pending` | 待处理 |
| `retrieving` | 检索模板与样本中 |
| `generating` | AI 生成中 |
| `reviewing` | 等待人工审核 |
| `completed` | 已完成 |
| `failed` | 失败 |

### 8.5 生成内容状态 (`generated_content.status`)

| 值 | 含义 | 约束 |
| --- | --- | --- |
| `draft` | 草稿 | 可编辑 |
| `in_review` | 审核中 | 锁定编辑 |
| `approved` | 审核通过 | 可进入发布 |
| `rejected` | 审核驳回 | 需修改后重新提交 |
| `published` | 已发布 | 终态 |

### 8.6 事实确认状态 (`fact_check_status`)

适用于 `analysis_results` 和 `generated_contents`。

| 值 | 含义 | 适用场景 |
| --- | --- | --- |
| `pending` | 待确认 | AI 分析后初始状态 |
| `confirmed` | 已确认 | 人工核实无误 |
| `needs_evidence` | 需补充证据 | 存在疑点，需标注出处 |
| `rejected` | 已排除 | 判定为事实错误或无需关注 |

### 8.7 审核决定 (`review_record.decision`)

| 值 | 含义 |
| --- | --- |
| `approve` | 通过，可发布 |
| `reject` | 驳回，不可发布 |
| `edit_required` | 需修改后重审 |

### 8.8 来源类型 (`source_type`)

| 值 | 含义 |
| --- | --- |
| `collector` | 采集器自动采集 |
| `manual_import` | 人工手动录入 |

### 8.9 模板分类 (`template_category`)

| 值 | 含义 |
| --- | --- |
| `title_hook` | 标题钩子模板 |
| `opening_hook` | 开头钩子模板 |
| `narrative_frame` | 叙事框架模板 |
| `ending_cta` | 结尾引导模板 |
| `full_script` | 完整脚本模板 |

### 8.10 删除语义约定

第一阶段“删除”统一指控制台发起的逻辑删除动作，数据层按状态归档处理。

| 资源 | 控制台动作文案 | 数据层落点 | 默认列表行为 | 备注 |
| --- | --- | --- | --- | --- |
| `posts` | 删除样本 | `status = archived` | 默认隐藏 | 历史分析、模板引用、发布来源追踪继续保留 |
| `templates` | 删除模板 | `status = archived` | 默认隐藏 | 已归档模板不可用于新生成任务 |
| `publish_records` | 删除发布记录 | `status = archived` | 默认隐藏 | 关联 `performance_snapshots` 保留 |
| `collection_tasks` | 不提供删除 | - | 正常展示 | 第一阶段保留任务追踪链路 |
| `generation_jobs` | 不提供删除 | - | 正常展示 | 第一阶段保留任务追踪链路 |
| `generated_contents` | 不提供删除 | - | 正常展示 | 第一阶段保留版本、审核、发布留痕 |

## 9. 读写权限边界

### 9.1 系统只写，人工只读

1. `platform_sources.created_at`
2. `collection_tasks.status`
3. `collection_tasks.success_count`
4. `analysis_results.model_name`
5. `generation_jobs.status`
6. `generated_contents.source_trace_json`

### 9.2 系统写入，人工可补充或修正

1. `posts.topic_keywords`
2. `posts.is_historical_hot`
3. `analysis_results.fact_check_status`
4. `analysis_results.fact_check_notes`
5. `generated_contents.fact_check_status`
6. `generated_contents.fact_check_notes`

### 9.3 人工主写，系统只归档

1. `review_records`
2. `publish_records`
3. `performance_snapshots`

### 9.4 删除与归档边界

1. 删除动作只允许通过 API 完成，不直接操作数据库物理删行。
2. 对支持删除的核心资源，后端统一通过 `status = archived` 表达归档结果。
3. 已归档资源默认不参与前台列表检索，但仍允许通过详情或关联链路读取历史数据。

## 10. 第一阶段裁剪说明

为保持 MVP 可落地，第一阶段不建议建以下重型对象：

1. 多平台统一调度配置表
2. 自动发布任务表
3. 模型供应商和路由策略表
4. 复杂 RBAC 权限表
