// Status and enum label mappings (English -> Chinese)

export const TASK_STATUS_LABELS: Record<string, string> = {
  pending: '待执行',
  running: '执行中',
  succeeded: '已完成',
  partial_failed: '部分失败',
  failed: '失败',
  cancelled: '已取消',
}

export const POST_STATUS_LABELS: Record<string, string> = {
  raw: '原始入库',
  normalized: '已规范化',
  analyzed: '已分析',
  templated: '已关联模板',
  archived: '已归档',
}

export const TEMPLATE_STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  active: '启用',
  disabled: '停用',
  archived: '已归档',
}

export const GENERATION_JOB_STATUS_LABELS: Record<string, string> = {
  pending: '待处理',
  retrieving: '检索中',
  generating: '生成中',
  reviewing: '审核中',
  completed: '已完成',
  failed: '失败',
}

export const GENERATED_CONTENT_STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  in_review: '审核中',
  approved: '审核通过',
  rejected: '已驳回',
  published: '已发布',
}

export const FACT_CHECK_LABELS: Record<string, string> = {
  pending: '待确认',
  confirmed: '已确认',
  needs_evidence: '需补充证据',
  rejected: '已排除',
}

export const FACT_RISK_LABELS: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
}

export const PUBLISH_STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
}

export const SOURCE_TYPE_LABELS: Record<string, string> = {
  collector: '采集',
  manual_import: '手动录入',
}

export const TASK_TYPE_LABELS: Record<string, string> = {
  historical_hot: '历史高赞',
  keyword_search: '关键词搜索',
}

export const TEMPLATE_CATEGORY_LABELS: Record<string, string> = {
  title_hook: '标题钩子',
  opening_hook: '开头钩子',
  narrative_frame: '叙事框架',
  ending_cta: '结尾引导',
  full_script: '完整脚本',
}

export const PLATFORM_CODE_LABELS: Record<string, string> = {
  zhihu: '知乎',
  bilibili: 'B 站',
  douyin: '抖音',
  xiaohongshu: '小红书',
  weibo: '微博',
}

export const REVIEW_DECISION_LABELS: Record<string, string> = {
  approve: '通过',
  reject: '驳回',
  edit_required: '需修改',
}
