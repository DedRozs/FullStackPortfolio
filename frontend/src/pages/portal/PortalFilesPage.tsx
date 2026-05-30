import { useEffect, useRef, useState } from 'react'
import { Button } from '../../components/catalyst-ui-kit/typescript/button'
import { ErrorMessage } from '../../components/catalyst-ui-kit/typescript/fieldset'
import { Heading } from '../../components/catalyst-ui-kit/typescript/heading'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/catalyst-ui-kit/typescript/table'
import { Text } from '../../components/catalyst-ui-kit/typescript/text'

interface FileRecord {
  id: string
  filename: string
  mime_type: string
  file_size_bytes: number
  created_at: string
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function PortalFilesPage() {
  const token = localStorage.getItem('auth_token')
  const headers = { Authorization: `Token ${token}` }

  const [files, setFiles] = useState<FileRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetch('/api/portal/files/', { headers })
      .then((r) => r.json())
      .then((d) => {
        setFiles(d.results ?? d)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    uploadFile(file)
  }

  function uploadFile(file: File) {
    setError(null)
    setUploading(true)
    setProgress(0)

    const formData = new FormData()
    formData.append('file', file)

    const xhr = new XMLHttpRequest()
    xhr.upload.onprogress = (ev) => {
      if (ev.lengthComputable) {
        setProgress(Math.round((ev.loaded / ev.total) * 100))
      }
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const result = JSON.parse(xhr.responseText)
        setFiles((prev) => [
          {
            id: result.id,
            filename: result.filename,
            mime_type: file.type,
            file_size_bytes: file.size,
            created_at: new Date().toISOString(),
          },
          ...prev,
        ])
      } else {
        try {
          const body = JSON.parse(xhr.responseText)
          setError(body.detail ?? `Upload failed (HTTP ${xhr.status})`)
        } catch {
          setError(`Upload failed (HTTP ${xhr.status})`)
        }
      }
      setUploading(false)
      setProgress(0)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
    xhr.onerror = () => {
      setError('Network error during upload')
      setUploading(false)
      setProgress(0)
    }
    xhr.open('POST', '/api/portal/files/upload/')
    xhr.setRequestHeader('Authorization', `Token ${token}`)
    xhr.send(formData)
  }

  return (
    <div>
      <Heading level={1} className="font-display tracking-wider uppercase text-neon-cyan mb-2">
        Files
      </Heading>
      <Text className="mb-8">Upload and manage project files.</Text>

      <div className="mb-8 rounded-xl border border-cyber-border bg-cyber-surface p-6">
        <Text className="mb-4 font-medium">Upload a file</Text>
        <div className="flex items-center gap-4">
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileChange}
            disabled={uploading}
            className="block text-sm text-text-muted file:mr-4 file:rounded file:border file:border-neon-cyan file:bg-transparent file:px-3 file:py-1 file:text-xs file:font-mono file:uppercase file:text-neon-cyan file:tracking-wider hover:file:bg-neon-cyan/10 disabled:opacity-50"
          />
          {uploading && (
            <Button disabled color="neon-cyan-outline">
              {progress}% uploading...
            </Button>
          )}
        </div>
        {uploading && (
          <div className="mt-3 h-1.5 w-full rounded bg-cyber-border overflow-hidden">
            <div
              className="h-full rounded bg-neon-cyan transition-all duration-200"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
        {error && <ErrorMessage className="mt-3">{error}</ErrorMessage>}
      </div>

      {loading ? (
        <Text className="animate-pulse">Loading files...</Text>
      ) : files.length === 0 ? (
        <Text>No files uploaded yet.</Text>
      ) : (
        <Table>
          <TableHead>
            <TableRow>
              <TableHeader>Name</TableHeader>
              <TableHeader>Type</TableHeader>
              <TableHeader>Size</TableHeader>
              <TableHeader>Uploaded</TableHeader>
            </TableRow>
          </TableHead>
          <TableBody>
            {files.map((f) => (
              <TableRow key={f.id}>
                <TableCell className="font-medium">{f.filename}</TableCell>
                <TableCell className="font-mono text-xs">{f.mime_type}</TableCell>
                <TableCell>{formatBytes(f.file_size_bytes)}</TableCell>
                <TableCell>{new Date(f.created_at).toLocaleDateString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
