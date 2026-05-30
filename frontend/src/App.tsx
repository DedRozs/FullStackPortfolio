import { lazy, Suspense } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout from './components/layout/Layout'
import PortalLayout from './components/layout/PortalLayout'
import DashboardLayout from './components/layout/DashboardLayout'
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
const DashboardOverviewPage = lazy(() => import('./pages/dashboard/DashboardOverviewPage'))
const DashboardMetricsPage = lazy(() => import('./pages/dashboard/DashboardMetricsPage'))
const DashboardAlertsPage = lazy(() => import('./pages/dashboard/DashboardAlertsPage'))

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
                <PortalLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<PortalDashboardPage />} />
            <Route path="projects/:id" element={<PortalProjectDetailPage />} />
            <Route path="files" element={<PortalFilesPage />} />
            <Route path="messages" element={<PortalMessagesPage />} />
          </Route>
          <Route
            path="dashboard"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardOverviewPage />} />
            <Route path="metrics" element={<DashboardMetricsPage />} />
            <Route path="alerts" element={<DashboardAlertsPage />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
