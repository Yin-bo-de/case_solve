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
  personalityTraits: string[]
  secrets: string[]
}

export interface Clue {
  id: string
  description: string
  clueType: 'physical' | 'testimonial' | 'forensic'
  location?: string
  relatedSuspectIds: string[]
  isRedHerring: boolean
  discovered: boolean
  discoveryNotes?: string
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
  murderMethod: string
  trueMurdererId?: string
  investigationLocations: string[]
}

export interface Observation {
  id: string
  description: string
  location: string
  timestamp: string
  relatedClueIds: string[]
  notes?: string
}

export interface Inference {
  id: string
  content: string
  observationIds: string[]
  parentInferenceIds: string[]
  confidence: number
  createdAt: string
  supportingEvidence: string[]
  contradictingEvidence: string[]
}

export interface Hypothesis {
  id: string
  title: string
  description: string
  inferenceIds: string[]
  suspectId?: string
  isVerified: boolean
  verificationNotes?: string
  createdAt: string
  supportScore: number
}

export interface DeductionChain {
  id: string
  observations: Observation[]
  inferences: Inference[]
  hypotheses: Hypothesis[]
  conclusion?: string
  finalAccusation?: string
  createdAt: string
  updatedAt: string
}

export interface GameState {
  gameId: string
  difficulty: GameDifficulty
  phase: GamePhase
  case?: Case
  deductionChain?: DeductionChain
  interviewedSuspectIds: string[]
  mistakesMade: number
  maxMistakes: number
  startTime?: string
  timeLimitMinutes?: number
  createdAt: string
  updatedAt: string
}
