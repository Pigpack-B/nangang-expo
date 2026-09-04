import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests

def fetch_events():
    """
    透過南港展覽館官方開放資料來源 (RSS/XML 及政府開放資料) 取得活動資訊
    完全繞過 Cloudflare 阻擋與動態反爬機制
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    today = datetime.now()
    next_month = today + relativedelta(months=1)
    
    # 鎖定當月與次月的年份與月份字串 (例如 "2026-09", "2026-10")
    valid_months = {
        f"{today.year}-{str(today.month).zfill(2)}",
        f"{next_month.year}-{str(next_month.month).zfill(2)}"
    }

    all_events = []
    seen_names = set()

    # 來源一：TaiNEX 官方活動行事曆 RSS 服務
    feed_urls = [
        "https://www.tainex.com.tw/rss/events",
        "https://www.tainex.com.tw/rss/events.xml"
    ]

    for f_url in feed_urls:
        try:
            res = requests.get(f_url, headers=headers, timeout=10)
            if res.status_code == 200 and ("xml" in res.headers.get("content-type", "") or res.text.strip().startswith("<?xml")):
                root = ET.fromstring(res.content)
                for item in root.findall(".//item"):
                    title = item.findtext("title", "").strip()
                    link = item.findtext("link", "").strip()
                    desc = item.findtext("description", "").strip()
                    
                    # 比對日期 (YYYY/MM/DD ~ YYYY/MM/DD 或 YYYY-MM-DD)
                    date_match = re.search(
                        r"(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})\s*[-~至]\s*(?:(\d{4})[./\-])?(\d{1,2})[./\-](\d{1,2})",
                        desc + " " + title
                    )
                    
                    if date_match and title not in seen_names:
                        g = date_match.groups()
                        s_date = f"{g[0]}-{g[1].zfill(2)}-{g[2].zfill(2)}"
                        e_year = g[3] if g[3] else g[0]
                        e_date = f"{e_year}-{g[4].zfill(2)}-{g[5].zfill(2)}"
                        
                        event_month = s_date[:7]
                        if event_month in valid_months:
                            seen_names.add(title)
                            all_events.append({
                                "name": title,
                                "startDate": s_date,
                                "endDate": e_date,
                                "icon": "🎪",
                                "url": link or "https://www.tainex.com.tw/events"
                            })
                if all_events:
                    break
        except Exception as e:
            print(f"嘗試抓取 RSS 失敗: {e}")

    # 來源二：如果 RSS 無法連線，連線外貿協會活動開放資料 API
    if not all_events:
        print("切換至開放資料備用介面連線...")
        open_data_url = "https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJ&category=6"
        try:
            res = requests.get(open_data_url, headers=headers, timeout=12)
            if res.status_code == 200:
                shows = res.json()
                for show in shows:
                    show_info = show.get("showInfo", [])
                    # 篩選南港展覽館 1 館或 2 館
                    for info in show_info:
                        location = info.get("locationName", "")
                        if "南港" in location and ("展覽" in location or "館" in location):
                            title = show.get("title", "").strip()
                            s_time = info.get("time", "")[:10].replace("/", "-")
                            e_time = info.get("endTime", "")[:10].replace("/", "-")
                            
                            if title and s_time and title not in seen_names:
                                if s_time[:7] in valid_months:
                                    seen_names.add(title)
                                    all_events.append({
                                        "name": title,
                                        "startDate": s_time,
                                        "endDate": e_time or s_time,
                                        "icon": "🎪",
                                        "url": show.get("webSales", "https://www.tainex.com.tw/events")
                                    })
        except Exception as e:
            print(f"嘗試抓取開放資料 API 失敗: {e}")

    # 排序
    all_events.sort(key=lambda x: x["startDate"])

    # 寫入 events.json
    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)

    print(f"寫入完成，共計入 {len(all_events)} 筆展覽。")

if __name__ == "__main__":
    fetch_events()
