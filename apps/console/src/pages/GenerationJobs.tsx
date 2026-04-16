import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { createGenerationJob, getGenerationJobs, getAvailableModels, getPosts, getTemplates, type GenerationJob, type ModelOption, type Post, type Template } from '../api/client'
import { GENERATION_JOB_STATUS_LABELS, POST_STATUS_LABELS } from '../api/labels'

const statusColors: Record<string, string> = {
  pending: '#faad14',
  retrieving: '#1677ff',
  generating: '#1677ff',
  reviewing: '#faad14',
  completed: '#52c41a',
  failed: '#ff4d4f',
}

export default function GenerationJobs() {
  const [searchParams] = useSearchParams()
  const [topic, setTopic] = useState('')
  const [brief, setBrief] = useState('')
  const [templateId, setTemplateId] = useState('')
  const [modelName, setModelName] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [jobs, setJobs] = useState<GenerationJob[]>([])
  const [loading, setLoading] = useState(false)
  const [models, setModels] = useState<ModelOption[]>([])
  const [modelsLoading, setModelsLoading] = useState(true)
  const [modelsError, setModelsError] = useState('')

  // 样本选择器状态
  const [posts, setPosts] = useState<Post[]>([])
  const [selectedPostIds, setSelectedPostIds] = useState<string[]>([])
  const [postSearchKeyword, setPostSearchKeyword] = useState('')
  const [postsLoading, setPostsLoading] = useState(false)

  // 模板选择器状态
  const [templates, setTemplates] = useState<Template[]>([])
  const [templatesLoading, setTemplatesLoading] = useState(false)

  useEffect(() => {
    loadJobs()
    loadModels()
    loadPosts()
    loadTemplates()

    // 从 URL 参数预填
    const refPost = searchParams.get('ref_post')
    const refTopic = searchParams.get('topic')
    if (refPost) {
      setSelectedPostIds([refPost])
    }
    if (refTopic) {
      setTopic(decodeURIComponent(refTopic))
    }
  }, [])

  async function loadModels() {
    setModelsLoading(true)
    try {
      const res = await getAvailableModels()
      setModels(res.data.options)
      const defaultName = res.data.default_model
      const defaultModel = res.data.options.find((m) => m.model_name === defaultName) || res.data.options.find((m) => m.enabled)
      if (defaultModel) setModelName(defaultModel.model_name)
    } catch (e) {
      setModelsError('模型配置接口不可用，已使用默认选项')
      setModels([
        { model_name: 'gpt-4.1', label: 'GPT-4.1', provider: 'openai', enabled: true, recommended: false, description: '', scene: 'generation', supported_task_types: [] },
        { model_name: 'gpt-4.1-mini', label: 'GPT-4.1 Mini', provider: 'openai', enabled: true, recommended: false, description: '', scene: 'generation', supported_task_types: [] },
      ])
      setModelName('gpt-4.1')
    } finally {
      setModelsLoading(false)
    }
  }

  async function loadJobs() {
    setLoading(true)
    try {
      const res = await getGenerationJobs({ page: 1, page_size: 50 })
      setJobs(res.data.items)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function loadPosts() {
    setPostsLoading(true)
    try {
      const res = await getPosts({ page_size: 100, status: 'analyzed' })
      setPosts(res.data.items)
    } catch (e) {
      console.error('加载样本失败:', e)
    } finally {
      setPostsLoading(false)
    }
  }

  async function loadTemplates() {
    setTemplatesLoading(true)
    try {
      const res = await getTemplates({ status: 'active', page_size: 100 })
      setTemplates(res.data.items)
    } catch (e) {
      console.error('加载模板失败:', e)
    } finally {
      setTemplatesLoading(false)
    }
  }

  function togglePost(postId: string) {
    setSelectedPostIds(prev =>
      prev.includes(postId) ? prev.filter(id => id !== postId) : [...prev, postId]
    )
  }

  const filteredPosts = postSearchKeyword
    ? posts.filter(p =>
        (p.title || '').includes(postSearchKeyword) ||
        (p.topic_keywords || []).some(kw => kw.includes(postSearchKeyword))
      )
    : posts

  async function handleSubmit() {
    if (!topic.trim()) {
      alert('请输入主题')
      return
    }
    setSubmitting(true)
    try {
      const res = await createGenerationJob({
        job_type: 'script_generation',
        topic,
        brief: brief || undefined,
        selected_template_id: templateId || undefined,
        reference_post_ids: selectedPostIds.length > 0 ? selectedPostIds : undefined,
        prompt_version: 'generation.zhihu_to_video.v1',
        model_name: modelName,
      })
      alert(`生成任务已创建: ${res.data.id}`)
      setTopic('')
      setBrief('')
      setSelectedPostIds([])
      loadJobs()
    } catch (e) {
      alert('创建失败: ' + (e as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>内容生成</h2>

      <div className="card">
        <h3 style={{ marginBottom: 12 }}>新建生成任务</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <label className="label">主题 *</label>
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="如: 如果秦始皇多活十年"
              className="input"
              style={{ width: '100%' } as React.CSSProperties}
            />
          </div>
          <div>
            <label className="label">简要说明</label>
            <textarea
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
              placeholder="如: 做成 60 秒短视频口播稿"
              rows={2}
              className="input"
              style={{ width: '100%', resize: 'vertical' } as React.CSSProperties}
            />
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <div>
              <label className="label">模板 (可选)</label>
              {templatesLoading ? (
                <div className="input" style={{ color: 'var(--color-text-secondary)' }}>加载中...</div>
              ) : (
                <select value={templateId} onChange={(e) => setTemplateId(e.target.value)} className="input" style={{ minWidth: 200 }}>
                  <option value="">不使用模板</option>
                  {templates.map(t => (
                    <option key={t.id} value={t.id}>
                      {t.name} ({t.template_category})
                    </option>
                  ))}
                </select>
              )}
            </div>
            <div>
              <label className="label">模型</label>
              {modelsLoading ? (
                <div className="input" style={{ color: 'var(--color-text-secondary)', minWidth: 160 }}>加载中...</div>
              ) : (
                <>
                  <select value={modelName} onChange={(e) => setModelName(e.target.value)} className="input">
                    {models.filter((m) => m.enabled).map((m) => (
                      <option key={m.model_name} value={m.model_name}>
                        {m.label}{m.recommended ? ' (推荐)' : ''}
                      </option>
                    ))}
                  </select>
                  {modelsError && <p style={{ fontSize: 11, color: '#faad14', margin: '2px 0 0' }}>{modelsError}</p>}
                </>
              )}
            </div>
          </div>

          {/* 参考样本多选器 */}
          <div>
            <label className="label">参考样本 (可选)</label>
            <input
              value={postSearchKeyword}
              onChange={(e) => setPostSearchKeyword(e.target.value)}
              placeholder="搜索样本 (标题/关键词)"
              className="input"
              style={{ width: '100%', marginBottom: 8 } as React.CSSProperties}
            />
            {postsLoading ? (
              <p style={{ color: 'var(--color-text-secondary)' }}>加载样本中...</p>
            ) : (
              <div style={{ maxHeight: 200, overflow: 'auto', border: '1px solid var(--color-border)', borderRadius: 4, padding: 8 }}>
                {filteredPosts.length === 0 ? (
                  <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>无匹配样本</p>
                ) : (
                  filteredPosts.map(post => (
                    <label key={post.post_id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={selectedPostIds.includes(post.post_id)}
                        onChange={() => togglePost(post.post_id)}
                      />
                      <span style={{ fontSize: 13 }}>
                        {post.title || '(无标题)'}
                        <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--color-text-secondary)' }}>
                          赞 {post.like_count} | 评 {post.comment_count}
                        </span>
                      </span>
                      <span style={{
                        marginLeft: 'auto',
                        fontSize: 11,
                        padding: '1px 6px',
                        borderRadius: 3,
                        background: '#f0f0f0',
                      }}>
                        {POST_STATUS_LABELS[post.status] || post.status}
                      </span>
                    </label>
                  ))
                )}
              </div>
            )}
            {selectedPostIds.length > 0 && (
              <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', margin: '4px 0 0' }}>
                已选择 {selectedPostIds.length} 个样本
              </p>
            )}
          </div>

          <button onClick={handleSubmit} disabled={submitting} className="btn">
            {submitting ? '生成中...' : '开始生成'}
          </button>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h3 style={{ margin: 0 }}>任务记录</h3>
          <button onClick={loadJobs} className="btn btn-sm">刷新</button>
        </div>

        {loading && <p>加载中...</p>}

        <table className="data-table">
          <thead>
            <tr>
              <th>任务 ID</th>
              <th>主题</th>
              <th>模型</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {jobs.length === 0 && !loading && (
              <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--color-text-secondary)' }}>暂无生成任务</td></tr>
            )}
            {jobs.map((j) => (
              <tr key={j.id}>
                <td>{j.id}</td>
                <td>{j.topic}</td>
                <td>{j.model_name}</td>
                <td>
                  <span style={{
                    display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 12, color: '#fff',
                    background: statusColors[j.status] || '#8c8c8c',
                  } as React.CSSProperties}>
                    {GENERATION_JOB_STATUS_LABELS[j.status] || j.status}
                  </span>
                </td>
                <td>{new Date(j.created_at).toLocaleString()}</td>
                <td>
                  {j.status === 'reviewing' || j.status === 'completed' ? (
                    <Link to="/generated-contents" style={{ color: 'var(--color-primary)' }}>查看结果</Link>
                  ) : (
                    <span style={{ color: 'var(--color-text-secondary)' }}>-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
