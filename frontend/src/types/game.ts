// 游戏相关类型定义

export type GameDifficulty = 'easy' | 'classic' | 'hardcore'

export type GamePhase = 'start' | 'investigation' | 'interrogation' | 'deduction' | 'conclusion'

// 华生对话消息类型
export type WatsonMessageType =
  | 'guidance'
  | 'clue_discussion'
  | 'suspect_analysis'
  | 'deduction_review'
  | 'knowledge'
  | 'encouragement'
  | 'general'

export interface WatsonChatMessage {
  id: string
  role: 'user' | 'watson'
  content: string
  messageType: WatsonMessageType
  timestamp: string
}

// 快捷提问配置
export interface QuickQuestion {
  label: string
  message: string
  phase: GamePhase[]
}

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

export interface Witness {
  id: string
  name: string
  age: number
  occupation: string
  relationshipToCase: string
  timeline: string
  personalityTraits: string[]
  relatedSuspectIds: string[]
  credibility: number
  // secrets / isLyingForSomeone / bribedBySuspectId 服务端剥离，不下发前端
}

export interface ExpertKeyFinding {
  topic: string
  finding: string
  relatedClueIds: string[]
}

export interface Expert {
  id: string
  name: string
  title: string
  expertise: string[]
  preliminaryReport: string
  keyFindings: ExpertKeyFinding[]
  methodologyNotes: string[]
  relatedClueIds: string[]
}

export type ActorType = 'suspect' | 'witness' | 'expert'

export interface CredibilityCheckResult {
  credibilityConcern: boolean
  concernType?: 'fear' | 'bribery' | 'memory_gap' | null
  confidence: number
  microexpression?: string
  notes?: string
}

export interface SceneObject {
  id: string
  name: string
  description: string
  hiddenClueIds: string[]
  searchHints: string[]
}

export interface Scene {
  id: string
  name: string
  description: string
  atmosphereImage?: string
  npcPersona: string
  objects: SceneObject[]
}

export interface SceneSearchResponse {
  narrative: string
  matchedObjectIds: string[]
  clueCandidates: Array<{
    objectId: string
    suggestedClueId?: string
    hint: string
  }>
  dialogOptions?: string[]
}

export interface ReasoningRecord {
  id: string
  content: string
  clueIds: string[]
  verificationResult?: 'correct' | 'wrong' | 'partial'
  oracleExplanation?: string
  confidence: number
  createdAt: string
  userMarkedImportant: boolean
}

export interface WatsonTip {
  type: 'suggestion' | 'contradiction' | 'question_template'
  text: string
  relatedClueIds: string[]
}

export interface Clue {
  id: string
  description: string
  clueType: 'physical' | 'testimonial' | 'forensic'
  location?: string
  relatedSuspectIds: string[]
  isRedHerring?: boolean
  discovered: boolean
  discoveryNotes?: string
  userLabel?: string
  sourceType?: 'initial' | 'scene' | 'interrogation' | 'witness' | 'expert'
  sourceRef?: string
  quotedText?: string
  userGenerated?: boolean
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
  summary: string
  murderMethod: string
  trueMurdererId?: string
  investigationLocations: string[]
  scenes: Scene[]
  witnesses: Witness[]
  experts: Expert[]
}

/** 后端 DTO：仅用于 API 层和 setGameState 入口，含后端返回的初始 clues */
export interface CaseDto extends Case {
  clues: Clue[]
}

/** 后端 GameState DTO：case 字段含 clues，组件层不直接使用 */
export interface GameStateDto extends Omit<GameState, 'case'> {
  case?: CaseDto
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
  clueIds?: string[]
  verificationResult?: 'correct' | 'wrong' | 'partial'
  oracleExplanation?: string
  userMarkedImportant?: boolean
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

// 结案相关类型
export interface ConclusionReadiness {
  isReady: boolean
  reason: string
  observationsCount: number
  inferencesCount: number
  hypothesesCount: number
  minimumObservations: number
}

export interface AccusedSuspect {
  id: string
  name: string
  background: string
}

export interface TrueMurderer {
  id: string
  name: string
}

export interface AccusationResult {
  isCorrect: boolean
  accusedSuspect: AccusedSuspect
  trueMurderer?: TrueMurderer
  watsonFeedback: string
  mistakesMade: number
  maxMistakes: number
  canContinue: boolean
}

export interface CaseReveal {
  victim: {
    name: string
    background: string
    causeOfDeath: string
    timeOfDeath: string
    location: string
  }
  trueMurderer?: {
    id: string
    name: string
    age: number
    background: string
    motive: string
    secrets: string[]
  }
  murderMethod: string
  caseSummary: string
  allSuspects: Array<{
    id: string
    name: string
    age: number
    background: string
    motive: string
    isGuilty: boolean
  }>
  keyClues: Array<{
    id: string
    description: string
    clueType: string
    isRedHerring: boolean
  }>
}
