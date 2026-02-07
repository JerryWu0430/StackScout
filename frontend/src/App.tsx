import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Analysis from './pages/Analysis'
import Tools from './pages/Tools'
import Schedule from './pages/Schedule'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/analysis/:repo_id" element={<Analysis />} />
        <Route path="/tools" element={<Tools />} />
        <Route path="/schedule/:repo_id/:tool_id" element={<Schedule />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
