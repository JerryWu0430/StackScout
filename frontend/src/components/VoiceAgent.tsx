import { useState } from 'react'

export default function VoiceAgent() {
  const [isActive, setIsActive] = useState(false)

  return (
    <div className="bg-white p-6 rounded-lg shadow-md text-center">
      <div className={`w-24 h-24 mx-auto mb-4 rounded-full flex items-center justify-center ${isActive ? 'bg-red-100' : 'bg-gray-100'}`}>
        <svg className={`w-12 h-12 ${isActive ? 'text-red-500' : 'text-gray-400'}`} fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
        </svg>
      </div>

      <h3 className="text-lg font-semibold text-gray-800 mb-2">
        {isActive ? 'Listening...' : 'Voice Agent Ready'}
      </h3>
      <p className="text-gray-600 text-sm mb-4">
        Talk to our AI to schedule a demo call
      </p>

      <button
        onClick={() => setIsActive(!isActive)}
        className={`px-6 py-2 rounded-lg transition ${
          isActive
            ? 'bg-red-500 text-white hover:bg-red-600'
            : 'bg-blue-600 text-white hover:bg-blue-700'
        }`}
      >
        {isActive ? 'Stop' : 'Start Conversation'}
      </button>
    </div>
  )
}
