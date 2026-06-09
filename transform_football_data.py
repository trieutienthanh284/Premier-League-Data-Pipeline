import json
import pandas as pd
import yaml
import os

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Đổi đường dẫn trỏ vào data_epl
raw_filename = "data_epl/football_data_raw.json"
clean_filename = "data_epl/football_data_clean.csv"

if not os.path.exists(raw_filename):
    print(f"Không tìm thấy file {raw_filename}. Bạn đã chuyển file vào data_epl chưa?")
    exit()

with open(raw_filename, "r", encoding="utf-8") as file:
    raw_data = json.load(file)

matches = raw_data.get("matches", [])
cleaned_matches = []

for match in matches:
    referee_list = match.get("referees", [])
    main_referee = referee_list[0].get("name") if len(referee_list) > 0 else None

    match_info = {
        "fd_match_id": match.get("id"),
        "match_date": match.get("utcDate"),
        "home_team": match.get("homeTeam", {}).get("shortName") or match.get("homeTeam", {}).get("name"),
        "away_team": match.get("awayTeam", {}).get("shortName") or match.get("awayTeam", {}).get("name"),
        "home_score": match.get("score", {}).get("fullTime", {}).get("home"),
        "away_score": match.get("score", {}).get("fullTime", {}).get("away"),
        "referee": main_referee,
        "data_source": "football-data.org"
    }
    cleaned_matches.append(match_info)

df = pd.DataFrame(cleaned_matches)
df['match_date'] = pd.to_datetime(df['match_date'])
df.to_csv(clean_filename, index=False, encoding="utf-8-sig")

print(f"Đã xử lý xong Nguồn 2. Lưu tại: {clean_filename}")