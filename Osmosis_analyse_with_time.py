import requests
import time
import re
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tqdm  # tqdm をインポート

# RPCエンドポイント
RPC_URL = "https://rpc.lavenderfive.com/osmosis/block_results?height="
BLOCK_HEADER_URL = "https://rpc.lavenderfive.com/osmosis/block?height="

# 解析対象のブロック範囲
START_HEIGHT = 30050000
END_HEIGHT = 30052000  # デバッグ用に小さい範囲

print(f"{START_HEIGHT} から {END_HEIGHT} までの {END_HEIGHT - START_HEIGHT} ブロック分の分析")

# データ保存用辞書
send_packets = {}
ack_packets = {}
block_timestamps = {}
fee_data = {}
send_tx_data = {}
ack_tx_data = {}

packet_delays = []

def fetch_block_results(height, retries=3):
    """ 指定したブロックの情報を取得する（最大3回リトライ）"""
    for attempt in range(retries):
        try:
            response = requests.get(RPC_URL + str(height), timeout=5)  # 5秒のタイムアウト設定
            if response.status_code == 200:
                data = response.json()
                if data.get("result") and "txs_results" in data["result"]:
                    return data  # 成功した場合はデータを返す
                else:
                    print(f"Warning: txs_results is missing for height {height}, attempt {attempt+1}/{retries}")
            else:
                print(f"Error: Received status code {response.status_code} for block {height}, attempt {attempt+1}/{retries}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching block {height}, attempt {attempt+1}/{retries}: {e}")

        time.sleep(1)  # 1秒待機して再試行

    print(f"Failed to fetch block {height} after {retries} attempts.")
    return None  # 取得できなかった場合は None を返す

def fetch_block_timestamp(height):
    """ 指定したブロックのタイムスタンプを取得する """
    try:
        response = requests.get(BLOCK_HEADER_URL + str(height), timeout=5)
        if response.status_code == 200:
            block_data = response.json()
            timestamp = block_data["result"]["block"]["header"]["time"]
            timestamp = timestamp.replace("Z", "")
            
            if "." in timestamp:
                base_time, fraction = timestamp.split(".")
                fraction = fraction[:6]  # 6桁までに切り捨て（マイクロ秒まで対応）
                timestamp = f"{base_time}.{fraction}"

            return datetime.fromisoformat(timestamp)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching timestamp for block {height}: {e}")
    return None

def parse_ibc_events(height, block_data):
    """ IBC関連のイベントを解析 """
    if not block_data or not isinstance(block_data, dict):
        print(f"Warning: Block data is invalid or missing for height {height}")
        return
    
    txs_results = block_data.get("txs_results")

    # txs_results が None の場合、リトライ後も取得できなかったと判断
    if not isinstance(txs_results, list):
        print(f"Warning: txs_results is missing or invalid for height {height}")
        return
    
    tx_fees = {}

    for tx in txs_results:
        tx_hash = tx.get("hash", None)
        fee_amount = None
        fee_denom = None
        for event in tx.get("events", []):
            if event["type"] == "tx_fee":
                for attr in event["attributes"]:
                    if attr["key"] == "amount":
                        fee_amount = attr["value"]
                    elif attr["key"] == "denom":
                        fee_denom = attr["value"]
        if tx_hash:
            tx_fees[tx_hash] = {"fee_amount": fee_amount, "fee_denom": fee_denom}

    for tx in txs_results:
        tx_hash = tx.get("hash", None)
        for event in tx.get("events", []):
            if event["type"] == "send_packet":
                packet_data = {attr["key"]: attr["value"] for attr in event["attributes"]}
                sequence = packet_data.get("packet_sequence")
                channel_id = packet_data.get("packet_src_channel")
                
                if sequence and channel_id:
                    send_packets[(channel_id, sequence)] = height
                    fee_data[(channel_id, sequence)] = tx_fees.get(tx_hash, {"fee_amount": None, "fee_denom": None})
                    send_tx_data[(channel_id, sequence)] = {
                        "send_tx_hash": tx_hash
                    }
            elif event["type"] == "acknowledge_packet":
                packet_data = {attr["key"]: attr["value"] for attr in event["attributes"]}
                sequence = packet_data.get("packet_sequence")
                channel_id = packet_data.get("packet_src_channel")
                
                if sequence and channel_id:
                    ack_packets[(channel_id, sequence)] = height
                    ack_tx_data[(channel_id, sequence)] = {"ack_tx_hash": tx_hash}

# 残り時間の計測用
start_time = time.time()
processed_blocks = 0

# tqdm で進捗バーを表示
with tqdm.tqdm(total=(END_HEIGHT - START_HEIGHT + 1), desc="Processing Blocks") as pbar:
    for height in range(START_HEIGHT, END_HEIGHT + 1):
        block_start_time = time.time()  # 各ブロックの処理開始時間

        block_results = fetch_block_results(height)
        if block_results:
            parse_ibc_events(height, block_results.get("result", {}))

        block_timestamps[height] = fetch_block_timestamp(height)

        # 平均処理時間の計算
        processed_blocks += 1
        elapsed_time = time.time() - start_time
        avg_time_per_block = elapsed_time / processed_blocks
        remaining_blocks = END_HEIGHT - height
        eta_seconds = avg_time_per_block * remaining_blocks
        eta_time = str(timedelta(seconds=int(eta_seconds)))

        # tqdm の進捗バー更新
        pbar.set_postfix({"ETA": eta_time, "Remaining Blocks": remaining_blocks})
        pbar.update(1)

        time.sleep(0.1)

# データ整理と保存
df = pd.DataFrame(packet_delays)
csv_filename = f"ibc_packet_delay_analysis_{START_HEIGHT}-{END_HEIGHT}.csv"
df.to_csv(csv_filename, index=False)
print(f"CSV file saved: {csv_filename}")
