import { useRef, useState } from "react"
import { createFileRoute } from "@tanstack/react-router"
import { motion, AnimatePresence } from "framer-motion"
import { FileText, UploadCloud, CheckCircle2, XCircle, Trash2, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useDocuments } from "@/hooks/useDocuments"
import { uploadDocument, ApiError } from "@/lib/api"
import { cn } from "@/lib/utils"

export const Route = createFileRoute("/_app/documents")({
  component: DocumentsPage,
})

function DocumentsPage() {
  const { documents, addDocument, removeDocument } = useDocuments()
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return
    const file = files[0]

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setStatusMessage("Only PDF files are supported.")
      return
    }

    const docId = crypto.randomUUID()
    setIsUploading(true)
    setStatusMessage(`Uploading ${file.name}...`)

    try {
      const response = await uploadDocument(file)
      addDocument({
        id: docId,
        name: file.name,
        chunksIndexed: response.chunks_indexed,
        uploadedAt: Date.now(),
        status: "success",
      })
      setStatusMessage(
        `${file.name} indexed successfully (${response.chunks_indexed} chunks).`
      )
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Upload failed unexpectedly."
      addDocument({
        id: docId,
        name: file.name,
        chunksIndexed: 0,
        uploadedAt: Date.now(),
        status: "error",
        errorMessage: message,
      })
      setStatusMessage(message)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="mx-auto flex h-screen max-w-3xl flex-col gap-6 overflow-y-auto p-8">
      <div>
        <h1 className="text-xl font-semibold">Documents</h1>
        <p className="text-sm text-muted-foreground">
          Upload PDFs so CARA can answer questions grounded in their content.
        </p>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setIsDragging(false)
          handleFiles(e.dataTransfer.files)
        }}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed p-12 text-center transition-colors",
          isDragging ? "border-primary bg-primary/5" : "border-border hover:bg-secondary/30"
        )}
      >
        {isUploading ? (
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        ) : (
          <UploadCloud className="h-8 w-8 text-muted-foreground" />
        )}
        <div>
          <p className="text-sm font-medium">
            {isUploading ? "Uploading..." : "Drag & drop a PDF here, or click to browse"}
          </p>
          <p className="text-xs text-muted-foreground">PDF files only</p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {statusMessage && (
        <p className="text-sm text-muted-foreground">{statusMessage}</p>
      )}

      <div className="flex flex-col gap-2">
        <h2 className="text-sm font-semibold text-muted-foreground">
          Indexed documents ({documents.length})
        </h2>

        {documents.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No documents uploaded yet in this browser.
          </p>
        )}

        <AnimatePresence initial={false}>
          {documents.map((doc) => (
            <motion.div
              key={doc.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, height: 0 }}
              className="glass flex items-center justify-between rounded-xl px-4 py-3"
            >
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 shrink-0 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">{doc.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {doc.status === "success"
                      ? `${doc.chunksIndexed} chunks · ${new Date(doc.uploadedAt).toLocaleString()}`
                      : doc.errorMessage}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {doc.status === "success" ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-destructive" />
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeDocument(doc.id)}
                  title="Remove from this list"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
