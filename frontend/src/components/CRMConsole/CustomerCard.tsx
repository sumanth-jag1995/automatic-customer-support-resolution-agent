const customers: Record<string, { name: string; email: string; plan: string }> = {
  cust_1: { name: 'Alice Chen', email: 'alice@example.com', plan: 'Pro' },
  cust_2: { name: 'Bob Smith', email: 'bob@example.com', plan: 'Free' },
  cust_3: { name: 'Carol White', email: 'carol@example.com', plan: 'Enterprise' },
}

export function CustomerCard({ customerId }: { customerId: string }) {
  const c = customers[customerId]
  if (!c) return <p className="text-sm text-gray-400">Unknown customer: {customerId}</p>
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold">
          {c.name[0]}
        </div>
        <div>
          <p className="font-semibold text-sm">{c.name}</p>
          <p className="text-xs text-gray-500">{c.email}</p>
        </div>
        <span className="ml-auto text-xs px-2 py-1 bg-indigo-100 text-indigo-700 rounded-full">{c.plan}</span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-gray-600">
        <div className="bg-gray-50 rounded p-2"><span className="font-medium">ID:</span> {customerId}</div>
        <div className="bg-gray-50 rounded p-2"><span className="font-medium">Status:</span> Active</div>
      </div>
    </div>
  )
}
