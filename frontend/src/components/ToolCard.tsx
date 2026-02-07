import { Link } from 'react-router-dom'

interface Tool {
  id: number
  name: string
  category: string
  description?: string
  tags: string[]
}

interface ToolCardProps {
  tool: Tool
  suitabilityScore: number
  demoPriority: number
  explanation: string
  repoId: string
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'bg-green-500'
  if (score >= 60) return 'bg-yellow-500'
  return 'bg-orange-500'
}

function getPriorityLabel(priority: number): string {
  if (priority <= 2) return 'High Priority'
  if (priority <= 3) return 'Medium Priority'
  return 'Low Priority'
}

function getPriorityColor(priority: number): string {
  if (priority <= 2) return 'bg-red-100 text-red-700'
  if (priority <= 3) return 'bg-yellow-100 text-yellow-700'
  return 'bg-gray-100 text-gray-600'
}

export default function ToolCard({
  tool,
  suitabilityScore,
  demoPriority,
  explanation,
  repoId,
}: ToolCardProps) {
  return (
    <div className="bg-white p-5 rounded-lg shadow-md">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">{tool.name}</h3>
          <p className="text-gray-600 text-sm">{tool.description}</p>
        </div>
        <div className="flex gap-2">
          <span className={`text-xs px-2 py-1 rounded font-medium ${getPriorityColor(demoPriority)}`}>
            {getPriorityLabel(demoPriority)}
          </span>
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
            {tool.category}
          </span>
        </div>
      </div>

      <div className="mb-3">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-600">Suitability Score</span>
          <span className="font-medium text-gray-800">{Math.round(suitabilityScore)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${getScoreColor(suitabilityScore)}`}
            style={{ width: `${suitabilityScore}%` }}
          />
        </div>
      </div>

      <p className="text-gray-600 text-sm mb-4 italic">{explanation}</p>

      <Link
        to={`/schedule/${repoId}/${tool.id}`}
        className="inline-block bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm font-medium"
      >
        Schedule Demo
      </Link>
    </div>
  )
}
