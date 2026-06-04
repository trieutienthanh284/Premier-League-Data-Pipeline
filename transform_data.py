import json
import pandas as pd

with open('premier_league_matches_raw.json', 'r', encoding = 'utf-8') as json_file:
    data = json.load(json_file)

matches = data.get("matches", [])
cleaned_matches = []

for match in matches:
    match_info = {
        "match_id": match.get("id"),
        "match_date": match.get("utcDate"),
        "status": match.get("status"),
        "matchday": match.get("matchday"),
        "home_team": match.get("homeTeam", {}).get("shortName"),
        "away_team": match.get("awayTeam", {}).get("shortName"),
        "home_score": match.get("score", {}).get("fullTime", {}).get("home"),
        "away_score": match.get("score", {}).get("fullTime", {}).get("away")
    }
    cleaned_matches.append(match_info)

df = pd.DataFrame(cleaned_matches)
df['match_date'] = pd.to_datetime(df['match_date'])

output_file = 'premier_league_matches_transformed.csv'
df.to_csv(output_file, index=False, encoding='utf-8')

print('Hoàn thành xuất dữ liệu')