import requests
import time
import pandas as pd
from datetime import datetime, timedelta
import tqdm  # 進捗バー
import os  # ディレクトリ操作

# RPCエンドポイント
RPC_URL = "https://celestia-mainnet-rpc.itrocket.net/block_results?height="
BLOCK_HEADER_URL = "https://celestia-mainnet-rpc.itrocket.net/block?height="

# 解析対象のブロック範囲
START_HEIGHT = 3100000
END_HEIGHT = 4102000
BLOCK_INTERVAL = 2000  # 一時保存間隔

# ディレクトリ設定
TEMP_DIR = "current"
FINAL_DIR = "."
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(FINAL_DIR, exist_ok=True)

print(f"Analyzing {START_HEIGHT} to {END_HEIGHT} ({END_HEIGHT - START_HEIGHT} blocks)")

# データ保存用辞書
send_packets = {}
ack_packets = {}
block_timestamps = {}
fee_data = {}
send_tx_data = {}
ack_tx_data = {}
packet_delays = []

def fetch_json(url, timeout=5):
    """指定URLのデータを取得する（成功するまでリトライ）"""
    while True:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch {url}, status code: {response.status_code}, response: {response.text}, retrying...")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}, retrying...")
        time.sleep(1)

def fetch_block_timestamp(height):
    """ブロックのタイムスタンプを取得"""
    data = fetch_json(BLOCK_HEADER_URL + str(height))
    if not data:
        print(f"Error: No data received for block {height}")
        return None
    
    try:
        timestamp = data.get("result", {}).get("block", {}).get("header", {}).get("time", None)
        if timestamp:
            timestamp = timestamp.replace("Z", "")
            if "." in timestamp:
                base_time, fraction = timestamp.split(".")
                fraction = fraction.ljust(6, "0")[:6]  # マイクロ秒精度を確保
                timestamp = f"{base_time}.{fraction}"
            return datetime.fromisoformat(timestamp)
        else:
            print(f"Warning: No timestamp found for block {height}")
    except Exception as e:
        print(f"Error parsing timestamp for block {height}: {e}")
    return None

def parse_ibc_events(height, block_data):
    """IBCパケット情報を解析"""
    if not block_data:
        print(f"Warning: Block data is invalid for height {height}")
        return
    
    # `None` の場合に空リストを代入
    events = (block_data.get("begin_block_events") or []) + (block_data.get("end_block_events") or [])
    tx_fees = {}

    for tx in block_data.get("txs_results", []) or []:
        tx_hash = tx.get("hash", None)  # TXハッシュが空でも問題ない
        events.extend(tx.get("events", []))
    
        # 手数料データを取得し、tx_hashに紐付ける
        fee_amount = None
        fee_denom = None
        for event in events:
            if event.get("type") in ["tx_fee", "fee_pay"]:
                for attr in event.get("attributes", []):
                    if attr.get("key") in ["amount", "fee"]:
                        fee_amount = attr.get("value")
                    elif attr.get("key") == "denom":
                        fee_denom = attr.get("value")
                tx_fees[tx_hash] = {"fee_amount": fee_amount, "fee_denom": fee_denom}
        
        for event in events:
            if event.get("type") in ["send_packet", "acknowledge_packet"]:
                packet_data = {attr.get("key"): attr.get("value") for attr in event.get("attributes", [])}
                sequence, channel_id = packet_data.get("packet_sequence"), packet_data.get("packet_src_channel")
                if sequence and channel_id:
                    key = (channel_id, sequence)
                    if event["type"] == "send_packet":
                        send_packets[key] = height
                        fee_data[key] = tx_fees.get(tx_hash, {"fee_amount": None, "fee_denom": None})
                    else:
                        ack_packets[key] = height

def save_csv(start_height, end_height, directory):
    """解析データをCSVに保存"""
    packet_delays = []
    
    for key in send_packets.keys():
        send_height = send_packets.get(key)
        ack_height = ack_packets.get(key, None)
        
        send_time = block_timestamps.get(send_height)
        ack_time = block_timestamps.get(ack_height) if ack_height else None

        packet_delays.append({
            "channel_id": key[0],
            "sequence": key[1],
            "send_height": send_height,
            "send_time": send_time.isoformat() if send_time else None,
            "ack_height": ack_height,
            "ack_time": ack_time.isoformat() if ack_time else None,
            "block_delay": ack_height - send_height if ack_height else None,
            "fee_amount": fee_data.get(key, {}).get("fee_amount"),
            "fee_denom": fee_data.get(key, {}).get("fee_denom")
        })

    if not packet_delays:
        print("No data to save. Skipping CSV creation.")
        return
    
    df = pd.DataFrame(packet_delays)
    csv_filename = os.path.join(directory, f"ibc_packet_delay_{start_height}-{end_height}.csv")
    df.to_csv(csv_filename, index=False)
    print(f"CSV file saved: {csv_filename}")

# メイン処理
start_time = time.time()
with tqdm.tqdm(total=(END_HEIGHT - START_HEIGHT + 1), desc="Processing Blocks") as pbar:
    for height in range(START_HEIGHT, END_HEIGHT + 1):
        block_results = fetch_json(RPC_URL + str(height))
        block_result = block_results.get("result", {})
        
        if not block_result:
            print(f"Warning: No 'result' field in block {height}, received data: {block_results}")
        else:
            parse_ibc_events(height, block_result)
        
        block_timestamps[height] = fetch_block_timestamp(height)
        pbar.update(1)
        time.sleep(0.1)

save_csv(START_HEIGHT, END_HEIGHT, FINAL_DIR)
print("Final CSV file saved successfully.")
