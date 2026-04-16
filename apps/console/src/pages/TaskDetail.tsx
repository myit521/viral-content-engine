import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getCollectorTask, runCollectorTask, type CollectorTask } from '../api/client'
import { TASK_STATUS_LABELS, TASK_TYPE_LABELS } from '../api/labels'

const statusColors: Record<string, string> = {
  pending: '#faad14',
  running: '#1677ff',
  succeeded: '#52c41a',
  partial_failed: '#fa8c16',
  failed: '#ff4d4f',
  cancelled: '#8c8c8c',
}

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>()
  const [task, setTask] = useState<CollectorTask | null>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  useEffect(() => {
    if (!id) return
    loadData()
  }, [id])

  async function loadData() {
    if (!id) return
    setLoading(true)
    try {
      const res = await getCollectorTask(id)
      setTask(res.data)
    } catch (e) {
      alert('加载任务详情失败: ' + (e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function handleRun() {
    if (!id) return
    setRunning(true)
    try {
      await runCollectorTask(id)
      alert('任务已触发')
      loadData()
    } catch (e) {
      alert('触发失败: ' + (e as Error).message)
    } finally {
      setRunning(false)
    }
  }

  if (loading) return <p>加载中...</p>
  if (!task) return <p>任务不存在</p>

  const fields: { label: string; value: React.ReactNode }[] = [
    { label: '任务 ID', value: task.id },
    { label: '任务类型', value: TASK_TYPE_LABELS[task.task_type] || task.task_type },
    { label: '关键词', value: task.query_keyword || '-' },
    { label: '时间范围', value: '-' },
    { label: '触发方式', value: task.trigger_mode },
    { label: '状态', value: (
      <span style={{
        display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 12, color: '#fff',
        background: statusColors[task.status] || '#8c8c8c',
      }}>
        {TASK_STATUS_LABELS[task.status] || task.status}
      </span>
    )},
    { label: '成功数', value: task.success_count },
    { label: '失败数', value: task.failed_count },
    { label: '错误信息', value: task.error_message || '-' },
    { label: '原始文件路径', value: task.raw_output_path || '-' },
    { label: '开始时间', value: task.started_at ? new Date(task.started_at).toLocaleString() : '-' },
    { label: '结束时间', value: task.finished_at ? new Date(task.finished_at).toLocaleString() : '-' },
    { label: '创建时间', value: new Date(task.created_at).toLocaleString() },
    { label: '更新时间', value: new Date(task.updated_at).toLocaleString() },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>采集任务详情</h2>
        {task.status === 'pending' && (
          <button onClick={handleRun} disabled={running} className="btn">
            {running ? '触发中...' : '执行任务'}
          </button>
        )}
      </div>

      <div className="card">
        <table style={{ fontSize: 13, width: '100%' }}>
          <tbody>
            {fields.map((f) => (
              <tr key={f.label}>
                <td style={{ padding: '6px 16px 6px 0', fontWeight: 600, whiteSpace: 'nowrap', width: 140, verticalAlign: 'top' } as React.CSSProperties}>
                  {f.label}
                </td>
                <td style={{ padding: '6px 0', color: 'var(--color-text-secondary)' } as React.CSSProperties}>
                  {f.value}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
