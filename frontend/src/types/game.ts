// 游戏相关类型定义

export type GameDifficulty = 'easy' | 'classic' | 'hardcore'

export type GamePhase = 'start' | 'investigation' | 'interrogation' | 'deduction' | 'conclusion'

export interface Suspect {
  id: string
  name: string
  age: number
  background: string
  motive: string
  timeline: string
  isGuilty: boolean
}

export interface Clue {
  id: string
  description: string
  clueType: 'physical' | 'testimonial' | 'forensic'
  location?: string
  relatedSuspectIds: string[]
  isRedHerring: boolean
}

export interface Case {
  id: string
  victimName: string
  victimBackground: string
  causeOfDeath: string
  timeOfDeath: string
  location: string
  date: string
  suspects: Suspect[]
  clues: Clue[]
  summary: string
}

export interface GameState {
  gameId: string
  difficulty: GameDifficulty
  phase: GamePhase
  case?: Case
  observations: string[]
  interviewedSuspectIds: string[]
  mistakesMade: number
  maxMistakes: number
  startTime?: string
  timeLimitMinutes?: number
  createdAt: string
  updatedAt: string
}
