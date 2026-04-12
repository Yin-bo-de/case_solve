import { Routes, Route } from 'react-router-dom'
import StartPage from '@/pages/StartPage'
import InvestigationPage from '@/pages/InvestigationPage'
import InterrogationPage from '@/pages/InterrogationPage'
import DeductionBoard from '@/pages/DeductionBoard'
import ConclusionPage from '@/pages/ConclusionPage'

console.debug('[App.tsx] 渲染 App 组件')

function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<StartPage />} />
        <Route path="/investigation/:gameId" element={<InvestigationPage />} />
        <Route path="/interrogation/:gameId" element={<InterrogationPage />} />
        <Route path="/deduction/:gameId" element={<DeductionBoard />} />
        <Route path="/conclusion/:gameId" element={<ConclusionPage />} />
      </Routes>
    </div>
  )
}

export default App
