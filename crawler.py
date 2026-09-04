import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests

def fetch_tainex_api_events():
    """
    直接呼叫南港展覽館官方 API 抓取當月與次月真實展覽
    無須解析 HTML，避開動態渲染抓不到資料的問題
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.tainex.com.tw/events"
    }

    today = datetime.now()
    # 自動抓取當月與次月
    target_months = [today, today + relativedelta(months=1)]
    
    all_events = []
    seen_names = set()

    for target_date in target_months:
        year_str = str(target_date.year)
        month_str = f"{target_date.month:02d}"
        
        # 官方展覽行事曆 API 節點
        api_url = f"https://www.tainex.com.tw/api/v1/events?year={year_str}&month={month_str}&lang=zh-TW"
        
        try:
            res = requests.get(api_url, headers=headers, timeout=15)
            if res.status_code == 200:
                json_data = res.json()
                
                # 兼容 API 回傳結構 (可能是 data 或 events 陣列)
                raw_items = []
                if isinstance(json_data, dict):
                    raw_items = json_data.get("data") or json_data.get("events") or json_data.get("result") or []
                elif isinstance(json_data, list):
                    raw_items = json_data

                for item in raw_items:
                    name = item.get("title") or item.get("name") or item.get("activityName") or ""
                    start_date = item.get("startDate") or item.get("start_date") or item.get("beginDate") or ""
                    end_date = item.get("endDate") or item.get("end_date") or ""
                    link = item.get("url") or item.get("link") or "https://www.tainex.com.tw/events"

                    if name and start_date:
                        clean_name = name.strip()
                        if clean_name not in seen_names:
                            seen_names.add(clean_name)
                            all_events.append({
                                "name": clean_name,
                                "startDate": start_date[:10],
                                "endDate": end_date[:10] if end_date else start_date[:10],
                                "icon": "🎪",
                                "url": link if link.startswith("http") else f"https://www.tainex.com.tw{link}"
                            })
            else:
                print(f"API 回傳異常代碼 [{res.status_code}]")
        except Exception as err:
            print(f"[{year_str}-{month_str}] 請求 API 時發生錯誤: {err}")

    # 依展覽日期排序
    all_events.sort(key=lambda x: x["startDate"])

    # 寫入 events.json
    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)

    print(f"抓取完成！成功取得 {len(all_events)} 筆展覽資料並寫入 events.json")

if __name__ == "__main__":
    fetch_tainex_api_events()
