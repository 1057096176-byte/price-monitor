import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

def detect_platform(url: str) -> str:
    if "jd.com" in url:
        return "jd"
    elif "taobao.com" in url or "tmall.com" in url:
        return "taobao"
    return "unknown"

def fetch_jd_price(url: str) -> dict:
    """抓取京东商品价格和名称"""
    try:
        # 提取商品ID
        sku_id = re.search(r'/(\d+)\.html', url)
        if not sku_id:
            sku_id = re.search(r'sku=(\d+)', url)
        if not sku_id:
            return {"error": "无法解析京东商品ID"}
        sku_id = sku_id.group(1)

        # 获取商品名称
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        name = None
        for selector in ["title", ".sku-name", "#itemName"]:
            el = soup.select_one(selector)
            if el:
                name = el.get_text(strip=True).replace(" - 京东", "").strip()
                break

        # 获取价格（京东价格接口）
        price_url = f"https://p.3.cn/prices/mgets?skuIds=J_{sku_id}"
        price_resp = requests.get(price_url, headers=HEADERS, timeout=10)
        price_data = price_resp.json()
        if price_data and len(price_data) > 0:
            price = float(price_data[0].get("p", 0))
            return {"name": name or f"京东商品{sku_id}", "price": price, "platform": "jd"}
        return {"error": "无法获取京东价格"}
    except Exception as e:
        return {"error": str(e)}

def fetch_taobao_price(url: str, cookie: str = None) -> dict:
    """抓取淘宝/天猫商品价格"""
    try:
        headers = {**HEADERS}
        if cookie:
            headers["Cookie"] = cookie

        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")

        # 获取商品名称
        name = None
        for selector in ["title", ".ItemHeader--mainTitle--", ".tb-main-title"]:
            el = soup.select_one(selector)
            if el:
                name = el.get_text(strip=True).replace(" - 淘宝网", "").replace(" - 天猫", "").strip()
                break

        # 尝试从页面脚本中提取价格
        price = None
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string:
                # 匹配常见价格格式
                match = re.search(r'"defaultItemPrice"\s*:\s*"([\d.]+)"', script.string)
                if not match:
                    match = re.search(r'"price"\s*:\s*"([\d.]+)"', script.string)
                if not match:
                    match = re.search(r'skuCore.*?"price".*?"priceMoney"\s*:\s*"(\d+)"', script.string)
                if match:
                    raw = match.group(1)
                    price = float(raw) / 100 if len(raw) > 4 else float(raw)
                    break

        if price:
            return {"name": name or "淘宝商品", "price": price, "platform": "taobao"}

        if not cookie:
            return {"error": "淘宝需要登录Cookie才能获取价格，请在设置中填写"}
        return {"error": "无法解析淘宝价格，Cookie可能已过期"}
    except Exception as e:
        return {"error": str(e)}

def fetch_price(url: str, cookie: str = None) -> dict:
    platform = detect_platform(url)
    if platform == "jd":
        return fetch_jd_price(url)
    elif platform == "taobao":
        return fetch_taobao_price(url, cookie)
    return {"error": "不支持的平台，目前仅支持京东和淘宝"}
