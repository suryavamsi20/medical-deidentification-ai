const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
const API_URL = `${API_BASE_URL}/upload-document`

export const uploadDocument = async (file, strategy) => {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("strategy", strategy)

  const response = await fetch(API_URL, {
    method: "POST",
    body: formData,
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(data.detail || "Document upload failed.")
  }

  return data
}
