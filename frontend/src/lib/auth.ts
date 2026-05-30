const STAFF_KEY = 'user_is_staff'

export function isStaff(): boolean {
  return localStorage.getItem(STAFF_KEY) === 'true'
}

export function setStaff(value: boolean): void {
  localStorage.setItem(STAFF_KEY, String(value))
}

export function clearAuth(): void {
  localStorage.removeItem('auth_token')
  localStorage.removeItem(STAFF_KEY)
}
