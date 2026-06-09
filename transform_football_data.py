import json
import pandas as pd
import yaml

# 1. Đọc cấu hình từ config
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

source_config = config['source_football_data_org']
raw_filename = source_config['output_file']
# Đã sửa: Lưu chuẩn vào thư mục data/
clean_filename = "data/football_data_clean.csv"

# 2. Đọc JSON thô
with open(raw_filename, "r", encoding="utf-8") as file:
    raw_data = json.load(file)

matches = raw_data.get("matches", [])
cleaned_matches = []

# 3. Logic bóc tách với các chốt chặn an toàn
for match in matches:
    referee_list = match.get("referees", [])
    main_referee = referee_list[0].get("name") if len(referee_list) > 0 else None

    match_info = {
        "fd_match_id": match.get("id"), # Đổi tên để tránh xung đột với API-Football
        "match_date": match.get("utcDate"),
        # Thêm fallback lấy tên dài nếu tên ngắn bị thiếu
        "home_team": match.get("homeTeam", {}).get("shortName") or match.get("homeTeam", {}).get("name"),
        "away_team": match.get("awayTeam", {}).get("shortName") or match.get("awayTeam", {}).get("name"),
        "home_score": match.get("score", {}).get("fullTime", {}).get("home"),
        "away_score": match.get("score", {}).get("fullTime", {}).get("away"),
        "referee": main_referee,
        "data_source": "football-data.org"
    }
    cleaned_matches.append(match_info)

# 4. Xuất xưởng
df = pd.DataFrame(cleaned_matches)
df['match_date'] = pd.to_datetime(df['match_date'])
df.to_csv(clean_filename, index=False, encoding="utf-8-sig")

print(f"🚀 Đã xử lý xong {len(df)} trận từ Nguồn 1.")
print(f"📁 Lưu an toàn tại: {clean_filename}")