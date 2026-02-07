interface ToolCardProps {
  name: string
  description: string
  category: string
}

export default function ToolCard({ name, description, category }: ToolCardProps) {
  return (
    <div className="bg-white p-4 rounded-lg shadow-md">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">{name}</h3>
          <p className="text-gray-600 text-sm">{description}</p>
        </div>
        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">{category}</span>
      </div>
    </div>
  )
}
