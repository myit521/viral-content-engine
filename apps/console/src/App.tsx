import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import { ToastProvider } from './components/Toast'
import Dashboard from './pages/Dashboard'
import CollectorTasks from './pages/CollectorTasks'
import TaskDetail from './pages/TaskDetail'
import Posts from './pages/Posts'
import PostDetail from './pages/PostDetail'
import Templates from './pages/Templates'
import TemplateDetail from './pages/TemplateDetail'
import GenerationJobs from './pages/GenerationJobs'
import GeneratedContents from './pages/GeneratedContents'
import ReviewCompare from './pages/ReviewCompare'
import PublishRecords from './pages/PublishRecords'

function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="tasks" element={<CollectorTasks />} />
          <Route path="tasks/:id" element={<TaskDetail />} />
          <Route path="posts" element={<Posts />} />
          <Route path="posts/:id" element={<PostDetail />} />
          <Route path="templates" element={<Templates />} />
          <Route path="templates/:id" element={<TemplateDetail />} />
          <Route path="generation" element={<GenerationJobs />} />
          <Route path="generated-contents" element={<GeneratedContents />} />
          <Route path="generated-contents/:id/review" element={<ReviewCompare />} />
          <Route path="publish" element={<PublishRecords />} />
        </Route>
      </Routes>
    </ToastProvider>
  )
}

export default App
