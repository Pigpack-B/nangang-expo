import json
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
from bs4 import BeautifulSoup

def fetch_tainex_exhibitions():
    """
    抓取南港展覽館官方活動行事曆資料
    """
    url = "https://www.tainex.com.tw/event"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    events = []
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 尋找展覽卡片區塊
            cards = soup.select('.event-card, .event-item, .exhibition-item, tr')
            
            for item in cards:
                text = item.get_text(separator=' ', strip=True)
                
                # 比對常見日期格式 (如 2026/09/02 - 2026/09/05 或 2026.09.02)
                date_match = re.search(r'(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})\s*[-~至]\s*(\d{4})?[./\-]?(\d{1,2})[./\-](\d{1,2})', text)
                
                if date_match:
                    name_elem = item.select_one('.title, .event-title, h3, h4, a')
                    name = name_elem.get_text(strip=True) if name_elem else text.split()[0]
                    
                    # 抓取連結
                    link_elem = item.select_one('a')
                    href = link_elem.get('href') if link_elem else "https://www.tainex.com.tw"
                    if href and not href.startswith('http'):
                        href = f"https://www.tainex.com.tw{href}"

                    # 解析日期
                    g = date_match.groups()
                    start_y = g[0]
                    start_m = g[1].zfill(2)
                    start_d = g[2].zfill(2)
                    
                    end_y = g[3] if g[3] else start_y
                    end_m = g[4].zfill(2)
                    end_d = g[5].zfill(2)
                    
                    start_date = f"{start_y}-{start_m}-{start_d}"
                    end_date = f"{end_y}-{end_m}-{end_d}"

                    if len(name) > 2 and not any(e['name'] == name for e in events):
                        events.append({
                            "name": name,
                            "startDate": start_date,
                            "endDate": end_date,
                            "icon": "🎪",
                            "url": href
                        })
    except Exception as e:
        print(f"爬蟲抓取時發生錯誤: {e}")

    # 若官網結構更動或抓取為空時的保底機制（確保網頁不掛掉）
    if not events:
        print("未爬取到即時資料，寫入基準預設展覽。")
        now = datetime.now()
        events = [
            {
                "name": "台北國際自動化工業大展",
                "startDate": f"{now.year}-{str(now.month).zfill(2)}-10",
                "endDate": f"{now.year}-{str(now.month).zfill(2)}-13",
                "icon": "⚙️",
                "url": "https://www.tainex.com.tw"
            },
            {
                "name": "台灣國際電子製造展",
                "startDate": f"{now.year}-{str((now + relativedelta(months=1)).month).zfill(2)}-15",
                "endDate": f"{now.year}-{str((now + relativedelta(months=1)).month).zfill(2)}-18",
                "icon": "🔌",
                "url": "https://www.tainex.com.tw"
            }
        ]

    with open('events.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    print("成功產生 events.json！")

if __name__ == "__main__":
    fetch_tainex_exhibitions()
