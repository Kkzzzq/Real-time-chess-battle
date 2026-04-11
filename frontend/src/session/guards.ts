import { bootstrapSession } from './bootstrap'

export function requiresSession(pathname: string): boolean {
  return pathname.startsWith('/room/') || pathname.startsWith('/game/')
}

export function shouldRedirectToLobby(pathname: string): boolean {
  if (!requiresSession(pathname)) return false
  const result = bootstrapSession(pathname)
  return !result.ok
}
