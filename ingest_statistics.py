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
stats_output_file = source_config['stats_output_file']

BATCH_SIZE = 95

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
    print(f"❌ Lỗi: Không tìm thấy {base_raw_file}")
    exit()

os.makedirs(os.path.dirname(stats_output_file), exist_ok=True)

# 4. Kiểm tra trạng thái
existing_stats = []
if os.path.exists(stats_output_file):
    with open(stats_output_file, "r", encoding="utf-8") as f:
        try:
            existing_stats = json.load(f)
        except json.JSONDecodeError:
            existing_stats = []

processed_ids = [item["fixture_id"] for item in existing_stats]
unprocessed_matches = [m for m in all_matches if m['fixture']['id'] not in processed_ids]

print(f"Tổng số trận: {len(all_matches)}")
print(f"Đã xử lý: {len(processed_ids)} trận")
print(f"Còn lại: {len(unprocessed_matches)} trận")

if not unprocessed_matches:
    print("🎉 Tuyệt vời! Đã thu thập đủ thống kê cho toàn bộ mùa giải.")
    exit()

matches_to_process = unprocessed_matches[:BATCH_SIZE]
print(f"🚀 Bắt đầu lấy dữ liệu cho {len(matches_to_process)} trận hôm nay...\n")

# 5. Vòng lặp gọi API với cơ chế chống rớt mạng
for index, match in enumerate(matches_to_process):
    match_id = match['fixture']['id']
    print(f"[{index + 1}/{len(matches_to_process)}] Đang lấy ID: {match_id}...", end=" ")

    stats_url = f"{base_url}/fixtures/statistics"
    querystring = {"fixture": match_id}

    # BỌC ÁO GIÁP: Thử gọi tối đa 3 lần cho mỗi trận
    max_retries = 3
    success = False

    for attempt in range(max_retries):
        try:
            # Thêm tham số timeout (15 giây) để tránh bị treo vĩnh viễn
            response = requests.get(stats_url, headers=headers, params=querystring, timeout=15)

            if response.status_code == 200:
                stats_data = response.json()

                if stats_data.get("errors"):
                    print(f"⚠️ Bị chặn! Lỗi: {stats_data['errors']}")
                    success = True  # Chặn cố tình từ máy chủ, không retry nữa
                    break

                existing_stats.append({
                    "fixture_id": match_id,
                    "statistics": stats_data.get("response", [])
                })

                with open(stats_output_file, "w", encoding="utf-8") as file:
                    json.dump(existing_stats, file, ensure_ascii=False, indent=4)

                print("Thành công!")
                success = True
                break  # Thoát vòng lặp retry vì đã thành công
            else:
                print(f" Lỗi HTTP {response.status_code}. Thử lại...")

        except requests.exceptions.RequestException as e:
            # Bắt toàn bộ các lỗi liên quan đến rớt mạng, timeout, cúp kết nối
            print(f"Rớt mạng (Lần {attempt + 1}/{max_retries}). Đang thử lại...", end=" ")
            time.sleep(5)  # Đợi 5 giây cho mạng ổn định rồi thử lại

    if not success:
        print(f"❌ Thất bại sau 3 lần thử. Bỏ qua trận này để tránh sập hệ thống.")
        # Bạn có thể break nếu muốn dừng hẳn, hoặc continue để sang trận tiếp theo.
        # Ở đây dùng continue để hệ thống kiên cường chạy tiếp.
        continue

    # Nghỉ 10s để tránh bị khóa IP
    time.sleep(10)

print("\n✅ Hoàn thành công việc cào dữ liệu hôm nay! Hãy quay lại vào 7h00 sáng mai để chạy tiếp.")