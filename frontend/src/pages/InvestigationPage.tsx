import { useParams } from 'react-router-dom'

export default function InvestigationPage() {
  const { gameId } = useParams<{ gameId: string }>()

  console.debug('[InvestigationPage] 渲染勘查页面', { gameId })

  return (
    <div className="investigation-page">
      <h1>现场勘查</h1>
      <p>游戏 ID: {gameId}</p>
      <p>勘查页面将在后续迭代中实现</p>
    </div>
  )
}
