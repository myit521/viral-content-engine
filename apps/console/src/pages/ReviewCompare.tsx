import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getGeneratedContent,
  getReviewCompare,
  createVersion,
  submitReview,
  type GeneratedContent,
  type ReviewCompareData,
} from '../api/client'

export default function ReviewCompare() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [content, setContent] = useState<GeneratedContent | null>(null)
  const [compareData, setCompareData] = useState<ReviewCompareData | null>(null)
  const [loading, setLoading] = useState(true)

  // Edit form
  const [editTitle, setEditTitle] = useState('')
  const [editScript, setEditScript] = useState('')
  const [editNote, setEditNote] = useState('')

  // Review form
  const [reviewDecision, setReviewDecision] = useState('approve')
  const [reviewComment, setReviewComment] = useState('')

  useEffect(() => {
    if (!id) return
    loadData()
  }, [id])

  async function loadData() {
    if (!id) return
    setLoading(true)
    try {
      const [contentRes, compareRes] = await Promise.all([
        getGeneratedContent(id),
        getReviewCompare(id),
      ])
      setContent(contentRes.data)
      setCompareData(compareRes.data)
      setEditTitle(contentRes.data.title || '')
      setEditScript(contentRes.data.script_text)
    } catch (e) {
      alert('加载失败: ' + (e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function handleSaveVersion() {
    if (!id || !editScript.trim()) {
      alert('脚本文本不能为空')
      return
    }
    try {
      await createVersion(id, {
        editor: 'owner',
        title: editTitle || undefined,
        script_text: editScript,
        edit_note: editNote || undefined,
      })
      alert('版本已保存')
      loadData()
    } catch (e) {
      alert('保存失败: ' + (e as Error).message)
    }
  }

  async function handleSubmitReview() {
    if (!id) return
    try {
      await submitReview({
        generated_content_id: id,
        reviewer: 'owner',
        decision: reviewDecision,
        comment: reviewComment || undefined,
      })
      alert('审核已提交')
      navigate('/generated-contents')
    } catch (e) {
      alert('提交失败: ' + (e as Error).message)
    }
  }

  if (loading) return <p>加载中...</p>
  if (!content) return <p>生成结果不存在</p>

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>审核: {content.title || content.id}</h2>

      {/* Comparison View */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        <div className="card">
          <h3 style={{ marginBottom: 8 }}>AI 初稿</h3>
          {compareData?.initial_draft ? (
            <>
              <p style={{ fontWeight: 600 }}>{compareData.initial_draft.title || '-'}</p>
              <pre style={{ fontSize: 13, lineHeight: 1.7, whiteSpace: 'pre-wrap', margin: 0 } as React.CSSProperties}>{compareData.initial_draft.script_text}</pre>
            </>
          ) : (
            <p style={{ color: 'var(--color-text-secondary)' }}>无初稿数据</p>
          )}
        </div>
        <div className="card">
          <h3 style={{ marginBottom: 8 }}>参考来源</h3>
          {compareData?.source_summary && compareData.source_summary.length > 0 ? (
            <ul style={{ paddingLeft: 20, margin: 0 }}>
              {compareData.source_summary.map((postId, i) => (
                <li key={i} style={{ marginBottom: 4 }}>
                  <code style={{ fontSize: 12 }}>{postId}</code>
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ color: 'var(--color-text-secondary)' }}>无参考来源</p>
          )}
        </div>
      </div>

      {/* Edit Form */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginBottom: 12 }}>编辑当前版本</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <input
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            placeholder="标题"
            className="input"
          />
          <textarea
            value={editScript}
            onChange={(e) => setEditScript(e.target.value)}
            placeholder="脚本文本"
            rows={10}
            className="input"
            style={{ resize: 'vertical', fontFamily: 'inherit' } as React.CSSProperties}
          />
          <input
            value={editNote}
            onChange={(e) => setEditNote(e.target.value)}
            placeholder="编辑说明 (可选)"
            className="input"
          />
          <button onClick={handleSaveVersion} className="btn">保存版本</button>
        </div>
      </div>

      {/* Review Form */}
      <div className="card">
        <h3 style={{ marginBottom: 12 }}>提交审核</h3>
        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
          <div>
            <label className="label">决定</label>
            <select value={reviewDecision} onChange={(e) => setReviewDecision(e.target.value)} className="input">
              <option value="approve">通过</option>
              <option value="reject">驳回</option>
              <option value="edit_required">需修改</option>
            </select>
          </div>
          <div style={{ flex: 1 }}>
            <label className="label">意见</label>
            <input
              value={reviewComment}
              onChange={(e) => setReviewComment(e.target.value)}
              placeholder="审核意见 (可选)"
              className="input"
              style={{ width: '100%' } as React.CSSProperties}
            />
          </div>
          <button onClick={handleSubmitReview} className="btn">提交</button>
        </div>
      </div>
    </div>
  )
}
