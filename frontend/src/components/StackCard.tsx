interface StackCardProps {
  name: string
  version: string
  category: string
}

export default function StackCard({ name, version, category }: StackCardProps) {
  return (
    <div className="bg-white p-4 rounded-lg shadow-md">
      <span className="text-xs text-blue-600 font-medium">{category}</span>
      <h3 className="text-lg font-semibold text-gray-800">{name}</h3>
      <p className="text-gray-500 text-sm">v{version}</p>
    </div>
  )
}
