import requests
import re
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# RPCエンドポイント
BLOCK_HEADER_URL = "https://rpc.lavenderfive.com/osmosis/block?height="

# フィルターモードを選択
filter_mode = input("フィルターを適用しますか？ (yes/no): ").strip().lower()
apply_filter = filter_mode == "yes"

# CSVファイルからブロック高さを取得
def load_block_heights(csv_filename, target_channel=None):
    """CSVファイルから指定したチャネルのブロック高さを取得する"""
    df = pd.read_csv(csv_filename)
    if target_channel and apply_filter:
        df = df[df["channel_id"] == f"channel-{target_channel}"]  # 指定チャネルのデータのみ抽出
    return df["send_height"].dropna().tolist() + df["ack_height"].dropna().tolist()

# ブロックタイムスタンプを取得
def fetch_block_timestamp(height):
    """指定されたブロックのタイムスタンプを取得"""
    try:
        response = requests.get(BLOCK_HEADER_URL + str(height))
        if response.status_code == 200:
            block_data = response.json()
            timestamp = block_data["result"]["block"]["header"]["time"]
            timestamp = timestamp[:26]  # ナノ秒をマイクロ秒に調整
            dt = datetime.fromisoformat(timestamp)
            print(f"Successfully fetched timestamp for block {height}: {dt}")
            return dt
        else:
            print(f"Failed to fetch timestamp for block {height}")
    except Exception as e:
        print(f"Error fetching timestamp for block {height}: {e}")
    return None

# チャネルを指定してデータを取得
base_file = "ibc_packet_delay_analysis_30159500-30190534"
target_csv = base_file + ".csv"
df = pd.read_csv(target_csv)
available_channels = sorted(set(df["channel_id"].str.replace("channel-", "").astype(int)))
print("利用可能なチャネルID:", ", ".join(map(str, available_channels)))

if apply_filter:
    target_channel = input("対象のチャネル番号を入力してください (例: 0, 122, 208): ").strip()
    if target_channel not in map(str, available_channels):
        print("無効なチャネルIDが入力されました。利用可能なチャネルを確認してください。")
        exit()
else:
    target_channel = None

block_heights = load_block_heights(target_csv, target_channel)

# 各ブロックのタイムスタンプを取得
timestamps = {height: fetch_block_timestamp(height) for height in block_heights}

# データのフィルタリング
if apply_filter:
    df = df[df["channel_id"] == f"channel-{target_channel}"]
filtered_ibc_count = len(df)
print(f"Filtered IBC transactions count: {filtered_ibc_count}")

df["send_time"] = df["send_height"].map(timestamps)
df["ack_time"] = df["ack_height"].map(timestamps)
df["time_delay_sec"] = (df["ack_time"] - df["send_time"]).dt.total_seconds()
df["block_delay"] = df["ack_height"] - df["send_height"]

# 結果を保存
output_csv = f"ibc_time_delay_analysis_{target_channel if apply_filter else 'all'}.csv"
df.to_csv(output_csv, index=False)
print(f"CSV file saved: {output_csv}")

# time_delay_secの分布図を作成
plt.figure(figsize=(10, 6))
plt.hist(df["time_delay_sec"].dropna(), bins=100, edgecolor='black', alpha=0.7)
plt.xlabel("Time Delay (seconds)")
plt.ylabel("Frequency")
plt.title("Distribution of Time Delay (seconds)")
plt.grid(axis='y', linestyle='--', alpha=0.7)

# 画像ファイルとして保存
plot_filename = f"time_delay_distribution_" + str(base_file) + "_" + f"{target_channel if apply_filter else 'all'}.png"
plt.savefig(plot_filename)
print(f"Histogram saved as {plot_filename}")

# block_delayの分布図を作成
plt.figure(figsize=(10, 6))
plt.hist(df["block_delay"].dropna(), bins=100, edgecolor='black', alpha=0.7)
plt.xlabel("Block Delay (blocks)")
plt.ylabel("Frequency")
plt.title("Distribution of Block Delay (blocks)")
plt.grid(axis='y', linestyle='--', alpha=0.7)

# 画像ファイルとして保存
block_plot_filename = f"block_delay_distribution_" + str(base_file) + "_" + f"{target_channel if apply_filter else 'all'}.png"
plt.savefig(block_plot_filename)
print(f"Histogram saved as {block_plot_filename}")

