import json
import requests
import os
import yaml
from dotenv import load_dotenv

# 1. Đọc cấu hình nguồn mới
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

source_config = config['source_api_football']

# 2. Tải khóa bí mật mới từ .env
load_dotenv()
API_KEY = os.getenv("API_FOOTBALL_KEY")
if not API_KEY:
    raise ValueError("Chưa tìm thấy API_FOOTBALL_KEY trong file .env!")

# 3. Lắp ráp URL và tham số
url = f"{source_config['base_url']}/{source_config['endpoint']}"
querystring = {"league": source_config['league_id'], "season": source_config['season']}
raw_filename = source_config['output_file']

headers = {'x-apisports-key': API_KEY}

print(f"Đang kết nối [Nguồn 2: API-Football] để kéo dữ liệu chi tiết...")

# 4. Gửi yêu cầu và lưu file
response = requests.get(url, headers=headers, params=querystring)

if response.status_code == 200:
    raw_data = response.json()

    # BỔ SUNG QUAN TRỌNG: Tự động kiểm tra và tạo thư mục (ví dụ: data_laliga) nếu chưa tồn tại
    os.makedirs(os.path.dirname(raw_filename), exist_ok=True)

    with open(raw_filename, "w", encoding="utf-8") as file:
        json.dump(raw_data, file, ensure_ascii=False, indent=4)
    print(f"Hoàn tất Nguồn 2! Đã lưu kho dữ liệu siêu chi tiết vào file: {raw_filename}")
else:
    print(f"Lỗi Nguồn 2 - HTTP: {response.status_code} | Chi tiết: {response.text}")