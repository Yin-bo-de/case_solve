import { Routes, Route } from 'react-router-dom'
import StartPage from '@/pages/StartPage'
import InvestigationPage from '@/pages/InvestigationPage'
import InterrogationPage from '@/pages/InterrogationPage'
import DeductionBoard from '@/pages/DeductionBoard'

console.debug('[App.tsx] 渲染 App 组件')

function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<StartPage />} />
        <Route path="/investigation/:gameId" element={<InvestigationPage />} />
        <Route path="/interrogation/:gameId" element={<InterrogationPage />} />
        <Route path="/deduction/:gameId" element={<DeductionBoard />} />
      </Routes>
    </div>
  )
}

export default App
