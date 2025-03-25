import requests
import matplotlib.pyplot as plt
import pandas as pd
import time
from tqdm import tqdm

# NobleのRPCエンドポイント
RPC_URL = "https://cosmos-rpc.polkachu.com/"
# https://noble-rpc.polkachu.com
# 取得するブロック範囲
START_BLOCK = 24779169
END_BLOCK = 24779169 + 100000
MAX_RETRIES = 1000  # 最大リトライ回数
WAIT_TIME = 5  # エラー時の待機時間（秒）

def get_block(block_height):
    """指定したブロックの情報を取得（リトライ対応）"""
    url = f"{RPC_URL}/block?height={block_height}"
    session = requests.Session()
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[Error] {e}, retrying {attempt+1}/{MAX_RETRIES}...")
            time.sleep(WAIT_TIME)
    return None

# 過去ブロックのタイムスタンプを取得
timestamps = []
for height in tqdm(range(START_BLOCK, END_BLOCK + 1), desc="Fetching Blocks", unit="block"):
    block = get_block(height)
    if block:
        timestamp = block["result"]["block"]["header"]["time"]  # ISO8601形式
        timestamps.append(pd.to_datetime(timestamp))
    time.sleep(0.2)  # RPCの負荷軽減

# ブロック生成時間を計算
block_intervals = [(timestamps[i] - timestamps[i-1]).total_seconds() for i in range(1, len(timestamps))]

# データをCSVに保存
df = pd.DataFrame(block_intervals, columns=["ブロック生成時間 (秒)"])
df.to_csv("noble_block_times_10000_20000.csv", index=False)
print("データを 'noble_block_times_10000_20000.csv' に保存しました。")

# データの可視化
plt.figure(figsize=(10, 5))
plt.hist(block_intervals, bins=20, edgecolor='black', alpha=0.7)
plt.xlabel("ブロック生成時間 (秒)")
plt.ylabel("頻度")
plt.title("Nobleブロック生成時間の分布 (10000-20000)")
plt.grid()
plt.savefig("NOBLE_Btime.png")

# 統計情報を表示
print(df.describe())
