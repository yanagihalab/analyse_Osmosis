import requests
import re
import pandas as pd
from datetime import datetime

# RPCエンドポイント
BLOCK_HEADER_URL = "https://rpc.lavenderfive.com/osmosis/block?height="

# CSVファイルからブロック高さを取得
def load_block_heights(csv_filename):
    """CSVファイルからブロック高さを取得する"""
    df = pd.read_csv(csv_filename)
    return df[["send_height", "ack_height"]].dropna().values.flatten()

# ブロックタイムスタンプを取得
def fetch_block_timestamp(height):
    """指定されたブロックのタイムスタンプを取得"""
    try:
        response = requests.get(BLOCK_HEADER_URL + str(height))
        if response.status_code == 200:
            block_data = response.json()
            timestamp = block_data["result"]["block"]["header"]["time"]
            timestamp = timestamp[:26]  # ナノ秒をマイクロ秒 (6桁) に切り詰める
            dt = datetime.fromisoformat(timestamp)
            print(f"Successfully fetched timestamp for block {height}: {dt}")  # ✅ 正常時のログ
            return dt
        else:
            print(f"Failed to fetch timestamp for block {height}")
    except Exception as e:
        print(f"Error fetching timestamp for block {height}: {e}")
    return None


# CSVからブロック情報をロード
target_csv = "ibc_packet_delay_analysis.csv"
block_heights = load_block_heights(target_csv)

# 各ブロックのタイムスタンプを取得
timestamps = {height: fetch_block_timestamp(height) for height in block_heights}

# 差分を計算
df = pd.read_csv(target_csv)
df["send_time"] = df["send_height"].map(timestamps)
df["ack_time"] = df["ack_height"].map(timestamps)
df["time_delay_sec"] = (df["ack_time"] - df["send_time"]).dt.total_seconds()

# 結果を保存
output_csv = "ibc_time_delay_analysis.csv"
df.to_csv(output_csv, index=False)
print(f"CSV file saved: {output_csv}")
