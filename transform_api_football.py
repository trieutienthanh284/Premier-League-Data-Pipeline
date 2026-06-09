import json
import pandas as pd
import yaml

# 1. Đọc cấu hình Nguồn
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

source_config = config['source_api_football']
raw_base_file = source_config['output_file']

# Khai báo thêm file chứa thống kê chuyên sâu và chỉnh lại đường dẫn đầu ra
raw_stats_file = "data/api_football_statistics.json"
clean_filename = "data/api_football_clean.csv"

# ==========================================
# BƯỚC 1: XỬ LÝ DỮ LIỆU CƠ BẢN
# ==========================================
with open(raw_base_file, "r", encoding="utf-8") as file:
    raw_base_data = json.load(file)

base_matches = raw_base_data.get("response", [])
base_list = []

for match in base_matches:
    fixture = match.get("fixture", {})
    teams = match.get("teams", {})
    goals = match.get("goals", {})
    score = match.get("score", {})

    base_list.append({
        "match_id": fixture.get("id"),
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
# BƯỚC 2: XỬ LÝ VÀ GỘP DỮ LIỆU THỐNG KÊ (NẾU CÓ)
# ==========================================
try:
    with open(raw_stats_file, "r", encoding="utf-8") as f:
        raw_stats_data = json.load(f)
except FileNotFoundError:
    raw_stats_data = []

if raw_stats_data:
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

    # Nối 2 bảng bằng phương pháp Left Join (Bảo toàn 380 trận cơ bản dù thống kê có bị thiếu)
    df_api_complete = pd.merge(df_base, df_stats, on="match_id", how="left")

    # ==========================================
    # BƯỚC 3: CHUẨN HÓA KIỂU DỮ LIỆU
    # ==========================================
    print("Đang dọn dẹp và chuẩn hóa kiểu dữ liệu...")
    float_columns = ['home_expected_goals', 'away_expected_goals', 'home_goals_prevented', 'away_goals_prevented']
    pct_columns = ['home_ball_possession', 'away_ball_possession', 'home_passes_%', 'away_passes_%']
    exclude_from_int = ['match_id', 'match_date', 'home_team', 'away_team', 'referee',
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
    print("⚠Chưa tìm thấy file thống kê, chỉ xuất dữ liệu cơ bản.")
    final_df = df_base

# 4. Xuất xưởng
final_df.to_csv(clean_filename, index=False, encoding="utf-8-sig")
print(f"Đã xử lý xong siêu bảng API-Football. Lưu an toàn tại: {clean_filename}")