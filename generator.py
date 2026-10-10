import json
from datetime import datetime, timezone, timedelta
import urllib.request

# Cấu hình API Bia Ôm TV
API_URL = "https://cmsx5.mtbkta.xyz/api/live-streams?limit=50&actionStatus=live&actionStatus=scheduled&brandName=all"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 5ce148fe3b92694d818c1677f43d9473f1b7a76b4632417e1de97ede6bc4bd70",
    "User-Agent": "Mozilla/5.0"
}

def fetch_data():
    req = urllib.request.Request(API_URL, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data.get("data", [])
    except Exception as e:
        print(f"Lỗi khi gọi API: {e}")
    return []

def generate_m3u():
    items = fetch_data()
    
    # Thiết lập thời gian hiện tại theo giờ Việt Nam (UTC+7)
    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    today_str = now_vn.strftime('%Y-%m-%d')
    tomorrow_str = (now_vn + timedelta(days=1)).strftime('%Y-%m-%d')

    parsed_matches = []

    for item in items:
        match_info = item.get("match", {})
        if not match_info:
            continue

        starting_at = match_info.get("starting_at") # Dạng ISO: 2026-10-10T08:35:00+00:00
        if not starting_at:
            continue

        # Chuyển đổi sang múi giờ Việt Nam (UTC+7)
        dt_utc = datetime.fromisoformat(starting_at.replace("Z", "+00:00"))
        dt_vn = dt_utc.astimezone(vn_tz)
        match_date_key = dt_vn.strftime('%Y-%m-%d')
        
        # Chỉ lấy danh sách trận đấu hôm nay và ngày mai
        if match_date_key not in [today_str, tomorrow_str]:
            continue

        # Lưu lại đối tượng chứa đầy đủ thông tin + timestamp thời gian để sắp xếp
        parsed_matches.append({
            "datetime_vn": dt_vn,
            "home_team": match_info.get("home", {}).get("name", "Home"),
            "away_team": match_info.get("away", {}).get("name", "Away"),
            "home_logo": match_info.get("home", {}).get("image_url", ""),
            "blv_name": item.get("streamer", {}).get("displayName", "Chưa rõ").strip(),
            "stream_url": item.get("streamUrl", ""),        # FLV
            "mobile_stream_url": item.get("mobileStreamUrl", "") # HLS (.m3u8)
        })

    # SẮP XẾP TĂNG DẦN THEO THỜI GIAN (Trận sớm hơn sẽ lên trước)
    parsed_matches.sort(key=lambda x: x["datetime_vn"])

    # Tạo nội dung M3U
    m3u_content = '#EXTM3U x-tvg-url=""\n'

    for match in parsed_matches:
        dt_vn = match["datetime_vn"]
        time_formatted = dt_vn.strftime('%H:%M')
        date_formatted = dt_vn.strftime('%d/%m')

        home_team = match["home_team"]
        away_team = match["away_team"]
        home_logo = match["home_logo"]
        blv_name = match["blv_name"]
        
        match_title = f"{time_formatted} {date_formatted} ⚽ {home_team} vs {away_team} ({blv_name})"

        # 1. Luồng FLV
        if match["stream_url"]:
            title_flv = f"{match_title} [flv]"
            m3u_content += f'#EXTINF:-1 tvg-id="" tvg-name="{home_team} vs {away_team}" tvg-logo="{home_logo}" group-title="Bia Ôm TV",{title_flv}\n'
            m3u_content += f'{match["stream_url"]}\n'

        # 2. Luồng HLS
        if match["mobile_stream_url"]:
            title_hls = f"{match_title} [hls]"
            m3u_content += f'#EXTINF:-1 tvg-id="" tvg-name="{home_team} vs {away_team}" tvg-logo="{home_logo}" group-title="Bia Ôm TV",{title_hls}\n'
            m3u_content += f'{match["mobile_stream_url"]}\n'

    with open("biaom_live.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print("Đã sắp xếp danh sách trận đấu theo thứ tự thời gian tăng dần thành công!")

if __name__ == "__main__":
    generate_m3u()
    
