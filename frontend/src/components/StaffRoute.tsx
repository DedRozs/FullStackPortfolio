import { Navigate, useLocation } from 'react-router-dom'
import { isStaff } from '../lib/auth'

const TOAST_KEY = 'pending_toast'

interface StaffRouteProps {
  children: React.ReactNode
}

export default function StaffRoute({ children }: StaffRouteProps) {
  const token = localStorage.getItem('auth_token')
  const location = useLocation()

  if (!token) {
    return <Navigate to="/portal/login" state={{ from: location.pathname }} replace />
  }

  if (!isStaff()) {
    sessionStorage.setItem(
      TOAST_KEY,
      JSON.stringify({
        title: 'Access restricted',
        message: 'That area is for staff only. You have been redirected to your portal.',
        variant: 'warning',
      }),
    )
    return <Navigate to="/portal" replace />
  }

  return <>{children}</>
}

export { TOAST_KEY }
