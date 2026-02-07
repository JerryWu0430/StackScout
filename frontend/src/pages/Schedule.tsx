import { useSearchParams } from 'react-router-dom'
import VoiceAgent from '../components/VoiceAgent'

export default function Schedule() {
  const [searchParams] = useSearchParams()
  const repoUrl = searchParams.get('repo')

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Schedule Demo</h1>
        <p className="text-gray-600 mb-6 truncate">{repoUrl}</p>

        <VoiceAgent />
      </div>
    </div>
  )
}
