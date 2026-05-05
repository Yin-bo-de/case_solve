import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from '@/pages/LoginPage'
import StartPage from '@/pages/StartPage'
import BriefingPage from '@/pages/BriefingPage'
import InvestigationPage from '@/pages/InvestigationPage'
import ScenePage from '@/pages/ScenePage'
import InterrogationPage from '@/pages/InterrogationPage'
import DeductionBoard from '@/pages/DeductionBoard'
import ConclusionPage from '@/pages/ConclusionPage'
import MusicPlayer from '@/components/MusicPlayer'
import { getRedemptionSession } from '@/utils/redemptionSession'

console.debug('[App.tsx] 渲染 App 组件')

/** 路由守卫：检查 localStorage 中存在有效的兑换码会话，否则跳回登录页 */
function RequireRedeem({ children }: { children: React.ReactNode }) {
  const session = getRedemptionSession()
  if (!session?.code) {
    console.info('[RequireRedeem] 无有效兑换码会话，重定向至登录页')
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}

function App() {
  return (
    <div className="app">
      <MusicPlayer />
      <Routes>
        {/* 登录页：新入口 */}
        <Route path="/" element={<LoginPage />} />

        {/* 以下路由均需通过兑换码验证 */}
        <Route path="/start" element={<RequireRedeem><StartPage /></RequireRedeem>} />
        <Route path="/briefing/:gameId" element={<RequireRedeem><BriefingPage /></RequireRedeem>} />
        <Route path="/investigation/:gameId" element={<RequireRedeem><InvestigationPage /></RequireRedeem>} />
        <Route path="/investigation/:gameId/scene/:sceneId" element={<RequireRedeem><ScenePage /></RequireRedeem>} />
        <Route path="/interrogation/:gameId" element={<RequireRedeem><InterrogationPage /></RequireRedeem>} />
        <Route path="/deduction/:gameId" element={<RequireRedeem><DeductionBoard /></RequireRedeem>} />
        <Route path="/conclusion/:gameId" element={<RequireRedeem><ConclusionPage /></RequireRedeem>} />
      </Routes>
    </div>
  )
}

export default App
