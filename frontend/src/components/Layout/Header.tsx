export function Header({ title }: { title: string }) {
  return (
    <header className="h-14 border-b border-gray-200 bg-white flex items-center px-6">
      <h1 className="font-semibold text-gray-800">{title}</h1>
    </header>
  )
}
