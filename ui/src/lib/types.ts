export interface IcebreakerResponse {
  id: string
  text: string
}

export interface TurnRequest {
  order: number
  text: string
  speaker: 'ai' | 'user'
}

export interface Turn {
  conversationId: string
  order: number
  text: string
  speaker: 'ai' | 'user'
  createdAt: string
}

export interface AiReply {
  order: number
  text: string
}

export interface TurnResponse {
  turn: Turn
  aiReply?: AiReply
}
