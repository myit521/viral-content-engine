import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  getCollectorTasks,
  createCollectorTask,
  runCollectorTask,
  getPlatforms,
  type CollectorTask,
  type Platform,
} from '../api/client'
import { TASK_STATUS_LABELS, TASK_TYPE_LABELS } from '../api/labels'

const statusColors: Record<string, string> = {
  pending: '#faad14',
  running: '#1677ff',
  succeeded: '#52c41a',
  partial_failed: '#fa8c16',
  failed: '#ff4d4f',
  cancelled: '#8c8c8c',
}

export default function CollectorTasks() {
  const [tasks, setTasks] = useState<CollectorTask[]>([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [taskType, setTaskType] = useState('historical_hot')
  const [platformCode, setPlatformCode] = useState('')
  const [platforms, setPlatforms] = useState<Platform[]>([])

  useEffect(() => {
    loadTasks()
    loadPlatforms()
  }, [])

  async function loadPlatforms() {
    try {
      const res = await getPlatforms()
      setPlatforms(res.data)
      const defaultPlatform = res.data.find(p => p.enabled) || res.data[0]
      if (defaultPlatform) setPlatformCode(defaultPlatform.code)
    } catch (e) {
      console.error('加载平台失败:', e)
    }
  }

  async function loadTasks() {
    setLoading(true)
    try {
      const res = await getCollectorTasks({ page: 1, page_size: 50 })
      setTasks(res.data.items)
    } catch (e) {
      alert('加载任务列表失败: ' + (e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate() {
    try {
      const res = await createCollectorTask({
        platform_code: 'zhihu',
        task_type: taskType,
        query_keyword: keyword || undefined,
      })
      alert(`任务已创建: ${res.data.task_id}`)
      setShowForm(false)
      loadTasks()
    } catch (e) {
      alert('创建任务失败: ' + (e as Error).message)
    }
  }

  async function handleRun(taskId: string) {
    try {
      await runCollectorTask(taskId)
      alert('任务已触发')
      loadTasks()
    } catch (e) {
      alert('触发任务失败: ' + (e as Error).message)
    }
  }

  useEffect(() => { loadTasks() }, [])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>采集任务</h2>
        <div>
          <button onClick={() => setShowForm(!showForm)} className="btn">
            {showForm ? '取消' : '新建任务'}
          </button>
          <button onClick={loadTasks} className="btn" style={{ marginLeft: 8 }}>刷新</button>
        </div>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
            <div>
              <label className="label">平台</label>
              <select value={platformCode} onChange={(e) => setPlatformCode(e.target.value)} className="input">
                <option value="">选择平台</option>
                {platforms.filter(p => p.enabled).map(p => (
                  <option key={p.code} value={p.code}>{p.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">任务类型</label>
              <select value={taskType} onChange={(e) => setTaskType(e.target.value)} className="input">
                <option value="historical_hot">历史高赞</option>
                <option value="keyword_search">关键词搜索</option>
              </select>
            </div>
            <div>
              <label className="label">关键词</label>
              <input
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="如: 历史人物"
                className="input"
              />
            </div>
            <button onClick={handleCreate} className="btn">创建</button>
          </div>
        </div>
      )}

      {loading && <p>加载中...</p>}

      <table className="data-table">
        <thead>
          <tr>
            <th>任务 ID</th>
            <th>类型</th>
            <th>关键词</th>
            <th>状态</th>
            <th>成功</th>
            <th>失败</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {tasks.length === 0 && (
            <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--color-text-secondary)' } as React.CSSProperties}>暂无任务</td></tr>
          )}
          {tasks.map((t) => (
            <tr key={t.id}>
              <td><Link to={`/tasks/${t.id}`} style={{ color: 'var(--color-primary)' }}>{t.id}</Link></td>
              <td>{TASK_TYPE_LABELS[t.task_type] || t.task_type}</td>
              <td>{t.query_keyword || '-'}</td>
              <td>
                <span style={{
                  display: 'inline-block',
                  padding: '2px 8px',
                  borderRadius: 4,
                  fontSize: 12,
                  color: '#fff',
                  background: statusColors[t.status] || '#8c8c8c',
                }}>
                  {TASK_STATUS_LABELS[t.status] || t.status}
                </span>
              </td>
              <td>{t.success_count}</td>
              <td>{t.failed_count}</td>
              <td>
                {t.status === 'pending' && (
                  <button onClick={() => handleRun(t.id)} className="btn btn-sm">执行</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
