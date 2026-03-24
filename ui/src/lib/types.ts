export interface IcebreakerResponse {
  id: string
  text: string
}

export type Speaker = 'visitor' | 'consultant1' | 'consultant2'

export interface TurnRequest {
  order: number
  text: string
  speaker: Speaker
}

export interface Turn {
  conversationId: string
  order: number
  text: string
  speaker: Speaker
  createdAt: string
}

export interface ConsultantReply {
  order: number
  text: string
  speaker: 'consultant1' | 'consultant2'
}

export interface TurnResponse {
  turn: Turn
  consultantReplies?: ConsultantReply[]
}

// UI-only chat message
export interface ChatMessage {
  id: string
  speaker: Speaker
  text: string
}
