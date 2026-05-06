import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useGameStore } from '@/store'
import { gameApi } from '@/services/api'
import type { Case, Suspect, Witness, Expert } from '@/types/game'
import Typewriter from '@/components/Typewriter'
import './BriefingPage.css'

// ─── Slide: 案件概要 ──────────────────────────────────────────────────────────

interface SummarySlideProps {
  caseData: Case
  onTypingDone: () => void
}

function SummarySlide({ caseData, onTypingDone }: SummarySlideProps) {
  return (
    <div className="briefing-slide briefing-slide--summary">
      <div className="briefing-slide__header">
        <h2 className="briefing-slide__title">案件概要</h2>
        <p className="briefing-slide__subtitle">
          案件 #{caseData.id.slice(0, 8).toUpperCase()} · {caseData.date}
        </p>
      </div>
      <div className="briefing-summary__body">
        <Typewriter
          text={caseData.summary}
          speed={30}
          onDone={onTypingDone}
          className="briefing-summary__text"
        />
      </div>
    </div>
  )
}

// ─── Slide: 法医鉴定 ──────────────────────────────────────────────────────────

interface ForensicSlideProps {
  caseData: Case
}

function ForensicSlide({ caseData }: ForensicSlideProps) {
  const expert: Expert | undefined = caseData.experts?.[0]
  return (
    <div className="briefing-slide briefing-slide--forensic">
      <div className="briefing-slide__header">
        <h2 className="briefing-slide__title">皇家法医：死亡鉴定</h2>
        {expert && (
          <p className="briefing-slide__subtitle">
            {expert.name} · {expert.title}
          </p>
        )}
      </div>

      <div className="briefing-forensic__cards">
        <div className="briefing-forensic__card">
          <span className="briefing-forensic__card-label">罹难者</span>
          <span className="briefing-forensic__card-value">{caseData.victimName}</span>
        </div>
        <div className="briefing-forensic__card">
          <span className="briefing-forensic__card-label">预估死亡时间</span>
          <span className="briefing-forensic__card-value">{caseData.timeOfDeath}</span>
        </div>
        <div className="briefing-forensic__card">
          <span className="briefing-forensic__card-label">死亡原因</span>
          <span className="briefing-forensic__card-value">{caseData.causeOfDeath}</span>
        </div>
      </div>

      {expert?.preliminaryReport && (
        <div className="briefing-forensic__report">
          <h3 className="briefing-forensic__report-title">初步报告</h3>
          <p className="briefing-forensic__report-body">{expert.preliminaryReport}</p>
        </div>
      )}
    </div>
  )
}

// ─── Slide: 嫌疑人列表 ────────────────────────────────────────────────────────

interface SuspectsSlideProps {
  suspects: Suspect[]
}

