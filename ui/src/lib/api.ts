import type { IcebreakerResponse, TurnRequest, TurnResponse } from './types'

const BASE = import.meta.env.VITE_API_URL ?? ''

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  })
  if (!res.ok) {
    let message = `HTTP ${res.status}`
    try {
      const body = (await res.json()) as { error?: string; message?: string }
      message = body.error ?? body.message ?? message
    } catch { /* ignore */ }
    throw new Error(message)
  }
  return res.json() as Promise<T>
}

export function getIcebreaker(): Promise<IcebreakerResponse> {
  return apiFetch('/conversations/icebreakers')
}

export function postTurn(conversationId: string, body: TurnRequest): Promise<TurnResponse> {
  return apiFetch(`/conversations/${conversationId}/turns`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}
