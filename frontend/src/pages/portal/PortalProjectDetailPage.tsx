import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

interface Milestone {
  id: string
  name: string
  status: string
  target_date: string | null
}

interface Approval {
  id: string
  deliverable_version: string
  status: string
  comment: string | null
}

const STATUS_BADGE: Record<string, string> = {
  PENDING: 'text-zinc-400 border-zinc-600',
  IN_PROGRESS: 'text-neon-cyan border-neon-cyan',
  COMPLETE: 'text-green-400 border-green-400',
  APPROVED: 'text-green-400 border-green-400',
  REJECTED: 'text-red-400 border-red-400',
  REVISION_REQUESTED: 'text-yellow-400 border-yellow-400',
}

export default function PortalProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const token = localStorage.getItem('auth_token')
  const headers = { Authorization: `Token ${token}` }

  const [milestones, setMilestones] = useState<Milestone[]>([])
  const [approvals, setApprovals] = useState<Approval[]>([])
  const [actionError, setActionError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    fetch(`/api/portal/milestones/?project=${id}`, { headers })
      .then((r) => r.json())
      .then((d) => setMilestones(d.results ?? d))
    fetch(`/api/portal/approvals/`, { headers })
      .then((r) => r.json())
      .then((d) => setApprovals(d.results ?? d))
  }, [id])

  async function handleApprovalAction(
    approvalId: string,
    action: 'grant' | 'reject' | 'request-revision',
    comment?: string,
  ) {
    setActionError(null)
    const res = await fetch(`/api/portal/approvals/${approvalId}/${action}/`, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ comment: comment ?? '' }),
    })
    if (!res.ok) {
      const body = await res.json()
      setActionError(body.detail ?? 'Action failed')
      return
    }
    const updated = await res.json()
    setApprovals((prev) =>
      prev.map((a) => (a.id === approvalId ? { ...a, status: updated.status } : a)),
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <h1 className="font-display text-3xl font-bold tracking-wider uppercase text-neon-cyan mb-8">
        Project Detail
      </h1>

      {actionError && (
        <p className="mb-6 rounded border border-red-500 bg-red-950/40 px-4 py-2 text-sm text-red-300">
          {actionError}
        </p>
      )}

      <section className="mb-12">
        <h2 className="font-display text-xl uppercase tracking-widest text-zinc-300 mb-4">
          Milestones
        </h2>
        {milestones.length === 0 ? (
          <p className="text-zinc-500 text-sm">No milestones yet.</p>
        ) : (
          <div className="space-y-3">
            {milestones.map((ms) => (
              <div
                key={ms.id}
                className="flex items-center justify-between rounded border border-zinc-700 bg-zinc-900 px-4 py-3"
              >
                <span className="text-white">{ms.name}</span>
                <div className="flex items-center gap-4">
                  {ms.target_date && (
                    <span className="text-xs text-zinc-500">{ms.target_date}</span>
                  )}
                  <span
                    className={`rounded border px-2 py-0.5 text-xs font-mono uppercase tracking-wider ${STATUS_BADGE[ms.status] ?? 'text-zinc-400 border-zinc-600'}`}
                  >
                    {ms.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="font-display text-xl uppercase tracking-widest text-zinc-300 mb-4">
          Approvals
        </h2>
        {approvals.length === 0 ? (
          <p className="text-zinc-500 text-sm">No approvals yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-700 text-left text-zinc-400">
                <th className="pb-2 pr-4">Version</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Comment</th>
                <th className="pb-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {approvals.map((ap) => (
                <tr key={ap.id} className="border-b border-zinc-800">
                  <td className="py-2 pr-4 font-mono text-zinc-300">{ap.deliverable_version}</td>
                  <td className="py-2 pr-4">
                    <span
                      className={`rounded border px-2 py-0.5 text-xs font-mono uppercase ${STATUS_BADGE[ap.status] ?? 'text-zinc-400 border-zinc-600'}`}
                    >
                      {ap.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-zinc-400">{ap.comment ?? '-'}</td>
                  <td className="py-2">
                    {ap.status === 'PENDING' && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleApprovalAction(ap.id, 'grant')}
                          className="rounded border border-green-600 px-2 py-0.5 text-xs text-green-400 transition hover:bg-green-900/30"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => {
                            const comment = window.prompt('Rejection reason:')
                            if (comment) handleApprovalAction(ap.id, 'reject', comment)
                          }}
                          className="rounded border border-red-600 px-2 py-0.5 text-xs text-red-400 transition hover:bg-red-900/30"
                        >
                          Reject
                        </button>
                        <button
                          onClick={() => {
                            const comment = window.prompt('Revision notes:')
                            if (comment) handleApprovalAction(ap.id, 'request-revision', comment)
                          }}
                          className="rounded border border-yellow-600 px-2 py-0.5 text-xs text-yellow-400 transition hover:bg-yellow-900/30"
                        >
                          Revise
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}
