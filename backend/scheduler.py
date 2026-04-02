from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from database import SessionLocal, Product, PriceHistory, Settings
from scraper import fetch_price
from notifier import send_wechat, build_price_change_message
from datetime import datetime

scheduler = BackgroundScheduler()

def get_setting(db: Session, key: str) -> str:
    row = db.query(Settings).filter(Settings.key == key).first()
    return row.value if row else None

def check_all_prices():
    db = SessionLocal()
    try:
        sendkey = get_setting(db, "sendkey")
        taobao_cookie = get_setting(db, "taobao_cookie")
        products = db.query(Product).all()

        for product in products:
            cookie = taobao_cookie if product.platform == "taobao" else None
            result = fetch_price(product.url, cookie)

            if "error" in result:
                continue

            new_price = result["price"]
            old_price = product.current_price

            # 记录价格历史
            db.add(PriceHistory(product_id=product.id, price=new_price, checked_at=datetime.utcnow()))

            # 价格有变动则通知
            if old_price is not None and abs(new_price - old_price) >= 0.01:
                product.current_price = new_price
                if sendkey:
                    title, content = build_price_change_message(
                        product.name, product.platform, old_price, new_price, product.url
                    )
                    send_wechat(sendkey, title, content)
            elif old_price is None:
                product.current_price = new_price

        db.commit()
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(check_all_prices, "interval", hours=1, id="price_check", replace_existing=True)
    scheduler.start()

def stop_scheduler():
    scheduler.shutdown()
