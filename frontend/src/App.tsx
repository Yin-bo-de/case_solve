import { Routes, Route } from 'react-router-dom'
import StartPage from '@/pages/StartPage'
import InvestigationPage from '@/pages/InvestigationPage'

console.debug('[App.tsx] 渲染 App 组件')

function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<StartPage />} />
        <Route path="/investigation/:gameId" element={<InvestigationPage />} />
      </Routes>
    </div>
  )
}

export default App
