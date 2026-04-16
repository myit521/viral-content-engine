import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getTemplates, createTemplate, updateTemplateStatus, deleteTemplate, generateTemplate, getAvailableModels, type Template, type ModelOption } from '../api/client'
import { TEMPLATE_STATUS_LABELS, TEMPLATE_CATEGORY_LABELS } from '../api/labels'

export default function Templates() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [showAIGenerate, setShowAIGenerate] = useState(false)
  const [tplName, setTplName] = useState('')
  const [tplCategory, setTplCategory] = useState('narrative_frame')
  const [tplType, setTplType] = useState('script')

  // AI generate form
  const [aiName, setAiName] = useState('')
  const [aiGoal, setAiGoal] = useState('')
  const [aiType, setAiType] = useState('script')
  const [aiCategory, setAiCategory] = useState('narrative_frame')
  const [aiPlatform, setAiPlatform] = useState('zhihu_to_video')
  const [aiTopic, setAiTopic] = useState('history')
  const [aiScene, setAiScene] = useState('')
  const [aiRequirements, setAiRequirements] = useState('')
  const [aiModelName, setAiModelName] = useState('')
  const [aiSubmitting, setAiSubmitting] = useState(false)
  const [aiError, setAiError] = useState('')
  const [aiGenerated, setAiGenerated] = useState<Template | null>(null)

  // Model options
  const [models, setModels] = useState<ModelOption[]>([])
  const [modelsLoading, setModelsLoading] = useState(false)
  const [modelsError, setModelsError] = useState('')

  async function loadTemplates() {
    setLoading(true)
    try {
      const res = await getTemplates({ page: 1, page_size: 50 })
      setTemplates(res.data.items)
    } catch (e) {
      alert('加载模板失败: ' + (e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function loadModels() {
    setModelsLoading(true)
    try {
      const res = await getAvailableModels('template_generation')
      setModels(res.data.options)
      const defaultName = res.data.default_model
      const defaultModel = res.data.options.find((m) => m.model_name === defaultName) || res.data.options.find((m) => m.enabled)
      if (defaultModel) setAiModelName(defaultModel.model_name)
    } catch (e) {
      setModelsError('模型配置接口不可用，已降级为默认选项')
      setModels([
        { model_name: 'gpt-4.1', label: 'GPT-4.1', provider: 'openai', enabled: true, recommended: false, description: '', scene: 'generation', supported_task_types: [] },
        { model_name: 'gpt-4.1-mini', label: 'GPT-4.1 Mini', provider: 'openai', enabled: true, recommended: false, description: '', scene: 'generation', supported_task_types: [] },
      ])
      setAiModelName('gpt-4.1')
    } finally {
      setModelsLoading(false)
    }
  }

  useEffect(() => { loadTemplates() }, [])

  async function handleCreate() {
    if (!tplName.trim()) {
      alert('请输入模板名称')
      return
    }
    try {
      await createTemplate({
        template_type: tplType,
        template_category: tplCategory,
        name: tplName,
        applicable_platform: 'zhihu_to_video',
        applicable_topic: 'history',
        structure_json: { opening: '', body: [], ending: '' },
      })
      alert('模板已创建')
      setShowForm(false)
      setTplName('')
      loadTemplates()
    } catch (e) {
      alert('创建失败: ' + (e as Error).message)
    }
  }

  async function handleAIGenerate() {
    if (!aiName.trim() && !aiGoal.trim()) {
      setAiError('请输入模板名称或生成目标')
      return
    }
    setAiError('')
    setAiSubmitting(true)
    try {
      const res = await generateTemplate({
        name: aiName || undefined,
        generation_goal: aiGoal || undefined,
        template_type: aiType,
        template_category: aiCategory,
        applicable_platform: aiPlatform,
        applicable_topic: aiTopic,
        applicable_scene: aiScene || undefined,
        requirements: aiRequirements || undefined,
        model_name: aiModelName || undefined,
      })
      setAiGenerated(res.data)
      setAiSubmitting(false)
      loadTemplates()
    } catch (e) {
      setAiError('AI 生成失败: ' + (e as Error).message)
      setAiSubmitting(false)
    }
  }

  async function handleToggleStatus(tpl: Template) {
    const newStatus = tpl.status === 'active' ? 'disabled' : 'active'
    try {
      await updateTemplateStatus(tpl.id, { status: newStatus })
      loadTemplates()
    } catch (e) {
      alert('操作失败: ' + (e as Error).message)
    }
  }

  async function handleDelete(tpl: Template) {
    if (!confirm(`确定要删除模板"${tpl.name}"吗？（逻辑删除，可恢复）`)) return
    try {
      await deleteTemplate(tpl.id)
      alert('模板已归档')
      loadTemplates()
    } catch (e) {
      const msg = (e as Error).message
      if (msg.includes('409')) {
        alert('删除失败：该模板正被生成任务引用')
      } else {
        alert('删除失败: ' + msg)
      }
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>模板中心</h2>
        <div>
          <button onClick={() => { setShowAIGenerate(!showAIGenerate); if (!showAIGenerate && models.length === 0) loadModels() }} className="btn" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#fff' }}>
            {showAIGenerate ? '取消' : 'AI 生成模板'}
          </button>
          <button onClick={() => setShowForm(!showForm)} className="btn" style={{ marginLeft: 8 }}>
            {showForm ? '取消' : '新建模板'}
          </button>
          <button onClick={loadTemplates} className="btn" style={{ marginLeft: 8 }}>刷新</button>
        </div>
      </div>

      {/* AI Generate Form */}
      {showAIGenerate && (
        <div className="card" style={{ marginBottom: 16, border: '1px solid #667eea' }}>
          <h3 style={{ marginBottom: 12 }}>AI 生成模板</h3>
          {modelsError && <p style={{ fontSize: 12, color: '#faad14', marginBottom: 8 }}>{modelsError}</p>}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <label className="label">模板名称（可选）</label>
                <input value={aiName} onChange={(e) => setAiName(e.target.value)} className="input" placeholder="如: 历史反转三段式" style={{ width: '100%' }} />
              </div>
              <div style={{ flex: 2 }}>
                <label className="label">生成目标 *</label>
                <input value={aiGoal} onChange={(e) => setAiGoal(e.target.value)} className="input" placeholder="如: 生成一个适合历史类短视频的叙事框架模板" style={{ width: '100%' }} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div>
                <label className="label">类型</label>
                <select value={aiType} onChange={(e) => setAiType(e.target.value)} className="input">
                  <option value="script">脚本</option>
                  <option value="title">标题</option>
                  <option value="storyboard">分镜</option>
                </select>
              </div>
              <div>
                <label className="label">分类</label>
                <select value={aiCategory} onChange={(e) => setAiCategory(e.target.value)} className="input">
                  <option value="narrative_frame">叙事框架</option>
                  <option value="opening_hook">开头钩子</option>
                  <option value="title_hook">标题钩子</option>
                  <option value="ending_cta">结尾引导</option>
                  <option value="full_script">完整脚本</option>
                </select>
              </div>
              <div>
                <label className="label">适用平台</label>
                <select value={aiPlatform} onChange={(e) => setAiPlatform(e.target.value)} className="input">
                  <option value="zhihu_to_video">知乎转视频</option>
                  <option value="zhihu">知乎</option>
                  <option value="bilibili">B 站</option>
                  <option value="xiaohongshu">小红书</option>
                </select>
              </div>
              <div>
                <label className="label">适用主题</label>
                <select value={aiTopic} onChange={(e) => setAiTopic(e.target.value)} className="input">
                  <option value="history">历史</option>
                  <option value="science">科普</option>
                  <option value="emotion">情感</option>
                  <option value="business">商业</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <label className="label">适用场景（可选）</label>
                <input value={aiScene} onChange={(e) => setAiScene(e.target.value)} className="input" placeholder="如: 人物争议" style={{ width: '100%' }} />
              </div>
              <div style={{ flex: 1 }}>
                <label className="label">模型</label>
                {modelsLoading ? (
                  <div className="input" style={{ color: 'var(--color-text-secondary)' }}>加载中...</div>
                ) : (
                  <select value={aiModelName} onChange={(e) => setAiModelName(e.target.value)} className="input">
                    {models.filter((m) => m.enabled).map((m) => (
                      <option key={m.model_name} value={m.model_name}>
                        {m.label}{m.recommended ? ' (推荐)' : ''}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>
            <div>
              <label className="label">需求描述（可选）</label>
              <textarea
                value={aiRequirements}
                onChange={(e) => setAiRequirements(e.target.value)}
                className="input"
                placeholder="补充说明你对模板的期望，AI 会据此生成结构..."
                rows={2}
                style={{ width: '100%', resize: 'vertical' } as React.CSSProperties}
              />
            </div>
            {aiError && <p style={{ color: '#ff4d4f', margin: 0, fontSize: 13 }}>{aiError}</p>}
            {aiGenerated && (
              <div style={{ padding: 12, background: '#f6ffed', borderRadius: 4, border: '1px solid #b7eb8f' }}>
                <p style={{ margin: '0 0 4px', fontWeight: 600, color: '#52c41a' }}>AI 生成成功！</p>
                <p style={{ margin: 0, fontSize: 13 }}>模板: <Link to={`/templates/${aiGenerated.id}`} style={{ color: 'var(--color-primary)' }}>{aiGenerated.name}</Link> | 分类: {TEMPLATE_CATEGORY_LABELS[aiGenerated.template_category] || aiGenerated.template_category}</p>
              </div>
            )}
            <button onClick={handleAIGenerate} disabled={aiSubmitting} className="btn">
              {aiSubmitting ? 'AI 生成中...' : 'AI 生成模板'}
            </button>
          </div>
        </div>
      )}

      {/* Manual Create Form */}
      {showForm && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
            <div>
              <label className="label">模板名称</label>
              <input value={tplName} onChange={(e) => setTplName(e.target.value)} className="input" placeholder="如: 历史反转三段式" />
            </div>
            <div>
              <label className="label">类型</label>
              <select value={tplType} onChange={(e) => setTplType(e.target.value)} className="input">
                <option value="script">脚本</option>
                <option value="title">标题</option>
                <option value="storyboard">分镜</option>
              </select>
            </div>
            <div>
              <label className="label">分类</label>
              <select value={tplCategory} onChange={(e) => setTplCategory(e.target.value)} className="input">
                <option value="narrative_frame">叙事框架</option>
                <option value="opening_hook">开头钩子</option>
                <option value="title_hook">标题钩子</option>
                <option value="ending_cta">结尾引导</option>
                <option value="full_script">完整脚本</option>
              </select>
            </div>
            <button onClick={handleCreate} className="btn">创建</button>
          </div>
        </div>
      )}

      {loading && <p>加载中...</p>}

      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>分类</th>
            <th>适用场景</th>
            <th>状态</th>
            <th>来源样本数</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {templates.length === 0 && !loading && (
            <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--color-text-secondary)' } as React.CSSProperties}>暂无模板</td></tr>
          )}
          {templates.map((t) => (
            <tr key={t.id}>
              <td>{t.id}</td>
              <td>
                <Link to={`/templates/${t.id}`} style={{ color: 'var(--color-primary)' }}>{t.name}</Link>
              </td>
              <td>{TEMPLATE_CATEGORY_LABELS[t.template_category] || t.template_category}</td>
              <td>{t.applicable_scene || '-'}</td>
              <td>
                <span style={{
                  display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 12, color: '#fff',
                  background: t.status === 'active' ? 'var(--color-success)' : t.status === 'draft' ? '#faad14' : '#8c8c8c',
                } as React.CSSProperties}>
                  {TEMPLATE_STATUS_LABELS[t.status] || t.status}
                </span>
              </td>
              <td>{t.source_post_ids?.length || 0}</td>
              <td>
                <button onClick={() => handleToggleStatus(t)} className="btn btn-sm" style={{ marginRight: 8 }}>
                  {t.status === 'active' ? '停用' : '启用'}
                </button>
                {t.status !== 'archived' && (
                  <button onClick={() => handleDelete(t)} className="btn btn-sm" style={{ color: '#ff4d4f', background: 'transparent', border: '1px solid #ff4d4f' }}>删除</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
