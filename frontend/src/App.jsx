import { useState, useEffect } from "react"
import { api } from "./api"

// ── 工具 ──────────────────────────────────────────────
function platformBadge(platform) {
  return platform === "jd"
    ? <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full font-medium">京东</span>
    : <span className="text-xs bg-orange-100 text-orange-600 px-2 py-0.5 rounded-full font-medium">淘宝</span>
}

function PriceTag({ current, min, max }) {
  const isMin = current <= min
  const isMax = current >= max
  return (
    <div className="text-right shrink-0">
      <div className="text-2xl font-bold text-gray-900">¥{current?.toFixed(2)}</div>
      <div className="text-xs text-gray-400 mt-0.5">
        最低 <span className="text-green-500 font-medium">¥{min?.toFixed(2)}</span>
        {" · "}
        最高 <span className="text-red-400 font-medium">¥{max?.toFixed(2)}</span>
      </div>
      {isMin && <div className="text-xs text-green-500 font-medium mt-0.5">📉 当前最低价</div>}
      {isMax && !isMin && <div className="text-xs text-red-400 font-medium mt-0.5">📈 当前最高价</div>}
    </div>
  )
}

function MiniChart({ history }) {
  const prices = history.map(h => h.price)
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1
  const W = 300, H = 40, PAD = 4
  const points = prices.map((p, i) => {
    const x = PAD + (i / (prices.length - 1)) * (W - PAD * 2)
    const y = PAD + ((max - p) / range) * (H - PAD * 2)
    return `${x},${y}`
  }).join(" ")
  return (
    <div className="mt-3">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-10">
        <polyline points={points} fill="none" stroke="#3b82f6" strokeWidth="1.5"
          strokeLinecap="round" strokeLinejoin="round" />
        {prices.map((p, i) => {
          const x = PAD + (i / (prices.length - 1)) * (W - PAD * 2)
          const y = PAD + ((max - p) / range) * (H - PAD * 2)
          return <circle key={i} cx={x} cy={y} r="2" fill="#3b82f6" />
        })}
      </svg>
    </div>
  )
}

function ProductCard({ product, onDelete, onCheck }) {
  const [checking, setChecking] = useState(false)
  async function handleCheck() {
    setChecking(true)
    try { await onCheck(product.id) } finally { setChecking(false) }
  }
  async function handleDelete() {
    if (!confirm(`确认删除「${product.name}」的监控？`)) return
    await onDelete(product.id)
  }
  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">{platformBadge(product.platform)}</div>
          <a href={product.url} target="_blank" rel="noreferrer"
            className="text-sm font-medium text-gray-800 line-clamp-2 leading-snug hover:text-blue-600">
            {product.name}
          </a>
        </div>
        <PriceTag current={product.current_price} min={product.min_price} max={product.max_price} />
      </div>
      {product.history?.length > 1 && <MiniChart history={product.history} />}
      <div className="flex gap-2 mt-3">
        <button onClick={handleCheck} disabled={checking}
          className="flex-1 text-sm py-2 rounded-xl bg-blue-50 text-blue-600 font-medium active:bg-blue-100 disabled:opacity-50">
          {checking ? "检查中…" : "立即检查"}
        </button>
        <button onClick={handleDelete}
          className="px-4 text-sm py-2 rounded-xl bg-gray-50 text-gray-400 font-medium active:bg-gray-100">
          删除
        </button>
      </div>
    </div>
  )
}

