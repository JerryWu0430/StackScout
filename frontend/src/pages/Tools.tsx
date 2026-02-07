import { useSearchParams, Link } from 'react-router-dom'
import ToolCard from '../components/ToolCard'

export default function Tools() {
  const [searchParams] = useSearchParams()
  const repoUrl = searchParams.get('repo')

  // Placeholder data - will be replaced with API call
  const tools = [
    { name: 'ESLint', description: 'Linting for JavaScript/TypeScript', category: 'Code Quality' },
    { name: 'Prettier', description: 'Code formatting', category: 'Code Quality' },
    { name: 'Jest', description: 'Testing framework', category: 'Testing' },
  ]

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Recommended Tools</h1>
        <p className="text-gray-600 mb-6 truncate">{repoUrl}</p>

        <div className="space-y-4">
          {tools.map((tool) => (
            <ToolCard key={tool.name} {...tool} />
          ))}
        </div>

        <Link
          to={`/schedule?repo=${encodeURIComponent(repoUrl || '')}`}
          className="inline-block mt-8 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          Schedule Demo Call
        </Link>
      </div>
    </div>
  )
}
