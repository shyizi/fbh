import re
import time
import requests
from PIL import Image, ImageDraw, ImageFont
import os

# ====================== 配置从 GitHub 环境变量读取 ======================
ZECTRIX_API_KEY = os.getenv("ZECTRIX_API_KEY")
DEVICE_ID = os.getenv("DEVICE_ID")
PUSH_PAGE_ID = "2"
SCREEN_W = 400
SCREEN_H = 300
# =====================================================================

TARGETS = [
    {"name": "华为终端", "uid": "huaweidevice"},
    {"name": "荣耀终端", "uid": "honor"},
    {"name": "OPPO", "uid": "oppo"},
    {"name": "大疆", "uid": "dji"},
    {"name": "Insta360影石", "uid": "insta360"},
    {"name": "联想中国", "uid": "lenovo"},
    {"name": "小米公司", "uid": "xiaomi"},
    {"name": "Redmi红米", "uid": "redmi"},
    {"name": "vivo", "uid": "vivo"},
    {"name": "iQOO", "uid": "iqoo"},
    {"name": "一加手机", "uid": "oneplus"},
    {"name": "华硕", "uid": "asus"},
    {"name": "ROG玩家国度", "uid": "asusrog"},
    {"name": "索尼中国", "uid": "sony"},
    {"name": "极米科技", "uid": "xgimi"},
    {"name": "追觅科技", "uid": "dreame"},
    {"name": "石头科技", "uid": "roborock"},
    {"name": "雷鸟创新", "uid": "rayneo"},
]

KEYWORDS = ["发布会", "定档", "新品", "官宣", "全场景", "旗舰", "发布", "直播", "预告"]
DATE_PATTERN = re.compile(r"(\d{1,2}月\d{1,2}日)")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def fetch_weibo_events():
    events = []
    for t in TARGETS:
        name = t["name"]
        uid = t["uid"]
        try:
            url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}"
            r = requests.get(url, headers=HEADERS, timeout=8)
            data = r.json()
            cards = data.get("data", {}).get("cards", [])
            for card in cards[:6]:
                if "mblog" not in card:
                    continue
                txt = card["mblog"]["text"]
                txt = re.sub(r'<[^>]+>', '', txt)
                if any(kw in txt for kw in KEYWORDS):
                    dates = DATE_PATTERN.findall(txt)
                    date = dates[0] if dates else "待官宣"
                    content = txt[:44].strip()
                    events.append({
                        "brand": name,
                        "date": date,
                        "content": content
                    })
                    break
        except Exception:
            pass
        time.sleep(1)
    return events

def create_eink_image(events):
    im = Image.new('1', (SCREEN_W, SCREEN_H), 1)
    draw = ImageDraw.Draw(im)

    # ==============================================
    # ✅ 已修复：强制使用你上传的 font.ttf 字体
    # ==============================================
    font_path = "./font.ttf"
    font_title = ImageFont.truetype(font_path, 20)
    font_text  = ImageFont.truetype(font_path, 14)

    # 标题
    draw.text((10, 6), "科技新品发布会监控", font=font_title, fill=0)
    draw.line((10, 33, SCREEN_W-10, 33), fill=0, width=1)

    y = 40
    if not events:
        draw.text((12, y), "暂无最新发布会", font=font_text, fill=0)
        return im

    for ev in events[:8]:
        draw.text((10, y), f"[{ev['brand']}] {ev['date']}", font=font_text, fill=0)
        draw.text((10, y+18), ev['content'], font=font_text, fill=0)
        y += 40
        if y > SCREEN_H - 30:
            break
    return im

def push_image(img_path):
    url = f"https://cloud.zectrix.com/open/v1/devices/{DEVICE_ID}/display/image"
    headers = {"X-API-Key": ZECTRIX_API_KEY}
    files = {"images": (os.path.basename(img_path), open(img_path, "rb"), "image/png")}
    data = {"pageId": PUSH_PAGE_ID, "dither": "true"}
    try:
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=20)
        return resp.json()
    except Exception:
        return {"error": "推送失败"}

if __name__ == "__main__":
    print("抓取中...")
    events = fetch_weibo_events()
    img = create_eink_image(events)
    img.save("eink_page2.png")
    print("推送中...")
    result = push_image("eink_page2.png")
    print("完成", result)
