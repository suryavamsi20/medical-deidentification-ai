import { useState } from "react"
import UploadBox from "../components/UploadBox"

function Dashboard() {
  const [results, setResults] = useState(null)

  return (
    <div className="app-shell">
      <main className="page">
        <section className="hero">
          <span className="eyebrow">Clinical privacy workflow</span>
          <h1 className="page-title">Medical De-Identification System</h1>
          <p className="page-subtitle">
            Upload a clinical note or document and compare the original text
            with the redacted output. The backend combines OCR, Presidio,
            SpaCy, and Ollama to detect protected health information before
            redaction or anonymization.
          </p>
        </section>

        <UploadBox setResults={setResults} />

        {results && (
          <>
            <section className="summary-grid">
              <article className="panel summary-card">
                <p className="summary-label">Filename</p>
                <p className="summary-value">{results.filename}</p>
              </article>
              <article className="panel summary-card">
                <p className="summary-label">Identifiers Found</p>
                <p className="summary-value">{results.redaction_count}</p>
              </article>
              <article className="panel summary-card">
                <p className="summary-label">Detection Types</p>
                <p className="summary-value">{results.detected_types.length}</p>
              </article>
              <article className="panel summary-card">
                <p className="summary-label">Input Type</p>
                <p className="summary-value">{results.input_kind}</p>
              </article>
              <article className="panel summary-card">
                <p className="summary-label">Extraction Mode</p>
                <p className="summary-value">{results.extraction_method}</p>
              </article>
              <article className="panel summary-card">
                <p className="summary-label">Strategy</p>
                <p className="summary-value">{results.strategy}</p>
              </article>
            </section>

            <section className="results-grid">
              <article className="panel result-card">
                <h2 className="result-label">Original Text</h2>
                <pre className="result-pre">{results.original_text}</pre>
              </article>

              <article className="panel result-card">
                <h2 className="result-label redacted">Redacted Text</h2>
                <pre className="result-pre">{results.redacted_text}</pre>
              </article>
            </section>

            <section className="panel report-panel">
              <div className="report-header">
                <h2 className="report-title">Redaction Report</h2>
                <p className="report-copy">
                  Audit trail showing which entities were detected and how each
                  value was transformed.
                </p>
              </div>

              <div className="report-summary">
                {results.redaction_report.summary.map((item) => (
                  <div className="report-chip" key={item.entity_type}>
                    <span>{item.entity_type}</span>
                    <strong>{item.count}</strong>
                  </div>
                ))}
              </div>

              <div className="report-table-wrap">
                <table className="report-table">
                  <thead>
                    <tr>
                      <th>Entity</th>
                      <th>Original</th>
                      <th>Replacement</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.redaction_report.entries.map((entry, index) => (
                      <tr key={`${entry.entity_type}-${index}`}>
                        <td>{entry.entity_type}</td>
                        <td>{entry.original}</td>
                        <td>{entry.replacement}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  )
}

export default Dashboard
