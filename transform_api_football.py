import json
import pandas as pd
import yaml
import os

# 1. Đọc cấu hình Nguồn
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Định nghĩa lại đường dẫn theo cấu trúc folder cô lập mới của bạn
raw_base_file = "data_epl/api_football_raw.json"
raw_stats_file = "data_epl/api_football_statistics.json"
clean_filename = "data_epl/api_football_clean.csv"

# ==========================================
# BƯỚC 1: XỬ LÝ DỮ LIỆU CƠ BẢN + THÊM LEAGUE_NAME
# ==========================================
if not os.path.exists(raw_base_file):
    print(f"Thất bại: Không tìm thấy file thô tại {raw_base_file}. Bạn đã di chuyển file vào data_epl chưa?")
    exit()

with open(raw_base_file, "r", encoding="utf-8") as file:
    raw_base_data = json.load(file)

base_matches = raw_base_data.get("response", [])
base_list = []

for match in base_matches:
    fixture = match.get("fixture", {})
    teams = match.get("teams", {})
    goals = match.get("goals", {})

    base_list.append({
        "match_id": fixture.get("id"),
        "league_name": "Premier League",
        "match_date": fixture.get("date"),
        "home_team": teams.get("home", {}).get("name"),
        "away_team": teams.get("away", {}).get("name"),
        "home_score": goals.get("home"),
        "away_score": goals.get("away"),
        "referee": fixture.get("referee"),
        "data_source": "api-football"
    })

df_base = pd.DataFrame(base_list)
df_base['match_date'] = pd.to_datetime(df_base['match_date'])

# ==========================================
# BƯỚC 2: XỬ LÝ VÀ GỘP DỮ LIỆU THỐNG KÊ
# ==========================================
try:
    with open(raw_stats_file, "r", encoding="utf-8") as f:
        raw_stats_data = json.load(f)
except FileNotFoundError:
    raw_stats_data = []

if raw_stats_data:
    print("Đang gộp thêm mỏ vàng dữ liệu thống kê chuyên sâu...")
    flattened_stats = []

    for match in raw_stats_data:
        match_id = match.get("fixture_id")
        match_stats = match.get("statistics", [])

        if len(match_stats) < 2:
            continue

        home_data = match_stats[0].get("statistics", [])
        away_data = match_stats[1].get("statistics", [])

        row = {"match_id": match_id}
        for stat in home_data:
            stat_type = str(stat["type"]).replace(" ", "_").lower()
            row[f"home_{stat_type}"] = stat["value"]

        for stat in away_data:
            stat_type = str(stat["type"]).replace(" ", "_").lower()
            row[f"away_{stat_type}"] = stat["value"]

        flattened_stats.append(row)

    df_stats = pd.DataFrame(flattened_stats)
    df_api_complete = pd.merge(df_base, df_stats, on="match_id", how="left")

    # ==========================================
    # BƯỚC 3: CHUẨN HÓA KIỂU DỮ LIỆU
    # ==========================================
    print("Đang dọn dẹp và chuẩn hóa kiểu dữ liệu...")
    float_columns = ['home_expected_goals', 'away_expected_goals', 'home_goals_prevented', 'away_goals_prevented']
    pct_columns = ['home_ball_possession', 'away_ball_possession', 'home_passes_%', 'away_passes_%']
    # Đã bổ sung 'league_name' vào danh sách loại trừ để Pandas không ép kiểu nhầm cột này
    exclude_from_int = ['match_id', 'league_name', 'match_date', 'home_team', 'away_team', 'referee',
                        'data_source'] + float_columns + pct_columns

    int_columns = [col for col in df_api_complete.columns if col not in exclude_from_int]

    for col in int_columns:
        df_api_complete[col] = pd.to_numeric(df_api_complete[col], errors='coerce').fillna(0).astype(int)

    for col in pct_columns:
        if col in df_api_complete.columns:
            df_api_complete[col] = df_api_complete[col].astype(str).str.replace('%', '', regex=False)
            df_api_complete[col] = pd.to_numeric(df_api_complete[col], errors='coerce').fillna(0).astype(int)

    for col in float_columns:
        if col in df_api_complete.columns:
            df_api_complete[col] = pd.to_numeric(df_api_complete[col], errors='coerce').fillna(0.0).astype(float)

    final_df = df_api_complete
else:
    print("Chưa tìm thấy file thống kê nâng cao, chỉ xuất dữ liệu cơ bản.")
    final_df = df_base

# 4. Xuất xưởng vào folder mới
final_df.to_csv(clean_filename, index=False, encoding="utf-8-sig")
print(f"Đã xử lý xong siêu bảng API-Football (Đã có cột league_name).")
print(f"Lưu tại: {clean_filename}")