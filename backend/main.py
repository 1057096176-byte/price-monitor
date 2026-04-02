from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os

from database import get_db, Product, PriceHistory, Settings
from scraper import fetch_price, detect_platform
from notifier import send_wechat
from scheduler import start_scheduler, stop_scheduler, check_all_prices

app = FastAPI(title="价格监控")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    start_scheduler()

@app.on_event("shutdown")
def shutdown():
    stop_scheduler()

# ── 商品 ──────────────────────────────────────────────

class AddProductRequest(BaseModel):
    url: str

@app.post("/api/products")
def add_product(req: AddProductRequest, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.url == req.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="该商品已在监控列表中")

    taobao_cookie = None
    settings_row = db.query(Settings).filter(Settings.key == "taobao_cookie").first()
    if settings_row:
        taobao_cookie = settings_row.value

    result = fetch_price(req.url, taobao_cookie)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    product = Product(
        url=req.url,
        name=result["name"],
        platform=result["platform"],
        current_price=result["price"],
    )
    db.add(product)
    db.flush()
    db.add(PriceHistory(product_id=product.id, price=result["price"]))
    db.commit()
    db.refresh(product)
    return product

@app.get("/api/products")
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    result = []
    for p in products:
        history = (
            db.query(PriceHistory)
            .filter(PriceHistory.product_id == p.id)
            .order_by(PriceHistory.checked_at)
            .all()
        )
        result.append({
            "id": p.id,
            "name": p.name,
            "url": p.url,
            "platform": p.platform,
            "current_price": p.current_price,
            "created_at": p.created_at,
            "history": [{"price": h.price, "checked_at": h.checked_at} for h in history],
            "min_price": min((h.price for h in history), default=p.current_price),
            "max_price": max((h.price for h in history), default=p.current_price),
        })
    return result

@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    db.query(PriceHistory).filter(PriceHistory.product_id == product_id).delete()
    db.delete(product)
    db.commit()
    return {"ok": True}

@app.post("/api/products/{product_id}/check")
def check_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    taobao_cookie = None
    row = db.query(Settings).filter(Settings.key == "taobao_cookie").first()
    if row:
        taobao_cookie = row.value
    result = fetch_price(product.url, taobao_cookie)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    product.current_price = result["price"]
    db.add(PriceHistory(product_id=product.id, price=result["price"]))
    db.commit()
    return {"price": result["price"]}

@app.post("/api/check-all")
def check_all():
    check_all_prices()
    return {"ok": True}

# ── 设置 ──────────────────────────────────────────────

class SettingsRequest(BaseModel):
    sendkey: Optional[str] = None
    taobao_cookie: Optional[str] = None

@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    rows = db.query(Settings).all()
    data = {r.key: r.value for r in rows}
    return {
        "sendkey": data.get("sendkey", ""),
        "taobao_cookie": data.get("taobao_cookie", ""),
    }

@app.post("/api/settings")
def save_settings(req: SettingsRequest, db: Session = Depends(get_db)):
    for key, value in [("sendkey", req.sendkey), ("taobao_cookie", req.taobao_cookie)]:
        if value is None:
            continue
        row = db.query(Settings).filter(Settings.key == key).first()
        if row:
            row.value = value
        else:
            db.add(Settings(key=key, value=value))
    db.commit()
    return {"ok": True}

@app.post("/api/settings/test-notify")
def test_notify(db: Session = Depends(get_db)):
    row = db.query(Settings).filter(Settings.key == "sendkey").first()
    if not row or not row.value:
        raise HTTPException(status_code=400, detail="请先填写 Server酱 SendKey")
    ok = send_wechat(row.value, "✅ 价格监控测试", "微信通知配置成功！价格变动时你会收到提醒。")
    if not ok:
        raise HTTPException(status_code=400, detail="发送失败，请检查 SendKey 是否正确")
    return {"ok": True}

# ── 前端静态文件 ──────────────────────────────────────

if os.path.exists("../frontend/dist"):
    app.mount("/assets", StaticFiles(directory="../frontend/dist/assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        return FileResponse("../frontend/dist/index.html")
