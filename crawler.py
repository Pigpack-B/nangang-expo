import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests

def fetch_tainex_real_schedule():
    """
    對接南港展覽館活動查詢服務端點，抓取當月與次月真實展期
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://www.tainex.com.tw",
        "Referer": "https://www.tainex.com.tw/events"
    }

    today = datetime.now()
    # 鎖定 2 個月份：當月與次月
    target_months = [today, today + relativedelta(months=1)]
    
    all_events = []
    seen_names = set()

    for d in target_months:
        year_str = str(d.year)
        month_str = f"{d.month:02d}"

        # 官網展覽資料查詢端點
        query_url = f"https://www.tainex.com.tw/api/v1/event/list?year={year_str}&month={month_str}&hall="
        
        try:
            res = requests.get(query_url, headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json()
                
                # 相容回傳結構 (可能位於 data, result, 或 items 欄位)
                items = []
                if isinstance(data, dict):
                    items = data.get("data") or data.get("result") or data.get("items") or []
                elif isinstance(data, list):
                    items = data

                for item in items:
                    name = item.get("title") or item.get("name") or item.get("eventName") or ""
                    start = item.get("startDate") or item.get("start") or item.get("beginDate") or ""
                    end = item.get("endDate") or item.get("end") or ""
                    link = item.get("url") or item.get("link") or "https://www.tainex.com.tw/events"

                    if name and start:
                        clean_name = name.strip()
                        if clean_name not in seen_names:
                            seen_names.add(clean_name)
                            all_events.append({
                                "name": clean_name,
                                "startDate": str(start)[:10].replace("/", "-"),
                                "endDate": str(end)[:10].replace("/", "-") if end else str(start)[:10].replace("/", "-"),
                                "icon": "🎪",
                                "url": link if link.startswith("http") else f"https://www.tainex.com.tw{link}"
                            })
            else:
                # 備用端點：POST 查詢格式
                post_url = "https://www.tainex.com.tw/api/v1/events/search"
                payload = {"year": year_str, "month": month_str}
                post_res = requests.post(post_url, headers=headers, json=payload, timeout=15)
                if post_res.status_code == 200:
                    data = post_res.json()
                    items = data.get("data") or []
                    for item in items:
                        name = item.get("title") or item.get("name") or ""
                        start = item.get("startDate") or ""
                        end = item.get("endDate") or ""
                        link = item.get("url") or "https://www.tainex.com.tw/events"
                        if name and start and name not in seen_names:
                            seen_names.add(name)
                            all_events.append({
                                "name": name.strip(),
                                "startDate": str(start)[:10].replace("/", "-"),
                                "endDate": str(end)[:10].replace("/", "-") if end else str(start)[:10].replace("/", "-"),
                                "icon": "🎪",
                                "url": link
                            })
        except Exception as err:
            print(f"[{year_str}-{month_str}] 查詢失敗: {err}")

    # 排序
    all_events.sort(key=lambda x: x["startDate"])

    # 輸出至 events.json
    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)

    print(f"爬取作業完成，共寫入 {len(all_events)} 筆最新展覽資料。")

if __name__ == "__main__":
    fetch_tainex_real_schedule()
