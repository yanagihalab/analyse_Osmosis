import requests
import time
import csv
import os

URL = "https://cosmos-rpc.quickapi.com/unconfirmed_txs"
CSV_FILE = "unconfirmed_txs.csv"

# CSVファイルのヘッダーを作成（初回のみ）
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "n_txs", "total", "total_bytes"])

def fetch_and_save_data():
    while True:
        try:
            response = requests.get(URL)
            if response.status_code == 200:
                data = response.json()

                # レスポンスデータを確認
                print("Received JSON:", data)

                # 必要なデータを取得
                result = data.get("result")
                if not result:
                    print("No 'result' field in response")
                    continue

                n_txs = result.get("n_txs", "0")
                total = result.get("total", "0")
                total_bytes = result.get("total_bytes", "0")

                # CSVにデータを追記
                with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), n_txs, total, total_bytes])

                print(f"Saved: n_txs={n_txs}, total={total}, total_bytes={total_bytes}")

            else:
                print(f"Error: {response.status_code}")

        except Exception as e:
            print(f"Request failed: {e}")

        time.sleep(3)  # 3秒ごとにデータ取得

if __name__ == "__main__":
    fetch_and_save_data()
