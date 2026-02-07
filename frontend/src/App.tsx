import { useQuery } from '@tanstack/react-query'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['health'],
    queryFn: () => fetch(`${API_URL}/health`).then(res => res.json()),
  })

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-md text-center">
        <h1 className="text-3xl font-bold text-gray-800 mb-4">StackScout</h1>
        <p className="text-gray-600">
          {isLoading && 'Connecting to API...'}
          {error && 'API not available'}
          {data && `API Status: ${data.status}`}
        </p>
      </div>
    </div>
  )
}

export default App
