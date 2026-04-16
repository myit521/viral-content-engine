import { Outlet, Link, useLocation } from 'react-router-dom'

const navItems = [
  { path: '/', label: '概览' },
  { path: '/tasks', label: '采集任务' },
  { path: '/posts', label: '内容样本' },
  { path: '/templates', label: '模板中心' },
  { path: '/generation', label: '内容生成' },
  { path: '/generated-contents', label: '生成结果' },
  { path: '/publish', label: '发布回填' },
]

export default function Layout() {
  const location = useLocation()

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <aside
        style={{
          width: 220,
          background: '#001529',
          color: '#fff',
          padding: '16px 0',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            padding: '0 24px 24px',
            fontSize: 16,
            fontWeight: 600,
            borderBottom: '1px solid rgba(255,255,255,0.1)',
            marginBottom: 8,
          }}
        >
          VCE Console
        </div>
        <nav>
          {navItems.map((item) => {
            const isActive =
              item.path === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.path)
            return (
              <Link
                key={item.path}
                to={item.path}
                style={{
                  display: 'block',
                  padding: '10px 24px',
                  color: isActive ? '#fff' : 'rgba(255,255,255,0.65)',
                  background: isActive ? 'var(--color-primary)' : 'transparent',
                  textDecoration: 'none',
                  transition: 'all 0.2s',
                }}
              >
                {item.label}
              </Link>
            )
          })}
        </nav>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <header
          style={{
            height: 48,
            background: '#fff',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            padding: '0 24px',
            fontSize: 16,
            fontWeight: 500,
          }}
        >
          {navItems.find((n) =>
            n.path === '/'
              ? location.pathname === '/'
              : location.pathname.startsWith(n.path)
          )?.label || 'Viral Content Engine'}
        </header>
        <div style={{ flex: 1, padding: 24, overflow: 'auto' }}>
          <Outlet />
        </div>
      </main>
    </div>
  )
}
