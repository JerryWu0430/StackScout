interface StackCardProps {
  category: string
  technologies: string[]
}

const CATEGORY_ICONS: Record<string, string> = {
  frontend: '🖥️',
  backend: '⚙️',
  database: '🗄️',
  infrastructure: '☁️',
}

export default function StackCard({ category, technologies }: StackCardProps) {
  const icon = CATEGORY_ICONS[category.toLowerCase()] || '📦'

  return (
    <div className="bg-white p-5 rounded-lg shadow-md">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xl">{icon}</span>
        <h3 className="text-lg font-semibold text-gray-800 capitalize">{category}</h3>
      </div>
      {technologies.length > 0 ? (
        <ul className="space-y-1">
          {technologies.map((tech) => (
            <li key={tech} className="text-gray-600 text-sm flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
              {tech}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-gray-400 text-sm italic">None detected</p>
      )}
    </div>
  )
}
