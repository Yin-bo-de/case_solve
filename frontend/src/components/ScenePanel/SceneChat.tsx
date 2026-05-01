import { useState, useRef, useEffect } from 'react'
import { gameApi } from '@/services/api'
import { useCluesStore, useSceneChatStore } from '@/store'
import type { SceneChatMessage } from '@/store'
import type { SceneSearchResponse } from '@/types/game'
import AddClueModal from './AddClueModal'
import Toast from '@/components/Toast'
import { SelectableMessage } from '@/components/SelectableMessage'
import ExtractClueModal from '@/components/ExtractClueModal'

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
  const { addMessage, getMessages } = useSceneChatStore()
  const messages = getMessages(sceneId)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [pendingClue, setPendingClue] = useState<PendingClue | null>(null)
  const [pendingExtractText, setPendingExtractText] = useState<string | null>(null)
  const [showToast, setShowToast] = useState(false)
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
    const userMsg: SceneChatMessage = { role: 'user', content: query }
    addMessage(sceneId, userMsg)
    setInput('')
    setIsLoading(true)

    try {
      const history = messages
        .filter((m) => m.content)
        .map((m) => ({
          role: m.role === 'user' ? 'user' : 'assistant',
          content: m.content,
        }))
      const result = await gameApi.sceneSearch(gameId, sceneId, query, history)
      console.info('[SceneChat] 收到场景回应', { candidates: result.clueCandidates.length })

      const npcMsg: SceneChatMessage = {
        role: 'npc',
        content: result.narrative,
        candidates: result.clueCandidates.length > 0 ? result.clueCandidates : undefined,
      }
      addMessage(sceneId, npcMsg)
    } catch (err) {
      console.error('[SceneChat] 场景搜查失败', err)
      addMessage(sceneId, { role: 'npc', content: '（场景陷入寂静，没有回应……）' })
    } finally {
      setIsLoading(false)
    }
  }

  const handleExtractConfirm = async (userLabel: string) => {
    if (!pendingExtractText) return
    console.info('[SceneChat] 从聊天记录提取线索', { userLabel, sceneId })
    try {
      const clue = await gameApi.addClue(gameId, {
        userLabel,
        description: pendingExtractText,
        sourceType: 'scene',
        sourceRef: sceneId,
      })
      addClueFromBackend(clue)
      setShowToast(true)
      console.info('[SceneChat] 线索提取成功', { clueId: clue.id })
    } catch (err) {
      console.error('[SceneChat] 提取线索失败', err)
    } finally {
      setPendingExtractText(null)
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
      setShowToast(true)
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
            {msg.role === 'npc' ? (
              <SelectableMessage
                text={msg.content}
                onExtract={(text) => setPendingExtractText(text)}
              />
            ) : (
              <p>{msg.content}</p>
            )}
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
      {pendingExtractText && (
        <ExtractClueModal
          quotedText={pendingExtractText}
          onConfirm={handleExtractConfirm}
          onClose={() => setPendingExtractText(null)}
        />
      )}
      {showToast && (
        <Toast message="线索已成功添加！" onDismiss={() => setShowToast(false)} />
      )}
    </div>
  )
}
