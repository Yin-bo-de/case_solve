import { useState, useRef, useEffect } from 'react'
import { gameApi } from '@/services/api'
import { useCluesStore } from '@/store'
import type { SceneSearchResponse } from '@/types/game'
import AddClueModal from './AddClueModal'

interface ChatMessage {
  role: 'user' | 'npc'
  content: string
  candidates?: SceneSearchResponse['clueCandidates']
}

interface PendingClue {
  suggestedClueId?: string
  description: string
  sceneId: string
}

interface Props {
  gameId: string
  sceneId: string
}

export default function SceneChat({ gameId, sceneId }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [pendingClue, setPendingClue] = useState<PendingClue | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { addClueFromBackend } = useCluesStore()

  console.debug('[SceneChat] 渲染', { gameId, sceneId })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const query = input.trim()
    if (!query || isLoading) return

    console.info('[SceneChat] 发送搜查请求', { sceneId, query })
    const userMsg: ChatMessage = { role: 'user', content: query }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    try {
      const history = messages.map((m) => ({
        role: m.role === 'user' ? 'user' : 'assistant',
        content: m.content,
      }))
      const result = await gameApi.sceneSearch(gameId, sceneId, query, history)
      console.info('[SceneChat] 收到场景回应', { candidates: result.clueCandidates.length })

      const npcMsg: ChatMessage = {
        role: 'npc',
        content: result.narrative,
        candidates: result.clueCandidates.length > 0 ? result.clueCandidates : undefined,
      }
      setMessages((prev) => [...prev, npcMsg])
    } catch (err) {
      console.error('[SceneChat] 场景搜查失败', err)
      setMessages((prev) => [
        ...prev,
        { role: 'npc', content: '（场景陷入寂静，没有回应……）' },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const openAddClueModal = (candidate: SceneSearchResponse['clueCandidates'][number]) => {
    setPendingClue({
      suggestedClueId: candidate.suggestedClueId,
      description: candidate.hint,
      sceneId,
    })
  }

  const handleConfirmAddClue = async (userLabel: string) => {
    if (!pendingClue) return
    console.info('[SceneChat] 添加线索', { userLabel, pendingClue })

    try {
      const clue = await gameApi.addClue(gameId, {
        userLabel,
        description: pendingClue.description,
        sourceType: 'scene',
        sourceRef: sceneId,
        baseClueId: pendingClue.suggestedClueId,
      })
      addClueFromBackend(clue)
      console.info('[SceneChat] 线索添加成功', { clueId: clue.id })
    } catch (err) {
      console.error('[SceneChat] 添加线索失败', err)
    } finally {
      setPendingClue(null)
    }
  }

  return (
    <div className="scene-chat">
      <div className="scene-chat__messages">
        {messages.length === 0 && (
          <p className="scene-chat__empty">向此处的人询问，或描述你的搜查行动……</p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`scene-chat__message scene-chat__message--${msg.role}`}>
            <p>{msg.content}</p>
            {msg.candidates && msg.candidates.length > 0 && (
              <div className="scene-chat__candidates">
                {msg.candidates.map((c, ci) => (
                  <button
                    key={ci}
                    className="scene-chat__add-clue-btn"
                    onClick={() => openAddClueModal(c)}
                    type="button"
                  >
                    📎 添加为线索：{c.hint.substring(0, 30)}…
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="scene-chat__message scene-chat__message--npc scene-chat__message--loading">
            <span>……</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="scene-chat__input-area">
        <textarea
          className="scene-chat__input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="例如：仔细查看办公桌"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          rows={2}
        />
        <button
          className="scene-chat__send-btn action-button"
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          type="button"
        >
          探查
        </button>
      </div>

      {pendingClue && (
        <AddClueModal
          defaultDescription={pendingClue.description}
          onConfirm={handleConfirmAddClue}
          onClose={() => setPendingClue(null)}
        />
      )}
    </div>
  )
}
