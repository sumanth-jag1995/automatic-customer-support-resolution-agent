import { useState } from 'react'

interface Props { onSubmit: (data: { customer_id: string; subject: string; body: string }) => Promise<void> }

export function TicketForm({ onSubmit }: Props) {
  const [customerId, setCustomerId] = useState('cust_1')
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await onSubmit({ customer_id: customerId, subject, body })
      setSubject('')
      setBody('')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 bg-white p-4 rounded-xl border border-gray-200">
      <h3 className="font-semibold text-sm">New Ticket</h3>
      <select
        value={customerId}
        onChange={e => setCustomerId(e.target.value)}
        className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
      >
        <option value="cust_1">Alice Chen (cust_1)</option>
        <option value="cust_2">Bob Smith (cust_2)</option>
        <option value="cust_3">Carol White (cust_3)</option>
      </select>
      <input
        value={subject}
        onChange={e => setSubject(e.target.value)}
        placeholder="Subject"
        required
        className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
      />
      <textarea
        value={body}
        onChange={e => setBody(e.target.value)}
        placeholder="Describe the issue…"
        rows={3}
        required
        className="w-full rounded border border-gray-300 px-3 py-2 text-sm resize-none"
      />
      <button
        type="submit"
        disabled={loading}
        className="w-full py-2 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 disabled:opacity-50"
      >
        {loading ? 'Submitting…' : 'Submit Ticket'}
      </button>
    </form>
  )
}
