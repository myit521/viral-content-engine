import { useState, useEffect } from 'react'
import { createPublishRecord, createSnapshot, getPublishRecords, deletePublishRecord, type PublishRecord } from '../api/client'
import { PUBLISH_STATUS_LABELS, PLATFORM_CODE_LABELS } from '../api/labels'

export default function PublishRecords() {
  const [records, setRecords] = useState<PublishRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [showSnapshot, setShowSnapshot] = useState<string | null>(null)

  useEffect(() => {
    loadRecords()
  }, [])

  // Publish form
  const [contentId, setContentId] = useState('')
  const [platformCode, setPlatformCode] = useState('bilibili')
  const [publishedUrl, setPublishedUrl] = useState('')
  const [publishedAt, setPublishedAt] = useState('')
  const [operator, setOperator] = useState('owner')
  const [notes, setNotes] = useState('')

  // Snapshot form
  const [snapViews, setSnapViews] = useState(0)
  const [snapLikes, setSnapLikes] = useState(0)
  const [snapComments, setSnapComments] = useState(0)
  const [snapFavorites, setSnapFavorites] = useState(0)
  const [snapShares, setSnapShares] = useState(0)

  async function loadRecords() {
    setLoading(true)
    try {
      const res = await getPublishRecords()
      setRecords(res.data.items)
    } catch (e) {
      alert('加载发布记录失败: ' + (e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function handlePublish() {
    if (!contentId.trim()) {
      alert('请输入生成结果 ID')
      return
    }
    try {
      await createPublishRecord({
        generated_content_id: contentId,
        platform_code: platformCode,
        publish_channel: 'manual',
        published_url: publishedUrl || undefined,
        published_at: publishedAt || undefined,
        operator,
        notes: notes || undefined,
      })
      alert('发布记录已创建')
      setShowForm(false)
      setContentId('')
      setPublishedUrl('')
      setPublishedAt('')
      setNotes('')
      loadRecords()
    } catch (e) {
      alert('创建失败: ' + (e as Error).message)
    }
  }

  async function handleSnapshot(recordId: string) {
    try {
      await createSnapshot(recordId, {
        view_count: snapViews || undefined,
        like_count: snapLikes || undefined,
        comment_count: snapComments || undefined,
        favorite_count: snapFavorites || undefined,
        share_count: snapShares || undefined,
        captured_at: new Date().toISOString(),
      })
      alert('效果快照已回填')
      setShowSnapshot(null)
      loadRecords()
    } catch (e) {
      alert('回填失败: ' + (e as Error).message)
    }
  }

  async function handleDelete(recordId: string) {
    if (!confirm('确定要删除该发布记录吗？（逻辑删除，关联快照保留）')) return
    try {
      await deletePublishRecord(recordId)
      alert('发布记录已归档')
      loadRecords()
    } catch (e) {
      alert('删除失败: ' + (e as Error).message)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>发布回填</h2>
        <div>
          <button onClick={() => setShowForm(!showForm)} className="btn">
            {showForm ? '取消' : '新建发布记录'}
          </button>
          <button onClick={loadRecords} className="btn" style={{ marginLeft: 8 }}>刷新</button>
        </div>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 12 }}>新建发布记录</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <label className="label">生成结果 ID *</label>
              <input value={contentId} onChange={(e) => setContentId(e.target.value)} placeholder="gc_xxx" className="input" style={{ width: '100%' }} />
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div>
                <label className="label">发布平台</label>
                <select value={platformCode} onChange={(e) => setPlatformCode(e.target.value)} className="input">
                  <option value="bilibili">B 站</option>
                  <option value="douyin">抖音</option>
                  <option value="xiaohongshu">小红书</option>
                  <option value="zhihu">知乎</option>
                </select>
              </div>
              <div style={{ flex: 1 }}>
                <label className="label">发布链接</label>
                <input value={publishedUrl} onChange={(e) => setPublishedUrl(e.target.value)} placeholder="https://..." className="input" style={{ width: '100%' }} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div>
                <label className="label">发布时间</label>
                <input type="datetime-local" value={publishedAt} onChange={(e) => setPublishedAt(e.target.value)} className="input" />
              </div>
              <div>
                <label className="label">操作人</label>
                <input value={operator} onChange={(e) => setOperator(e.target.value)} className="input" />
              </div>
            </div>
            <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="备注 (可选)" className="input" style={{ width: '100%' }} />
            <button onClick={handlePublish} className="btn">提交</button>
          </div>
        </div>
      )}

      {showSnapshot && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 12 }}>回填效果快照</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
            <div><label className="label">播放量</label><input type="number" value={snapViews} onChange={(e) => setSnapViews(Number(e.target.value))} className="input" style={{ width: '100%' }} /></div>
            <div><label className="label">点赞</label><input type="number" value={snapLikes} onChange={(e) => setSnapLikes(Number(e.target.value))} className="input" style={{ width: '100%' }} /></div>
            <div><label className="label">评论</label><input type="number" value={snapComments} onChange={(e) => setSnapComments(Number(e.target.value))} className="input" style={{ width: '100%' }} /></div>
            <div><label className="label">收藏</label><input type="number" value={snapFavorites} onChange={(e) => setSnapFavorites(Number(e.target.value))} className="input" style={{ width: '100%' }} /></div>
            <div><label className="label">分享</label><input type="number" value={snapShares} onChange={(e) => setSnapShares(Number(e.target.value))} className="input" style={{ width: '100%' }} /></div>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <button onClick={() => handleSnapshot(showSnapshot)} className="btn">提交快照</button>
            <button onClick={() => setShowSnapshot(null)} className="btn" style={{ background: '#8c8c8c' }}>取消</button>
          </div>
        </div>
      )}

      {loading && <p>加载中...</p>}

      <table className="data-table">
        <thead>
          <tr>
            <th >ID</th>
            <th >内容 ID</th>
            <th >平台</th>
            <th >链接</th>
            <th >发布时间</th>
            <th >状态</th>
            <th >操作</th>
          </tr>
        </thead>
        <tbody>
          {records.length === 0 && (
            <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--color-text-secondary)' }}>暂无发布记录</td></tr>
          )}
          {records.map((r) => (
            <tr key={r.id}>
              <td >{r.id}</td>
              <td >{r.generated_content_id}</td>
              <td >{PLATFORM_CODE_LABELS[r.platform_code] || r.platform_code}</td>
              <td >{r.published_url ? <a href={r.published_url} target="_blank" rel="noreferrer">链接</a> : '-'}</td>
              <td >{r.published_at ? new Date(r.published_at).toLocaleString() : '-'}</td>
              <td >{PUBLISH_STATUS_LABELS[r.status] || r.status}</td>
              <td >
                <button onClick={() => setShowSnapshot(r.id)} className="btn btn-sm" style={{ marginRight: 8 }}>回填数据</button>
                {r.status !== 'archived' && (
                  <button onClick={() => handleDelete(r.id)} className="btn btn-sm" style={{ color: '#ff4d4f', background: 'transparent', border: '1px solid #ff4d4f' }}>删除</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
