import { Routes, Route } from 'react-router-dom'

console.debug('[App.tsx] 渲染 App 组件')

function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<div>贝克街221B - 起始页面</div>} />
      </Routes>
    </div>
  )
}

export default App
