/**
 * Read the CSRF token from the csrftoken cookie Django sets on every page load.
 * Required for POST/PUT/PATCH/DELETE requests when a Django session is active.
 */
export function getCsrfToken(): string {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}
