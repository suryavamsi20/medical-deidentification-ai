import { useState } from "react"
import { uploadDocument } from "../services/api"

function UploadBox({ setResults }) {
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState("")
  const [statusType, setStatusType] = useState("")
  const [strategy, setStrategy] = useState("placeholder")

  const handleUpload = async (event) => {
    const file = event.target.files?.[0]

    if (!file) {
      return
    }

    setLoading(true)
    setStatusType("loading")
    setStatus(`Processing ${file.name}...`)

    try {
      const data = await uploadDocument(file, strategy)
      setResults(data)
      setStatusType("success")
      setStatus(`Completed redaction for ${data.filename}.`)
    } catch (error) {
      setResults(null)
      setStatusType("error")
      setStatus(error.message)
    } finally {
      setLoading(false)
    }
  }

  const statusClassName = statusType ? `status-${statusType}` : ""

  return (
    <section className="panel upload-panel">
      <h2 className="upload-title">Upload Medical Document</h2>
      <p className="upload-copy">
        Supported formats: text files, PDFs, and images. The backend extracts
        embedded text from PDFs and uses OCR for images or scanned PDF pages,
        then applies hybrid PHI detection and either redacts or anonymizes the
        detected entities.
      </p>

      <label className="upload-label" htmlFor="strategy">
        De-identification strategy
      </label>
      <select
        id="strategy"
        className="upload-select"
        value={strategy}
        onChange={(event) => setStrategy(event.target.value)}
        disabled={loading}
      >
        <option value="placeholder">Neutral placeholders</option>
        <option value="synthetic">Synthetic replacements</option>
      </select>

      <input
        type="file"
        accept=".txt,.md,.csv,.json,.log,.text,.pdf,.png,.jpg,.jpeg,.bmp,.tif,.tiff,.webp"
        onChange={handleUpload}
        className="upload-input"
        disabled={loading}
      />

      <div className={`upload-meta ${statusClassName}`.trim()}>
        {status || "No document uploaded yet."}
      </div>
    </section>
  )
}

export default UploadBox