function SuspectsSlide({ suspects }: SuspectsSlideProps) {
  return (
    <div className="briefing-slide briefing-slide--suspects">
      <div className="briefing-slide__header">
        <h2 className="briefing-slide__title">嫌疑人介绍</h2>
        <p className="briefing-slide__subtitle">共 {suspects.length} 名</p>
      </div>
      <div className="briefing-suspects__list">
        {suspects.map((suspect) => (
          <div key={suspect.id} className="briefing-suspects__card">
            <div className="briefing-suspects__card-header">
              <span className="briefing-suspects__name">{suspect.name}</span>
              <span className="briefing-suspects__age">{suspect.age} 岁</span>
              <span className="briefing-suspects__relation">
                {suspect.relationshipToVictim || '—'}
              </span>
            </div>
            <p className="briefing-suspects__background">{suspect.background}</p>
            {suspect.timeline ? (
              <div className="briefing-suspects__timeline">
                <div className="briefing-suspects__timeline-bar" />
                <p className="briefing-suspects__timeline-text">{suspect.timeline}</p>
              </div>
            ) : (
              <p className="briefing-suspects__no-timeline">（暂无时间线记录）</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Slide: 证人与时间线 ──────────────────────────────────────────────────────

interface WitnessesSlideProps {
  witnesses: Witness[]
}

function WitnessesSlide({ witnesses }: WitnessesSlideProps) {
  if (!witnesses || witnesses.length === 0) {
    return (
      <div className="briefing-slide briefing-slide--witnesses">
        <div className="briefing-slide__header">
          <h2 className="briefing-slide__title">证人与时间线</h2>
        </div>
        <p className="briefing-witnesses__empty">
          本案无证人记录，将直接进入案发现场。
        </p>
      </div>
    )
  }

  return (
    <div className="briefing-slide briefing-slide--witnesses">
      <div className="briefing-slide__header">
        <h2 className="briefing-slide__title">证人与时间线</h2>
        <p className="briefing-slide__subtitle">共 {witnesses.length} 名证人</p>
      </div>
      <div className="briefing-witnesses__list">
        {witnesses.map((witness) => (
          <div key={witness.id} className="briefing-witnesses__card">
            <div className="briefing-witnesses__card-header">
              <span className="briefing-witnesses__name">{witness.name}</span>
              <span className="briefing-witnesses__age">{witness.age} 岁</span>
              <span className="briefing-witnesses__occupation">{witness.occupation}</span>
            </div>
            <p className="briefing-witnesses__relation">{witness.relationshipToCase}</p>
            <div className="briefing-witnesses__timeline">
              <div className="briefing-witnesses__timeline-bar" />
              <p className="briefing-witnesses__timeline-text">{witness.timeline}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Step Indicator ───────────────────────────────────────────────────────────

const STEP_LABELS = ['案件概要', '法医鉴定', '嫌疑人', '证人时间线']

interface StepIndicatorProps {
  current: number
  total: number
}

function StepIndicator({ current, total }: StepIndicatorProps) {
  return (
    <div className="briefing-step-indicator">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={`briefing-step-indicator__dot ${i === current ? 'briefing-step-indicator__dot--active' : i < current ? 'briefing-step-indicator__dot--done' : ''}`}
        />
      ))}
      <span className="briefing-step-indicator__label">{STEP_LABELS[current]}</span>
    </div>
  )
}

// ─── BriefingPage ─────────────────────────────────────────────────────────────

const TOTAL_STEPS = 4

export default function BriefingPage() {
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()
  const { gameState, setGameState, setPhase } = useGameStore()
  const caseData = gameState?.case ?? null

  const [step, setStep] = useState(0)
  const [summaryDone, setSummaryDone] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)

  // 进入页面时设置 briefing 阶段
  useEffect(() => {
    console.info('[BriefingPage] mount', { gameId, hasCase: !!caseData })
    setPhase('briefing')
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // store 无 case 时拉取（直链/刷新场景）
  useEffect(() => {
    if (!caseData && gameId) {
      console.info('[BriefingPage] store 无案件，拉取游戏状态', { gameId })
      gameApi.getGameState(gameId)
        .then((dto) => setGameState(dto))
        .catch(() => {
          console.error('[BriefingPage] 拉取游戏状态失败，跳回开始页')
          setLoadError('无法加载案件数据，请重新开始。')
          setTimeout(() => navigate('/start'), 2000)
        })
    }
  }, [caseData, gameId, navigate, setGameState])

  useEffect(() => {
    console.info('[BriefingPage] step', step)
  }, [step])

  const handleNext = () => {
    if (step < TOTAL_STEPS - 1) {
      console.info('[BriefingPage] step → next', { from: step, to: step + 1 })
      setStep((s) => s + 1)
    } else {
      console.info('[BriefingPage] 进入案发现场', { gameId })
      setPhase('investigation')
      navigate(`/investigation/${gameId}`)
    }
  }

  const handlePrev = () => {
    if (step > 0) setStep((s) => s - 1)
  }

  const canProceed = step !== 0 || summaryDone

  if (loadError) {
    return (
      <div className="briefing-page briefing-page--loading">
        <p className="briefing-loading__text">{loadError}</p>
      </div>
    )
  }

  if (!caseData) {
    return (
      <div className="briefing-page briefing-page--loading">
        <p className="briefing-loading__text">档案调取中…</p>
      </div>
    )
  }

  return (
    <div className="briefing-page">
      {/* 壁灯装饰 */}
      <div className="gaslight-wall-lamp gaslight-wall-lamp--left" />
      <div className="gaslight-wall-lamp gaslight-wall-lamp--right" />

      <div className="briefing-page__inner">
        <StepIndicator current={step} total={TOTAL_STEPS} />

        <div className="briefing-page__slide">
          {step === 0 && (
            <SummarySlide
              caseData={caseData}
              onTypingDone={() => setSummaryDone(true)}
            />
          )}
          {step === 1 && <ForensicSlide caseData={caseData} />}
          {step === 2 && <SuspectsSlide suspects={caseData.suspects} />}
          {step === 3 && <WitnessesSlide witnesses={caseData.witnesses} />}
        </div>

        <div className="briefing-page__footer">
          <button
            className="briefing-btn briefing-btn--secondary"
            onClick={handlePrev}
            disabled={step === 0}
            type="button"
          >
            上一步
          </button>
          <button
            className={`briefing-btn briefing-btn--primary ${!canProceed ? 'briefing-btn--pulse' : ''}`}
            onClick={handleNext}
            type="button"
          >
            {step === TOTAL_STEPS - 1 ? '进入案发现场' : '下一步'}
          </button>
        </div>
      </div>
    </div>
  )
}
