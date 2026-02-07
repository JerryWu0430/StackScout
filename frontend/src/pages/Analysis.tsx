import { useSearchParams, Link } from 'react-router-dom'
import StackCard from '../components/StackCard'

export default function Analysis() {
  const [searchParams] = useSearchParams()
  const repoUrl = searchParams.get('repo')

  // Placeholder data - will be replaced with API call
  const stacks = [
    { name: 'React', version: '18.2.0', category: 'Frontend' },
    { name: 'TypeScript', version: '5.0.0', category: 'Language' },
    { name: 'Tailwind CSS', version: '3.3.0', category: 'Styling' },
  ]

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Stack Fingerprint</h1>
        <p className="text-gray-600 mb-6 truncate">{repoUrl}</p>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {stacks.map((stack) => (
            <StackCard key={stack.name} {...stack} />
          ))}
        </div>

        <Link
          to={`/tools?repo=${encodeURIComponent(repoUrl || '')}`}
          className="inline-block mt-8 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          View Recommendations
        </Link>
      </div>
    </div>
  )
}
