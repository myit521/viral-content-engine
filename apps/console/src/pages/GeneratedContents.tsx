import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getGeneratedContents, type GeneratedContent } from '../api/client'
import { GENERATED_CONTENT_STATUS_LABELS, FACT_CHECK_LABELS } from '../api/labels'

const statusColors: Record<string, string> = {
  draft: '#8c8c8c',
  in_review: '#faad14',
  approved: '#52c41a',
  rejected: '#ff4d4f',
  published: '#1677ff',
}

export default function GeneratedContents() {
  const [items, setItems] = useState<GeneratedContent[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 20

  useEffect(() => {
    loadContents()
  }, [statusFilter, page])

  async function loadContents() {
    setLoading(true)
    try {
      const res = await getGeneratedContents({
        page,
        page_size: pageSize,
        status: statusFilter || undefined,
      })
      setItems(res.data.items)
      setTotal(res.data.total)
    } catch (e) {
      alert('加载生成结果失败: ' + (e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const totalPages = Math.ceil(total / pageSize)

  if (loading) return <p>加载中...</p>

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>生成结果</h2>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
            className="input"
          >
            <option value="">全部状态</option>
            <option value="draft">草稿</option>
            <option value="in_review">审核中</option>
            <option value="approved">已通过</option>
            <option value="rejected">已驳回</option>
            <option value="published">已发布</option>
          </select>
        </div>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>标题</th>
            <th>状态</th>
            <th>事实确认</th>
            <th>版本</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {items.length === 0 && !loading && (
            <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--color-text-secondary)' } as React.CSSProperties}>暂无生成结果</td></tr>
          )}
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.id}</td>
              <td>{item.title || '(无标题)'}</td>
              <td>
                <span style={{
                  display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 12, color: '#fff',
                  background: statusColors[item.status] || '#8c8c8c',
                } as React.CSSProperties}>
                  {GENERATED_CONTENT_STATUS_LABELS[item.status] || item.status}
                </span>
              </td>
              <td>{FACT_CHECK_LABELS[item.fact_check_status] || item.fact_check_status}</td>
              <td>v{item.current_version_no}</td>
              <td>
                <Link to={`/generated-contents/${item.id}/review`} style={{ color: 'var(--color-primary)', marginRight: 12 }}>审核</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 16 }}>
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} className="btn btn-sm">上一页</button>
          <span style={{ lineHeight: '32px', fontSize: 13 }}>第 {page} / {totalPages} 页（共 {total} 条）</span>
          <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="btn btn-sm">下一页</button>
        </div>
      )}
    </div>
  )
}
