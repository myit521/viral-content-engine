const API_BASE = '/api/v1'
const REQUEST_TIMEOUT = 120000

interface ApiResponse<T = unknown> {
  code: string
  message: string
  data: T
  request_id: string
}

interface PagedData<T> {
  items: T[]
  page: number
  page_size: number
  total: number
}

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT)
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
      signal: controller.signal,
    })
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`)
    }
    return res.json()
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') {
      throw new Error('请求超时，请检查后端服务(localhost:8000)是否已启动')
    }
    if (e instanceof TypeError && (e.message.includes('fetch') || e.message.includes('network') || e.message.includes('Failed'))) {
      throw new Error('网络错误，请检查后端服务(localhost:8000)是否已启动')
    }
    throw e
  } finally {
    clearTimeout(timer)
  }
}

// --- Platform & Config ---

export async function getPlatforms() {
  return request<Platform[]>('/platforms')
}

export interface Platform {
  id: number
  code: string
  name: string
  enabled: boolean
  mvp_enabled: boolean
}

export async function getAvailableModels(scene?: string) {
  const qs = scene ? `?scene=${encodeURIComponent(scene)}` : ''
  return request<ModelOptionsResponse>(`/model-options${qs}`)
}

export interface ModelOption {
  model_name: string
  label: string
  provider: string
  enabled: boolean
  recommended: boolean
  description: string
  scene: string
  supported_task_types: string[]
}

export interface ModelOptionsResponse {
  scene: string
  default_model: string
  options: ModelOption[]
}

// --- Collector Tasks ---

export async function getCollectorTasks(params?: {
  page?: number
  page_size?: number
  status?: string
}) {
  const qs = new URLSearchParams()
  if (params?.page) qs.set('page', String(params.page))
  if (params?.page_size) qs.set('page_size', String(params.page_size))
  if (params?.status) qs.set('status', params.status)
  const query = qs.toString()
  return request<PagedData<CollectorTask>>(`/collector-tasks${query ? `?${query}` : ''}`)
}

export async function createCollectorTask(body: {
  platform_code: string
  task_type: string
  query_keyword?: string
  date_range_start?: string
  date_range_end?: string
  limit?: number
}) {
  return request<{ task_id: string; status: string }>('/collector-tasks', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function getCollectorTask(taskId: string) {
  return request<CollectorTask>(`/collector-tasks/${taskId}`)
}

export async function runCollectorTask(taskId: string) {
  return request<CollectorTask>(`/collector-tasks/${taskId}/run`, {
    method: 'POST',
  })
}

export interface CollectorTask {
  id: string
  task_id: string
  platform_code: string
  task_type: string
  query_keyword: string | null
  collect_type: string | null
  source_url: string | null
  source_id: string | null
  trigger_mode: string
  status: string
  execution_status: string
  success_count: number
  failed_count: number
  retry_count: number
  raw_output_path: string | null
  error_message: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string
  updated_at: string
}

// --- Posts ---

export async function getPosts(params?: {
  page?: number
  page_size?: number
  source_type?: string
  status?: string
  keyword?: string
  include_archived?: boolean
}) {
  const qs = new URLSearchParams()
  if (params?.page) qs.set('page', String(params.page))
  if (params?.page_size) qs.set('page_size', String(params.page_size))
  if (params?.source_type) qs.set('source_type', params.source_type)
  if (params?.status) qs.set('status', params.status)
  if (params?.keyword) qs.set('keyword', params.keyword)
  if (params?.include_archived) qs.set('include_archived', String(params.include_archived))
  const query = qs.toString()
  return request<PagedData<Post>>(`/posts${query ? `?${query}` : ''}`)
}

export async function getPost(postId: string) {
  return request<Post>(`/posts/${postId}`)
}

export async function manualImportPost(body: {
  platform_code: string
  source_url?: string
  title?: string
  content_text: string
  author_name?: string
  published_at?: string
  topic_keywords?: string[]
  note?: string
}) {
  return request<Post>('/posts/manual-import', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function updatePost(postId: string, body: {
  topic_keywords?: string[]
  is_historical_hot?: boolean
  note?: string
}) {
  return request<Post>(`/posts/${postId}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export async function deletePost(postId: string) {
  return request<{ post_id: string; status: string }>(`/posts/${postId}`, {
    method: 'DELETE',
  })
}

