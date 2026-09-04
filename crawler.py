import json
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
from bs4 import BeautifulSoup

def fetch_tainex_two_months():
    """
    純動態抓取南港展覽館當月與次月的所有展覽活動
    完全不依賴寫死資料，終身全自動更新
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    today = datetime.now()
    # 鎖定 2 個月份：當月與次月
    target_months = [today, today + relativedelta(months=1)]
    
    all_events = []
    seen_names = set()

    for target_date in target_months:
        year_str = str(target_date.year)
        month_str = f"{target_date.month:02d}"
        
        url = f"https://www.tainex.com.tw/events?year={year_str}&month={month_str}"
        
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # 選取所有展覽行或卡片區塊
                cards = soup.select(".event-card, .event-item, .exhibition-item, tr, .calendar-event")
                
                for card in cards:
                    text = card.get_text(separator=" ", strip=True)
                    
                    # 匹配日期區間格式（例如 2026/09/02 - 2026/09/04、2026.09.02 ~ 09.04、2026-09-02 至 2026-09-04）
                    date_match = re.search(
                        r"(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})\s*[-~至]\s*(?:(\d{4})[./\-])?(\d{1,2})[./\-](\d{1,2})",
                        text
                    )
                    
                    if date_match:
                        title_el = card.select_one(".title, .event-title, h3, h4, strong, a")
                        name = title_el.get_text(strip=True) if title_el else text.split()[0]
                        
                        link_el = card.select_one("a")
                        href = link_el.get("href") if link_el else "https://www.tainex.com.tw/events"
                        if href and not href.startswith("http"):
                            href = f"https://www.tainex.com.tw{href}"

                        # 解析日期並補零正規化為 YYYY-MM-DD
                        groups = date_match.groups()
                        s_year = groups[0]
                        s_month = groups[1].zfill(2)
                        s_day = groups[2].zfill(2)
                        
                        e_year = groups[3] if groups[3] else s_year
                        e_month = groups[4].zfill(2)
                        e_day = groups[5].zfill(2)
                        
                        start_date = f"{s_year}-{s_month}-{s_day}"
                        end_date = f"{e_year}-{e_month}-{e_day}"

                        clean_name = name.strip()
                        if len(clean_name) >= 3 and clean_name not in seen_names:
                            seen_names.add(clean_name)
                            all_events.append({
                                "name": clean_name,
                                "startDate": start_date,
                                "endDate": end_date,
                                "icon": "🎪",
                                "url": href
                            })
        except Exception as err:
            print(f"[{year_str}-{month_str}] 連線抓取失敗: {err}")

    # 依展期開始日由近至遠排序
    all_events.sort(key=lambda x: x["startDate"])

    # 直接覆寫產出最新的 events.json（抓到幾筆就存幾筆，不塞入任何寫死假資料）
    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)

    print(f"更新成功！共計抓取並寫入 {len(all_events)} 筆最新展覽資料。")

if __name__ == "__main__":
    fetch_tainex_two_months()
