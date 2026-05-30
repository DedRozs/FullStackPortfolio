import { lazy, Suspense } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout from './components/layout/Layout'
import ProtectedRoute from './components/ProtectedRoute'

const AIAssistantPage = lazy(() => import('./pages/AIAssistantPage'))
const AboutPage = lazy(() => import('./pages/AboutPage'))
const BlogPage = lazy(() => import('./pages/BlogPage'))
const BlogPostPage = lazy(() => import('./pages/BlogPostPage'))
const ContactPage = lazy(() => import('./pages/ContactPage'))
const HomePage = lazy(() => import('./pages/HomePage'))
const ProjectsPage = lazy(() => import('./pages/ProjectsPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const PortalDashboardPage = lazy(() => import('./pages/portal/PortalDashboardPage'))
const PortalProjectDetailPage = lazy(() => import('./pages/portal/PortalProjectDetailPage'))
const PortalFilesPage = lazy(() => import('./pages/portal/PortalFilesPage'))
const PortalMessagesPage = lazy(() => import('./pages/portal/PortalMessagesPage'))

export default function App() {
  return (
    <BrowserRouter>
      <Suspense>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="blog" element={<BlogPage />} />
            <Route path="blog/:slug" element={<BlogPostPage />} />
            <Route path="ai" element={<AIAssistantPage />} />
            <Route path="about" element={<AboutPage />} />
            <Route path="contact" element={<ContactPage />} />
          </Route>
          <Route path="portal/login" element={<LoginPage />} />
          <Route
            path="portal"
            element={
              <ProtectedRoute>
                <PortalDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="portal/projects/:id"
            element={
              <ProtectedRoute>
                <PortalProjectDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="portal/files"
            element={
              <ProtectedRoute>
                <PortalFilesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="portal/messages"
            element={
              <ProtectedRoute>
                <PortalMessagesPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