function AddModal({ onClose, onAdd }) {
  const [url, setUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  async function handleSubmit(e) {
    e.preventDefault()
    if (!url.trim()) return
    setLoading(true); setError("")
    try { await onAdd(url.trim()); onClose() }
    catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }
  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-end" onClick={onClose}>
      <div className="bg-white w-full rounded-t-3xl p-6 pb-10" onClick={e => e.stopPropagation()}>
        <div className="w-10 h-1 bg-gray-200 rounded-full mx-auto mb-5" />
        <h2 className="text-lg font-semibold text-gray-900 mb-4">添加监控商品</h2>
        <form onSubmit={handleSubmit}>
          <textarea value={url} onChange={e => setUrl(e.target.value)}
            placeholder="粘贴京东或淘宝商品链接…"
            className="w-full border border-gray-200 rounded-xl p-3 text-sm resize-none h-24 focus:outline-none focus:border-blue-400"
            autoFocus />
          {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
          <button type="submit" disabled={loading || !url.trim()}
            className="w-full mt-3 py-3 bg-blue-500 text-white rounded-xl font-medium text-sm disabled:opacity-50 active:bg-blue-600">
            {loading ? "获取价格中…" : "开始监控"}
          </button>
        </form>
      </div>
    </div>
  )
}

function SettingsPage({ onBack }) {
  const [form, setForm] = useState({ sendkey: "", taobao_cookie: "" })
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [msg, setMsg] = useState("")
  useEffect(() => { api.getSettings().then(setForm).catch(() => {}) }, [])
  async function handleSave() {
    setSaving(true); setMsg("")
    try { await api.saveSettings(form); setMsg("✅ 保存成功") }
    catch (e) { setMsg("❌ " + e.message) }
    finally { setSaving(false) }
  }
  async function handleTest() {
    setTesting(true); setMsg("")
    try { await api.testNotify(); setMsg("✅ 测试消息已发送，请查看微信") }
    catch (e) { setMsg("❌ " + e.message) }
    finally { setTesting(false) }
  }
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white px-4 py-4 flex items-center gap-3 border-b border-gray-100">
        <button onClick={onBack} className="text-blue-500 text-sm">← 返回</button>
        <h1 className="text-base font-semibold text-gray-900">设置</h1>
      </div>
      <div className="p-4 space-y-4">
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
          <h3 className="font-medium text-gray-900 mb-1">微信通知（Server酱）</h3>
          <p className="text-xs text-gray-400 mb-3">
            前往 <a href="https://sct.ftqq.com" target="_blank" className="text-blue-500">sct.ftqq.com</a> 微信扫码登录，复制 SendKey 填入下方
          </p>
          <input value={form.sendkey} onChange={e => setForm({ ...form, sendkey: e.target.value })}
            placeholder="SCT…"
            className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-blue-400" />
          <button onClick={handleTest} disabled={testing}
            className="mt-2 w-full py-2.5 bg-green-50 text-green-600 rounded-xl text-sm font-medium disabled:opacity-50">
            {testing ? "发送中…" : "发送测试消息"}
          </button>
        </div>
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
          <h3 className="font-medium text-gray-900 mb-1">淘宝 Cookie</h3>
          <p className="text-xs text-gray-400 mb-3">
            在电脑浏览器登录淘宝后，按 F12 → Network → 复制请求头中的 Cookie 值粘贴到此处
          </p>
          <textarea value={form.taobao_cookie} onChange={e => setForm({ ...form, taobao_cookie: e.target.value })}
            placeholder="Cookie: …"
            className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm resize-none h-24 focus:outline-none focus:border-blue-400" />
        </div>
        {msg && <p className="text-center text-sm text-gray-600">{msg}</p>}
        <button onClick={handleSave} disabled={saving}
          className="w-full py-3 bg-blue-500 text-white rounded-xl font-medium text-sm disabled:opacity-50">
          {saving ? "保存中…" : "保存设置"}
        </button>
      </div>
    </div>
  )
}

export default function App() {
  const [products, setProducts] = useState([])
  const [showAdd, setShowAdd] = useState(false)
  const [page, setPage] = useState("home")
  const [checkingAll, setCheckingAll] = useState(false)
  const [loading, setLoading] = useState(true)

  async function loadProducts() {
    try { const data = await api.getProducts(); setProducts(data) }
    catch (e) { console.error(e) }
    finally { setLoading(false) }
  }
  useEffect(() => { loadProducts() }, [])

  async function handleAdd(url) { await api.addProduct(url); await loadProducts() }
  async function handleDelete(id) { await api.deleteProduct(id); setProducts(p => p.filter(x => x.id !== id)) }
  async function handleCheck(id) { await api.checkProduct(id); await loadProducts() }
  async function handleCheckAll() {
    setCheckingAll(true)
    try { await api.checkAll(); await loadProducts() } finally { setCheckingAll(false) }
  }

  if (page === "settings") return <SettingsPage onBack={() => setPage("home")} />

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      <div className="bg-white px-4 py-4 flex items-center justify-between border-b border-gray-100 sticky top-0 z-10">
        <h1 className="text-base font-semibold text-gray-900">🔔 价格监控</h1>
        <div className="flex items-center gap-3">
          <button onClick={handleCheckAll} disabled={checkingAll}
            className="text-sm text-blue-500 disabled:opacity-50">
            {checkingAll ? "检查中…" : "全部检查"}
          </button>
          <button onClick={() => setPage("settings")} className="text-sm text-gray-400">设置</button>
        </div>
      </div>
      <div className="p-4 space-y-3">
        {loading && <div className="text-center text-gray-400 text-sm py-16">加载中…</div>}
        {!loading && products.length === 0 && (
          <div className="text-center py-20">
            <div className="text-5xl mb-4">📦</div>
            <p className="text-gray-400 text-sm">还没有监控的商品</p>
            <p className="text-gray-300 text-xs mt-1">点击下方按钮添加</p>
          </div>
        )}
        {products.map(p => (
          <ProductCard key={p.id} product={p} onDelete={handleDelete} onCheck={handleCheck} />
        ))}
      </div>
      <div className="fixed bottom-8 left-0 right-0 flex justify-center z-10">
        <button onClick={() => setShowAdd(true)}
          className="bg-blue-500 text-white px-8 py-3.5 rounded-full shadow-lg text-sm font-medium active:bg-blue-600 flex items-center gap-2">
          <span className="text-lg leading-none">+</span> 添加商品
        </button>
      </div>
      {showAdd && <AddModal onClose={() => setShowAdd(false)} onAdd={handleAdd} />}
    </div>
  )
}
