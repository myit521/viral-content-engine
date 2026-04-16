import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getTemplate, type Template } from '../api/client'
import { TEMPLATE_STATUS_LABELS, TEMPLATE_CATEGORY_LABELS } from '../api/labels'

export default function TemplateDetail() {
  const { id } = useParams<{ id: string }>()
  const [template, setTemplate] = useState<Template | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    getTemplate(id)
      .then((res) => setTemplate(res.data))
      .catch((e) => alert('加载失败: ' + e.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <p>加载中...</p>
  if (!template) return <p>模板不存在</p>

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>模板详情: {template.name}</h2>
      <div className="card">
        <table style={{ fontSize: 13 }}>
          <tbody>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>类型</td><td>{template.template_type}</td></tr>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>分类</td><td>{TEMPLATE_CATEGORY_LABELS[template.template_category] || template.template_category}</td></tr>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>适用平台</td><td>{template.applicable_platform}</td></tr>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>适用主题</td><td>{template.applicable_topic}</td></tr>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>适用场景</td><td>{template.applicable_scene || '-'}</td></tr>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>质量评分</td><td>-</td></tr>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>来源样本数</td><td>{template.source_post_ids?.length || 0}</td></tr>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>状态</td><td>{TEMPLATE_STATUS_LABELS[template.status] || template.status}</td></tr>
            <tr><td style={{ padding: '4px 16px 4px 0', fontWeight: 600, whiteSpace: 'nowrap' } as React.CSSProperties}>版本</td><td>-</td></tr>
          </tbody>
        </table>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3 style={{ marginBottom: 8 }}>结构定义</h3>
        <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4, fontSize: 12, overflow: 'auto' }}>
          {JSON.stringify(template.structure_json, null, 2)}
        </pre>
      </div>
    </div>
  )
}
