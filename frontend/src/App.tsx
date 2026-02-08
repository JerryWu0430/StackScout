import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import AnalysisPage from './pages/AnalysisPage'
import BookingForm from './pages/BookingForm'
import CallStatus from './pages/CallStatus'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Main routes */}
        <Route path="/" element={<Home />} />
        <Route path="/analysis/:repo_id" element={<AnalysisPage />} />

        {/* CallPilot routes */}
        <Route path="/book" element={<BookingForm />} />
        <Route path="/calling/:requestId" element={<CallStatus />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
