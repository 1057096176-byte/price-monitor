import requests

BARK_KEY = "geyR9EoHhePS4c27EJACo"

def send_wechat(sendkey: str, title: str, content: str) -> bool:
    """通过 Bark 发送手机通知"""
    key = sendkey or BARK_KEY
    if not key:
        return False
    try:
        url = "https://api.day.app/push"
        resp = requests.post(url, json={
            "device_key": key,
            "title": title,
            "body": content,
            "sound": "default",
        }, timeout=10)
        return resp.json().get("code") == 200
    except Exception:
        return False

def build_price_change_message(name: str, platform: str, old_price: float, new_price: float, url: str) -> tuple[str, str]:
    diff = new_price - old_price
    direction = "📈 涨价" if diff > 0 else "📉 降价"
    pct = abs(diff / old_price * 100)
    platform_name = "京东" if platform == "jd" else "淘宝"

    title = f"{direction} | {name[:20]}"
    content = (
        f"**商品**：{name}\n\n"
        f"**平台**：{platform_name}\n\n"
        f"**变动**：{direction} {abs(diff):.2f} 元（{pct:.1f}%）\n\n"
        f"**原价**：¥{old_price:.2f}\n\n"
        f"**现价**：¥{new_price:.2f}\n\n"
        f"**链接**：[点击查看]({url})"
    )
    return title, content
