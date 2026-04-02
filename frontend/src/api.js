const BASE = import.meta.env.VITE_API_URL || ""

async function req(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "请求失败")
  return data
}

export const api = {
  getProducts: () => req("GET", "/api/products"),
  addProduct: (url) => req("POST", "/api/products", { url }),
  deleteProduct: (id) => req("DELETE", `/api/products/${id}`),
  checkProduct: (id) => req("POST", `/api/products/${id}/check`),
  checkAll: () => req("POST", "/api/check-all"),
  getSettings: () => req("GET", "/api/settings"),
  saveSettings: (data) => req("POST", "/api/settings", data),
  testNotify: () => req("POST", "/api/settings/test-notify"),
}
