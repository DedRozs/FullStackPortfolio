import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Badge } from '../../components/catalyst-ui-kit/typescript/badge'
import { Button } from '../../components/catalyst-ui-kit/typescript/button'
import { Dialog, DialogActions, DialogBody, DialogDescription, DialogTitle } from '../../components/catalyst-ui-kit/typescript/dialog'
import { ErrorMessage, Field, Label } from '../../components/catalyst-ui-kit/typescript/fieldset'
import { Heading, Subheading } from '../../components/catalyst-ui-kit/typescript/heading'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/catalyst-ui-kit/typescript/table'
import { Text } from '../../components/catalyst-ui-kit/typescript/text'
import { Textarea } from '../../components/catalyst-ui-kit/typescript/textarea'

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

type ApprovalAction = 'grant' | 'reject' | 'request-revision'

const STATUS_COLOR: Record<string, 'cyan' | 'green' | 'red' | 'yellow' | 'zinc'> = {
  PENDING: 'zinc',
  IN_PROGRESS: 'cyan',
  COMPLETE: 'green',
  APPROVED: 'green',
  REJECTED: 'red',
  REVISION_REQUESTED: 'yellow',
}

const ACTION_LABEL: Record<ApprovalAction, string> = {
  grant: 'Approve',
  reject: 'Reject',
  'request-revision': 'Request Revision',
}

export default function PortalProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const token = localStorage.getItem('auth_token')
  const headers = { Authorization: `Token ${token}` }

  const [milestones, setMilestones] = useState<Milestone[]>([])
  const [approvals, setApprovals] = useState<Approval[]>([])
  const [actionError, setActionError] = useState<string | null>(null)

  const [dialogOpen, setDialogOpen] = useState(false)
  const [pendingAction, setPendingAction] = useState<{ approvalId: string; action: ApprovalAction } | null>(null)
  const [comment, setComment] = useState('')

  useEffect(() => {
    if (!id) return
    fetch(`/api/portal/milestones/?project=${id}`, { headers })
      .then((r) => r.json())
      .then((d) => setMilestones(d.results ?? d))
    fetch(`/api/portal/approvals/`, { headers })
      .then((r) => r.json())
      .then((d) => setApprovals(d.results ?? d))
  }, [id])

  function openDialog(approvalId: string, action: ApprovalAction) {
    setPendingAction({ approvalId, action })
    setComment('')
    setActionError(null)
    setDialogOpen(true)
  }

  async function submitAction() {
    if (!pendingAction) return
    setActionError(null)
    const { approvalId, action } = pendingAction
    const res = await fetch(`/api/portal/approvals/${approvalId}/${action}/`, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ comment }),
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
    setDialogOpen(false)
    setPendingAction(null)
  }

  return (
    <div>
      <Heading level={1} className="font-display tracking-wider uppercase text-neon-cyan mb-8">
        Project Detail
      </Heading>

      <section className="mb-12">
        <Subheading level={2} className="font-display uppercase tracking-widest mb-4">
          Milestones
        </Subheading>
        {milestones.length === 0 ? (
          <Text>No milestones yet.</Text>
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableHeader>Milestone</TableHeader>
                <TableHeader>Target Date</TableHeader>
                <TableHeader>Status</TableHeader>
              </TableRow>
            </TableHead>
            <TableBody>
              {milestones.map((ms) => (
                <TableRow key={ms.id}>
                  <TableCell className="font-medium">{ms.name}</TableCell>
                  <TableCell>{ms.target_date ?? '-'}</TableCell>
                  <TableCell>
                    <Badge color={STATUS_COLOR[ms.status] ?? 'zinc'}>
                      {ms.status.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </section>

      <section>
        <Subheading level={2} className="font-display uppercase tracking-widest mb-4">
          Approvals
        </Subheading>
        {approvals.length === 0 ? (
          <Text>No approvals yet.</Text>
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableHeader>Version</TableHeader>
                <TableHeader>Status</TableHeader>
                <TableHeader>Comment</TableHeader>
                <TableHeader>Actions</TableHeader>
              </TableRow>
            </TableHead>
            <TableBody>
              {approvals.map((ap) => (
                <TableRow key={ap.id}>
                  <TableCell className="font-mono">{ap.deliverable_version}</TableCell>
                  <TableCell>
                    <Badge color={STATUS_COLOR[ap.status] ?? 'zinc'}>
                      {ap.status.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell>{ap.comment ?? '-'}</TableCell>
                  <TableCell>
                    {ap.status === 'PENDING' && (
                      <div className="flex gap-2">
                        <Button color="green" onClick={() => openDialog(ap.id, 'grant')}>
                          Approve
                        </Button>
                        <Button color="red" onClick={() => openDialog(ap.id, 'reject')}>
                          Reject
                        </Button>
                        <Button color="yellow" onClick={() => openDialog(ap.id, 'request-revision')}>
                          Revise
                        </Button>
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </section>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogTitle>
          {pendingAction ? ACTION_LABEL[pendingAction.action] : ''}
        </DialogTitle>
        <DialogDescription>
          Add an optional comment for this action.
        </DialogDescription>
        <DialogBody>
          <Field>
            <Label>Comment</Label>
            <Textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Optional notes..."
              rows={3}
            />
          </Field>
          {actionError && <ErrorMessage className="mt-3">{actionError}</ErrorMessage>}
        </DialogBody>
        <DialogActions>
          <Button plain onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button color="neon-cyan" onClick={submitAction}>Confirm</Button>
        </DialogActions>
      </Dialog>
    </div>
  )
}
