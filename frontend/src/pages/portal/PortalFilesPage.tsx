import { useEffect, useRef, useState } from 'react'

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
    <div className="max-w-5xl mx-auto px-6 py-12">
      <h1 className="font-display text-3xl font-bold tracking-wider uppercase text-neon-cyan mb-2">
        Files
      </h1>
      <p className="text-zinc-400 mb-8">Upload and manage project files.</p>

      <div className="mb-8 rounded border border-zinc-700 bg-zinc-900 p-6">
        <p className="mb-4 text-sm text-zinc-300 font-medium">Upload a file</p>
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileChange}
          disabled={uploading}
          className="block w-full text-sm text-zinc-300 file:mr-4 file:rounded file:border file:border-neon-cyan file:bg-transparent file:px-3 file:py-1 file:text-xs file:font-mono file:uppercase file:text-neon-cyan file:tracking-wider hover:file:bg-neon-cyan/10 disabled:opacity-50"
        />
        {uploading && (
          <div className="mt-4">
            <div className="h-1.5 w-full rounded bg-zinc-700 overflow-hidden">
              <div
                className="h-full rounded bg-neon-cyan transition-all duration-200"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-zinc-400">{progress}% uploaded</p>
          </div>
        )}
        {error && (
          <p className="mt-3 text-xs text-red-400">{error}</p>
        )}
      </div>

      {loading ? (
        <p className="text-zinc-400 animate-pulse">Loading files...</p>
      ) : files.length === 0 ? (
        <p className="text-zinc-500 text-sm">No files uploaded yet.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-700 text-left text-zinc-400">
              <th className="pb-2 pr-4">Name</th>
              <th className="pb-2 pr-4">Type</th>
              <th className="pb-2 pr-4">Size</th>
              <th className="pb-2">Uploaded</th>
            </tr>
          </thead>
          <tbody>
            {files.map((f) => (
              <tr key={f.id} className="border-b border-zinc-800 hover:bg-zinc-800/40 transition">
                <td className="py-2 pr-4 text-zinc-200">{f.filename}</td>
                <td className="py-2 pr-4 font-mono text-xs text-zinc-400">{f.mime_type}</td>
                <td className="py-2 pr-4 text-zinc-400">{formatBytes(f.file_size_bytes)}</td>
                <td className="py-2 text-zinc-500 text-xs">
                  {new Date(f.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
