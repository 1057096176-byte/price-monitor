import requests

def send_wechat(sendkey: str, title: str, content: str) -> bool:
    """通过 Server酱 发送微信通知"""
    if not sendkey:
        return False
    try:
        url = f"https://sctapi.ftqq.com/{sendkey}.send"
        resp = requests.post(url, data={"title": title, "desp": content}, timeout=10)
        return resp.json().get("code") == 0
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
