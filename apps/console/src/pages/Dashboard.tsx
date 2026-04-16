import { Link } from 'react-router-dom'

const stats = [
  { label: '采集任务', path: '/tasks', desc: '查看和管理采集任务状态' },
  { label: '内容样本', path: '/posts', desc: '浏览已采集或录入的样本' },
  { label: '模板中心', path: '/templates', desc: '管理结构模板与评分' },
  { label: '内容生成', path: '/generation', desc: '基于模板生成新脚本' },
  { label: '生成结果', path: '/generated-contents', desc: '查看和审核生成结果' },
  { label: '发布回填', path: '/publish', desc: '记录发布和效果数据' },
]

export default function Dashboard() {
  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>Viral Content Engine</h2>
      <p style={{ color: 'var(--color-text-secondary)', marginBottom: 24 }}>
        爆款内容研究与脚本生成系统 — 当前阶段：知乎单平台 MVP
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {stats.map((s) => (
          <Link
            key={s.path}
            to={s.path}
            style={{
              display: 'block',
              padding: 20,
              background: '#fff',
              borderRadius: 'var(--radius)',
              border: '1px solid var(--color-border)',
              textDecoration: 'none',
              color: 'inherit',
              transition: 'box-shadow 0.2s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.boxShadow = 'var(--shadow)')}
            onMouseLeave={(e) => (e.currentTarget.style.boxShadow = 'none')}
          >
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>{s.label}</h3>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{s.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
