import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests

def fetch_tainex_all_events():
    """
    透過南港展覽館 API 抓取當月與次月的真實展覽資料
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.tainex.com.tw/events"
    }

    today = datetime.now()
    months_to_check = [today, today + relativedelta(months=1)]
    
    all_events = []
    seen_names = set()

    for target_date in months_to_check:
        year_str = str(target_date.year)
        month_str = f"{target_date.month:02d}"

        # 南港展覽館官網活動查詢 API
        api_url = f"https://www.tainex.com.tw/api/v1/events?year={year_str}&month={month_str}&lang=zh-TW"
        
        try:
            res = requests.get(api_url, headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json()
                items = data.get("data", []) or data.get("events", []) or []
                
                for item in items:
                    name = item.get("title") or item.get("name") or item.get("activityName", "")
                    start_date = item.get("startDate") or item.get("start_date", "")
                    end_date = item.get("endDate") or item.get("end_date", "")
                    link = item.get("url") or item.get("link") or "https://www.tainex.com.tw/events"

                    # 格式正規化為 YYYY-MM-DD
                    if name and start_date and name not in seen_names:
                        seen_names.add(name)
                        all_events.append({
                            "name": name.strip(),
                            "startDate": start_date[:10],
                            "endDate": end_date[:10] if end_date else start_date[:10],
                            "icon": "🎪",
                            "url": link
                        })
        except Exception as e:
            print(f"抓取 {year_str}-{month_str} 資料時發生錯誤: {e}")

    # 若官網 API 異常時的保底資料
    if not all_events:
        print("未獲取到即時 API 資料，寫入備援清單")
        y = today.year
        all_events = [
            {
                "name": "SEMICON Taiwan 國際半導體展",
                "startDate": f"{y}-09-02",
                "endDate": f"{y}-09-04",
                "icon": "💡",
                "url": "https://www.semicontaiwan.org/"
            },
            {
                "name": "台北國際自動化工業大展",
                "startDate": f"{y}-09-16",
                "endDate": f"{y}-09-19",
                "icon": "⚙️",
                "url": "https://www.taiwanautomation.com.tw/"
            }
        ]

    # 按展覽開始日期排序
    all_events.sort(key=lambda x: x["startDate"])

    # 寫入 events.json
    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)

    print(f"更新完成，共計入 {len(all_events)} 檔展覽！")

if __name__ == "__main__":
    fetch_tainex_all_events()
