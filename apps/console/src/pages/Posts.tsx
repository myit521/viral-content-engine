import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getPosts, manualImportPost, deletePost, getPlatforms, getPostAnalysisResults, autoSummarizeTemplates, type Post, type Platform } from '../api/client'
import { POST_STATUS_LABELS, SOURCE_TYPE_LABELS } from '../api/labels'

export default function Posts() {
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(false)
  const [showImport, setShowImport] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [importTitle, setImportTitle] = useState('')
  const [importContent, setImportContent] = useState('')
  const [importUrl, setImportUrl] = useState('')
  const [platformCode, setPlatformCode] = useState('')
  const [platforms, setPlatforms] = useState<Platform[]>([])
  const [selectedPostIds, setSelectedPostIds] = useState<string[]>([])
  const [summarizing, setSummarizing] = useState(false)

  useEffect(() => { loadPosts(); loadPlatforms() }, [])

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

  async function loadPosts() {
    setLoading(true)
    try {
      const res = await getPosts({ page: 1, page_size: 50, keyword: keyword || undefined })
      setPosts(res.data.items)
    } catch (e) {
      alert('加载样本失败: ' + (e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function handleImport() {
    if (!importContent.trim()) {
      alert('请输入正文内容')
      return
    }
    try {
      await manualImportPost({
        platform_code: 'zhihu',
        title: importTitle || undefined,
        content_text: importContent,
        source_url: importUrl || undefined,
      })
      alert('样本已录入')
      setShowImport(false)
      setImportTitle('')
      setImportContent('')
      setImportUrl('')
      loadPosts()
    } catch (e) {
      alert('录入失败: ' + (e as Error).message)
    }
  }

  async function handleDelete(postId: string) {
    if (!confirm('确定要删除该样本吗？（逻辑删除，可恢复）')) return
    try {
      await deletePost(postId)
      alert('样本已归档')
      loadPosts()
    } catch (e) {
      const msg = (e as Error).message
      if (msg.includes('409')) {
        alert('删除失败：该样本仍被其他流程占用')
      } else {
        alert('删除失败: ' + msg)
      }
    }
  }

  function togglePost(postId: string) {
    setSelectedPostIds(prev =>
      prev.includes(postId) ? prev.filter(id => id !== postId) : [...prev, postId]
    )
  }

  function selectAll() {
    if (selectedPostIds.length === posts.length) {
      setSelectedPostIds([])
    } else {
      setSelectedPostIds(posts.map(p => p.post_id))
    }
  }

  async function handleBatchSummarize() {
    if (selectedPostIds.length === 0) return
    setSummarizing(true)
    try {
      // 获取所选帖子的分析结果ID
      const analysisIds: string[] = []
      for (const postId of selectedPostIds) {
        try {
          const res = await getPostAnalysisResults(postId)
          if (res.data.length > 0) {
            analysisIds.push(res.data[0].id) // 使用最新的分析结果
          }
        } catch (e) {
          console.error(`获取帖子 ${postId} 分析结果失败:`, e)
        }
      }

      if (analysisIds.length === 0) {
        alert('所选样本暂无分析结果，无法归纳模板')
        return
      }

      const res = await autoSummarizeTemplates({
        analysis_ids: analysisIds,
      })
      const count = res.data.items?.length || 0
      alert(`批量归纳完成！已创建 ${count} 个模板，请到模板中心查看`)
      setSelectedPostIds([])
    } catch (e) {
      alert('批量归纳失败: ' + (e as Error).message)
    } finally {
      setSummarizing(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>内容样本</h2>
        <div>
          {selectedPostIds.length > 0 && (
            <button
              onClick={handleBatchSummarize}
              className="btn"
              disabled={summarizing}
              style={{ marginRight: 8 }}
            >
              {summarizing ? '归纳中...' : `批量归纳模板 (${selectedPostIds.length})`}
            </button>
          )}
          <button onClick={() => setShowImport(!showImport)} className="btn">
            {showImport ? '取消' : '手动录入'}
          </button>
          <button onClick={loadPosts} className="btn" style={{ marginLeft: 8 }}>刷新</button>
        </div>
      </div>

      {showImport && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 12 }}>手动录入样本</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <label className="label">平台</label>
              <select value={platformCode} onChange={(e) => setPlatformCode(e.target.value)} className="input">
                <option value="">选择平台</option>
                {platforms.filter(p => p.enabled).map(p => (
                  <option key={p.code} value={p.code}>{p.name}</option>
                ))}
              </select>
            </div>
            <input
              value={importUrl}
              onChange={(e) => setImportUrl(e.target.value)}
              placeholder="来源链接 (可选)"
              className="input"
            />
            <input
              value={importTitle}
              onChange={(e) => setImportTitle(e.target.value)}
              placeholder="标题 (可选)"
              className="input"
            />
            <textarea
              value={importContent}
              onChange={(e) => setImportContent(e.target.value)}
              placeholder="正文内容 *"
              rows={6}
              className="input"
              style={{ resize: 'vertical' } as React.CSSProperties}
            />
            <button onClick={handleImport} className="btn">提交录入</button>
          </div>
        </div>
      )}

      <div style={{ marginBottom: 12 }}>
        <input
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="按关键词筛选"
          className="input"
          style={{ width: 200 } as React.CSSProperties}
          onKeyDown={(e) => e.key === 'Enter' && loadPosts()}
        />
      </div>

      {loading && <p>加载中...</p>}

      <table className="data-table">
        <thead>
          <tr>
            <th style={{ width: 40 }}>
              <input
                type="checkbox"
                checked={posts.length > 0 && selectedPostIds.length === posts.length}
                onChange={selectAll}
              />
            </th>
            <th>ID</th>
            <th>标题</th>
            <th>来源</th>
            <th>状态</th>
            <th>点赞</th>
            <th>收藏</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {posts.length === 0 && (
            <tr><td colSpan={8} style={{ textAlign: 'center', color: 'var(--color-text-secondary)' } as React.CSSProperties}>暂无样本</td></tr>
          )}
          {posts.map((p) => (
            <tr key={p.id}>
              <td>
                <input
                  type="checkbox"
                  checked={selectedPostIds.includes(p.post_id)}
                  onChange={() => togglePost(p.post_id)}
                />
              </td>
              <td>{p.id}</td>
              <td>{p.title || '(无标题)'}</td>
              <td>{SOURCE_TYPE_LABELS[p.source_type] || p.source_type}</td>
              <td>{POST_STATUS_LABELS[p.status] || p.status}</td>
              <td>{p.like_count}</td>
              <td>{p.favorite_count}</td>
              <td>
                <Link to={`/posts/${p.id}`} style={{ color: 'var(--color-primary)', marginRight: 8 }}>查看</Link>
                {p.status !== 'archived' && (
                  <button onClick={() => handleDelete(p.id)} className="btn btn-sm" style={{ color: '#ff4d4f', background: 'transparent', border: 'none', cursor: 'pointer', padding: 0 }}>删除</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
