import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getPost, createAnalysis, factCheckAnalysis, deletePost, getAvailableModels, getPostAnalysisResults, autoSummarizeTemplates, type Post, type AnalysisResult, type ModelOption } from '../api/client'
import { POST_STATUS_LABELS, SOURCE_TYPE_LABELS, FACT_CHECK_LABELS, FACT_RISK_LABELS } from '../api/labels'
import { showToast } from '../components/Toast'

export default function PostDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [post, setPost] = useState<Post | null>(null)
  const [analyses, setAnalyses] = useState<AnalysisResult[]>([])
  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [fcStatus, setFcStatus] = useState('')
  const [fcNotes, setFcNotes] = useState('')
  const [models, setModels] = useState<ModelOption[]>([])
  const [selectedModel, setSelectedModel] = useState('')
  const [modelsLoading, setModelsLoading] = useState(true)
  const [summarizing, setSummarizing] = useState(false)

  async function loadData() {
    if (!id) return
    setLoading(true)
    try {
      const [postRes, analysesRes] = await Promise.all([
        getPost(id),
        getPostAnalysisResults(id),
      ])
      setPost(postRes.data)
      setAnalyses(analysesRes.data)
      if (analysesRes.data.length > 0) {
        setSelectedAnalysis(analysesRes.data[0])
      }
    } catch (e) {
      alert('加载失败: ' + (e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [id])

  useEffect(() => {
    async function loadModels() {
      setModelsLoading(true)
      try {
        const res = await getAvailableModels()
        setModels(res.data.options)
        const defaultName = res.data.default_model
        const defaultModel = res.data.options.find((m) => m.model_name === defaultName) || res.data.options.find((m) => m.enabled)
        if (defaultModel) setSelectedModel(defaultModel.model_name)
      } catch (e) {
        // Fallback to first enabled model
        setSelectedModel('')
      } finally {
        setModelsLoading(false)
      }
    }
    loadModels()
  }, [])

  async function handleAnalyze() {
    if (!id) return
    if (!selectedModel) {
      alert('请先选择 AI 模型')
      return
    }
    setAnalysisLoading(true)
    try {
      const res = await createAnalysis({
        post_id: id,
        prompt_version: 'analysis.zhihu.history.v1',
        model_name: selectedModel,
      })
      setAnalyses(prev => [res.data, ...prev])
      setSelectedAnalysis(res.data)
      alert('分析完成')
    } catch (e) {
      alert('分析失败: ' + (e as Error).message)
    } finally {
      setAnalysisLoading(false)
    }
  }

  async function handleFactCheck() {
    if (!selectedAnalysis) return
    try {
      await factCheckAnalysis(selectedAnalysis.id, {
        fact_check_status: fcStatus,
        reviewer: 'owner',
        notes: fcNotes,
      })
      alert('事实确认已提交')
      loadData()
    } catch (e) {
      alert('提交失败: ' + (e as Error).message)
    }
  }

  async function handleSummarize() {
    if (!id || analyses.length === 0) return
    if (analyses.length < 2) {
      alert('至少需要 2 个分析结果才能归纳模板，当前仅有 ' + analyses.length + ' 个')
      return
    }
    setSummarizing(true)
    try {
      console.log('开始归纳模板，analysis_ids:', analyses.map(a => a.id))
      const res = await autoSummarizeTemplates({
        analysis_ids: analyses.map(a => a.id),
      })
      console.log('归纳响应:', res.data)
      const count = res.data.items?.length || 0
      alert(`归纳完成！已创建 ${count} 个模板，请到模板中心查看`)
    } catch (e: unknown) {
      console.error('归纳错误:', e)
      const errorMsg = (e as Error).message
      alert('归纳失败: ' + errorMsg)
    } finally {
      setSummarizing(false)
    }
  }

  function handleUseForGeneration() {
    if (!id || !selectedAnalysis) return
    const topic = selectedAnalysis.main_topic || ''
    navigate(`/generation?ref_post=${post?.post_id}&topic=${encodeURIComponent(topic)}`)
  }

  async function handleDelete() {
    if (!id) return
    if (!confirm('确定要删除该样本吗？（逻辑删除，可恢复）')) return
    try {
      await deletePost(id)
      alert('样本已归档')
      window.history.back()
    } catch (e) {
      const msg = (e as Error).message
      if (msg.includes('409')) {
        alert('删除失败：该样本仍被其他流程占用')
      } else {
        alert('删除失败: ' + msg)
      }
    }
  }

  if (loading) return <p>加载中...</p>
  if (!post) return <p>样本不存在</p>

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>样本详情: {post.id}</h2>
        {post.status !== 'archived' && (
          <button onClick={handleDelete} className="btn" style={{ color: '#ff4d4f', border: '1px solid #ff4d4f' }}>删除样本</button>
        )}
      </div>

      <div className="card">
        <h3 style={{ marginBottom: 8 }}>基本信息</h3>
        <table style={{ fontSize: 13 }}>
          <tbody>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>标题</td><td>{post.title || '-'}</td></tr>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>来源</td><td>{SOURCE_TYPE_LABELS[post.source_type] || post.source_type}</td></tr>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>状态</td><td>{POST_STATUS_LABELS[post.status] || post.status}</td></tr>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>链接</td><td>{post.source_url ? <a href={post.source_url} target="_blank" rel="noreferrer">{post.source_url}</a> : '-'}</td></tr>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>标签</td><td>{post.topic_keywords.join(', ') || '-'}</td></tr>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>互动</td><td>赞 {post.like_count} | 评 {post.comment_count} | 藏 {post.favorite_count}</td></tr>
          </tbody>
        </table>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3 style={{ marginBottom: 8 }}>
          正文内容
          <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginLeft: 8, fontWeight: 400 }}>
            {post.content_text.length} 字符
          </span>
        </h3>
        <div style={{ maxHeight: 500, overflow: 'auto', whiteSpace: 'pre-wrap', fontSize: 13, lineHeight: 1.7 }}>
          {post.content_text}
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3 style={{ marginBottom: 8 }}>AI 分析</h3>

        {/* 分析历史列表 */}
        {analyses.length > 0 && (
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 13, fontWeight: 500, marginBottom: 4, display: 'block' }}>分析历史:</label>
            <select
              value={selectedAnalysis?.id || ''}
              onChange={(e) => {
                const selected = analyses.find(a => a.id === e.target.value)
                setSelectedAnalysis(selected || null)
              }}
              className="input"
            >
              {analyses.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.model_name} - {a.created_at ? new Date(a.created_at).toLocaleString() : '未知时间'}
                </option>
              ))}
            </select>
          </div>
        )}

        {selectedAnalysis ? (
          <div>
            <p><strong>主题:</strong> {selectedAnalysis.main_topic || '-'}</p>
            <p><strong>钩子:</strong> {selectedAnalysis.hook_text || '-'}</p>
            <p><strong>情绪驱动:</strong> {selectedAnalysis.emotional_driver || '-'}</p>
            <p><strong>事实风险:</strong> {FACT_RISK_LABELS[selectedAnalysis.fact_risk_level] || selectedAnalysis.fact_risk_level}</p>
            <p><strong>事实确认:</strong> {FACT_CHECK_LABELS[selectedAnalysis.fact_check_status] || selectedAnalysis.fact_check_status}</p>

            {/* 分析后操作入口 */}
            <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
              <button onClick={handleSummarize} className="btn" disabled={summarizing} style={{ fontSize: 13 }}>
                {summarizing ? '归纳中...' : '从分析结果归纳模板'}
              </button>
              <button onClick={handleUseForGeneration} className="btn" style={{ fontSize: 13, background: '#1677ff' }}>
                用于生成
              </button>
            </div>

            <div style={{ marginTop: 12, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
              <h4 style={{ marginBottom: 8 }}>事实确认</h4>
              <select value={fcStatus} onChange={(e) => setFcStatus(e.target.value)} className="input">
                <option value="">选择状态</option>
                <option value="confirmed">已确认</option>
                <option value="needs_evidence">需补充证据</option>
                <option value="rejected">已排除</option>
              </select>
              <textarea
                value={fcNotes}
                onChange={(e) => setFcNotes(e.target.value)}
                placeholder="确认说明"
                rows={2}
                className="input" style={{ marginTop: 8, width: '100%', resize: 'vertical' } as React.CSSProperties}
              />
              <button onClick={handleFactCheck} className="btn" style={{ marginTop: 8 }}>提交确认</button>
            </div>
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: 12, display: 'flex', gap: 8, alignItems: 'center' }}>
              <label style={{ fontSize: 13, fontWeight: 500 }}>AI 模型:</label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="input"
                disabled={modelsLoading}
                style={{ minWidth: 200 }}
              >
                <option value="">选择模型</option>
                {models.filter(m => m.enabled).map((m) => (
                  <option key={m.model_name} value={m.model_name}>
                    {m.label}{m.recommended ? ' (推荐)' : ''}
                  </option>
                ))}
              </select>
              {modelsLoading && <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>加载中...</span>}
            </div>
            <button onClick={handleAnalyze} className="btn" disabled={!selectedModel || modelsLoading || analysisLoading}>
              {analysisLoading ? '分析中...' : '发起 AI 分析'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

