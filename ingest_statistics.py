import json
import requests
import os
import yaml
import time
from dotenv import load_dotenv

# 1. Đọc cấu hình
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

source_config = config['source_api_football']
base_url = source_config['base_url']
base_raw_file = source_config['output_file']

# File lưu trữ dữ liệu thống kê
stats_output_file = "data/api_football_statistics.json"
BATCH_SIZE = 95  # Chạy 95 trận 1 ngày để đảm bảo an toàn cho giới hạn 100

# 2. Tải khóa bí mật
load_dotenv()
API_KEY = os.getenv("API_FOOTBALL_KEY")
headers = {'x-apisports-key': API_KEY}

# 3. Đọc danh sách 380 trận đấu gốc
try:
    with open(base_raw_file, "r", encoding="utf-8") as f:
        base_data = json.load(f)
        all_matches = base_data.get("response", [])
except FileNotFoundError:
    print(f"Lỗi: Không tìm thấy {base_raw_file}")
    exit()

# 4. Kiểm tra trạng thái
existing_stats = []
if os.path.exists(stats_output_file):
    with open(stats_output_file, "r", encoding="utf-8") as f:
        try:
            existing_stats = json.load(f)
        except json.JSONDecodeError:
            existing_stats = []

# Lọc ra danh sách các ID đã xử lý
processed_ids = [item["fixture_id"] for item in existing_stats]

# Tìm các trận chưa xử lý
unprocessed_matches = [m for m in all_matches if m['fixture']['id'] not in processed_ids]

print(f"Tổng số trận: {len(all_matches)}")
print(f"Đã xử lý: {len(processed_ids)} trận")
print(f"Còn lại: {len(unprocessed_matches)} trận")

if not unprocessed_matches:
    print("Tuyệt vời! Đã thu thập đủ thống kê cho toàn bộ mùa giải.")
    exit()

# Lấy mẻ dữ liệu cho ngày hôm nay
matches_to_process = unprocessed_matches[:BATCH_SIZE]
print(f"Bắt đầu lấy dữ liệu cho {len(matches_to_process)} trận hôm nay...\n")

# 5. Vòng lặp gọi API
for index, match in enumerate(matches_to_process):
    match_id = match['fixture']['id']
    print(f"[{index + 1}/{len(matches_to_process)}] Đang lấy ID: {match_id}...", end=" ")

    stats_url = f"{base_url}/fixtures/statistics"
    querystring = {"fixture": match_id}

    response = requests.get(stats_url, headers=headers, params=querystring)

    if response.status_code == 200:
        stats_data = response.json()

        # Nếu máy chủ báo lỗi vượt giới hạn (Rate Limit) ở trong thân JSON
        if stats_data.get("errors"):
            print(f"Bị chặn! Lỗi: {stats_data['errors']}")
            break  # Dừng toàn bộ chương trình ngay lập tức

        # Lưu vào danh sách tạm
        existing_stats.append({
            "fixture_id": match_id,
            "statistics": stats_data.get("response", [])
        })

        # Lưu vào ổ cứng ngay sao mỗi trận
        with open(stats_output_file, "w", encoding="utf-8") as file:
            json.dump(existing_stats, file, ensure_ascii=False, indent=4)

        print("Thành công!")

        # Nghỉ 10s để tránh bị khóa IP
        time.sleep(10)
    else:
        print(f"Lỗi HTTP {response.status_code}. Dừng chương trình.")
        break

print("\nHoàn thành công việc cào dữ liệu hôm nay! Hãy quay lại vào 7h00 sáng mai để chạy tiếp.")