export interface Post {
  id: string
  post_id: string
  platform_code: string
  title: string | null
  content_text: string
  source_url: string | null
  source_type: string
  author_name: string | null
  published_at: string | null
  like_count: number
  comment_count: number
  favorite_count: number
  share_count: number
  view_count: number
  is_historical_hot: boolean
  note: string | null
  topic_keywords: string[]
  status: string
  created_at: string
  updated_at: string
}

// --- Analysis Results ---

export async function createAnalysis(body: {
  post_id: string
  analysis_version?: string
  prompt_version: string
  model_name: string
}) {
  return request<AnalysisResult>('/analysis-results', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function getAnalysisResult(analysisId: string) {
  return request<AnalysisResult>(`/analysis-results/${analysisId}`)
}

export async function factCheckAnalysis(analysisId: string, body: {
  fact_check_status: string
  reviewer: string
  notes?: string
  risk_items?: Array<{ claim: string; decision: string; evidence_note: string }>
}) {
  return request<AnalysisResult>(`/analysis-results/${analysisId}/fact-check`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function getPostAnalysisResults(postId: string) {
  return request<AnalysisResult[]>(`/posts/${postId}/analysis-results`)
}

export interface AnalysisResult {
  id: string
  analysis_id: string
  post_id: string
  analysis_version: string
  prompt_version: string
  model_name: string
  summary: string | null
  main_topic: string | null
  hook_text: string | null
  narrative_structure: Record<string, unknown> | null
  emotional_driver: string | null
  fact_risk_level: string
  fact_risk_items: string[]
  fact_check_status: string
  fact_check_reviewer: string | null
  fact_check_notes: string | null
  created_at: string
}

// --- Templates ---

export async function getTemplates(params?: {
  page?: number
  page_size?: number
  template_category?: string
  status?: string
  include_archived?: boolean
}) {
  const qs = new URLSearchParams()
  if (params?.page) qs.set('page', String(params.page))
  if (params?.page_size) qs.set('page_size', String(params.page_size))
  if (params?.template_category) qs.set('template_category', params.template_category)
  if (params?.status) qs.set('status', params.status)
  if (params?.include_archived) qs.set('include_archived', String(params.include_archived))
  const query = qs.toString()
  return request<PagedData<Template>>(`/templates${query ? `?${query}` : ''}`)
}

export async function createTemplate(body: {
  template_type: string
  template_category: string
  name: string
  applicable_platform: string
  applicable_topic: string
  applicable_scene?: string
  structure_json: Record<string, unknown>
  source_post_ids?: string[]
}) {
  return request<Template>('/templates', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function getTemplate(templateId: string) {
  return request<Template>(`/templates/${templateId}`)
}

export async function updateTemplateStatus(templateId: string, body: {
  status: string
}) {
  return request<Template>(`/templates/${templateId}/status`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function deleteTemplate(templateId: string) {
  return request<{ template_id: string; status: string }>(`/templates/${templateId}`, {
    method: 'DELETE',
  })
}

export async function autoSummarizeTemplates(body: {
  analysis_ids: string[]
  template_type?: string
  template_category?: string
  applicable_platform?: string
  applicable_topic?: string
  applicable_scene?: string
  min_cluster_size?: number
}) {
  return request<{
    created_count: number
    items: Template[]
    meta: Record<string, unknown>
  }>(
    '/templates/auto-summarize',
    { method: 'POST', body: JSON.stringify(body) }
  )
}

export async function generateTemplate(body: {
  name?: string
  generation_goal?: string
  template_type: string
  template_category: string
  applicable_platform: string
  applicable_topic: string
  applicable_scene?: string
  requirements?: string
  model_name?: string
}) {
  return request<Template>('/templates/ai-generate', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export interface Template {
  id: string
  template_id: string
  template_type: string
  template_category: string
  name: string
  applicable_platform: string
  applicable_topic: string
  applicable_scene: string | null
  structure_json: Record<string, unknown>
  source_post_ids: string[]
  status: string
  created_at: string
  updated_at: string
}

// --- Generation Jobs ---

export async function createGenerationJob(body: {
  job_type: string
  topic: string
  brief?: string
  selected_template_id?: string
  reference_post_ids?: string[]
  prompt_version: string
  model_name: string
}) {
  return request<GenerationJob>('/generation-jobs', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function getGenerationJobs(params?: {
  page?: number
  page_size?: number
  status?: string
}) {
  const qs = new URLSearchParams()
  if (params?.page) qs.set('page', String(params.page))
  if (params?.page_size) qs.set('page_size', String(params.page_size))
  if (params?.status) qs.set('status', params.status)
  const query = qs.toString()
  return request<PagedData<GenerationJob>>(`/generation-jobs${query ? `?${query}` : ''}`)
}

export async function getGenerationJob(jobId: string) {
  return request<GenerationJob>(`/generation-jobs/${jobId}`)
}

export async function getGeneratedContents(params?: {
  page?: number
  page_size?: number
  status?: string
  job_id?: string
}) {
  const qs = new URLSearchParams()
  if (params?.page) qs.set('page', String(params.page))
  if (params?.page_size) qs.set('page_size', String(params.page_size))
  if (params?.status) qs.set('status', params.status)
  if (params?.job_id) qs.set('job_id', params.job_id)
  const query = qs.toString()
  return request<PagedData<GeneratedContent>>(`/generated-contents${query ? `?${query}` : ''}`)
}

export async function getGeneratedContent(contentId: string) {
  return request<GeneratedContent>(`/generated-contents/${contentId}`)
}

export async function getReviewCompare(contentId: string) {
  return request<ReviewCompareData>(`/generated-contents/${contentId}/review-compare`)
}

export async function createVersion(contentId: string, body: {
  editor: string
  title?: string
  script_text: string
  edit_note?: string
}) {
  return request<GeneratedContentVersion>(`/generated-contents/${contentId}/versions`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export interface GenerationJob {
  id: string
  job_id: string
  job_type: string
  topic: string
  brief: string | null
  selected_template_id: string | null
  reference_post_ids: string[]
  prompt_version: string
  model_name: string
  status: string
  generated_content: Record<string, unknown> | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface GeneratedContent {
  id: string
  content_id: string
  title: string | null
  script_text: string
  storyboard_json: Record<string, unknown> | null
  cover_text: string | null
  publish_caption: string | null
  hashtags: string[]
  source_trace: Record<string, unknown>
  status: string
  fact_check_status: string
  fact_check_notes: string | null
  current_version_no: number
  created_at: string
  updated_at: string
}

export interface GeneratedContentVersion {
  id: string
  generated_content_id: string
  version_no: number
  title: string | null
  script_text: string
  storyboard_json: Record<string, unknown> | null
  cover_text: string | null
  publish_caption: string | null
  edit_note: string | null
  editor: string
  created_at: string
}

export interface ReviewCompareData {
  generated_content_id: string
  source_summary: string[]
  initial_draft: {
    version_no: number
    title: string | null
    script_text: string
  } | null
  current_edit: {
    version_no: number
    title: string | null
    script_text: string
  } | null
  final_draft: {
    version_no: number
    title: string | null
    script_text: string
  } | null
}

// --- Reviews ---

export async function submitReview(body: {
  generated_content_id: string
  reviewer: string
  decision: string
  comment?: string
  fact_check_status?: string
}) {
  return request<ReviewRecord>('/reviews', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export interface ReviewRecord {
  id: string
  generated_content_id: string
  reviewer: string
  decision: string
  comment: string | null
  fact_check_status: string | null
  selected_version_no: number | null
  reviewed_at: string
}

// --- Publish Records ---

export async function createPublishRecord(body: {
  generated_content_id: string
  platform_code: string
  publish_channel: string
  published_url?: string
  published_at?: string
  operator: string
  notes?: string
}) {
  return request<PublishRecord>('/publish-records', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function createSnapshot(publishRecordId: string, body: {
  like_count?: number
  comment_count?: number
  favorite_count?: number
  share_count?: number
  view_count?: number
  retention_rate?: number
  captured_at: string
}) {
  return request<PerformanceSnapshot>(`/publish-records/${publishRecordId}/snapshots`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function getPublishRecords(params?: {
  include_archived?: boolean
}) {
  const qs = new URLSearchParams()
  if (params?.include_archived) qs.set('include_archived', String(params.include_archived))
  const query = qs.toString()
  return request<PagedData<PublishRecord>>(`/publish-records${query ? `?${query}` : ''}`)
}

export async function deletePublishRecord(publishRecordId: string) {
  return request<{ publish_record_id: string; status: string }>(`/publish-records/${publishRecordId}`, {
    method: 'DELETE',
  })
}

export interface PublishRecord {
  id: string
  generated_content_id: string
  platform_code: string
  publish_channel: string
  published_url: string | null
  published_at: string | null
  operator: string
  status: string
  notes: string | null
  created_at: string
  updated_at: string
}

export interface PerformanceSnapshot {
  id: string
  publish_record_id: string
  like_count: number
  comment_count: number
  favorite_count: number
  share_count: number
  view_count: number
  retention_rate: number | null
  captured_at: string
  created_at: string
}
