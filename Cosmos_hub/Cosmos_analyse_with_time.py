import requests
import time
import pandas as pd
from datetime import datetime, timedelta
import tqdm  # 進捗バー
import os  # ディレクトリ操作

# RPCエンドポイント
RPC_URL = "https://cosmoshub.tendermintrpc.lava.build/block_results?height="
BLOCK_HEADER_URL = "https://cosmoshub.tendermintrpc.lava.build/block?height="

# 解析対象ブロック範囲
START_HEIGHT = 23144450
END_HEIGHT = 24603038
BLOCK_INTERVAL = 5000  # 一時保存間隔

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
            print(f"Failed to fetch {url}, retrying...")
        except Exception as e:
            print(f"Error fetching {url}, retrying: {e}")
        time.sleep(1)


def fetch_block_timestamp(height):
    """ブロックのタイムスタンプを取得"""
    data = fetch_json(BLOCK_HEADER_URL + str(height))
    if data:
        timestamp = data.get("result", {}).get("block", {}).get("header", {}).get("time", None)
        if timestamp:
            timestamp = timestamp.replace("Z", "")
            if "." in timestamp:
                base_time, fraction = timestamp.split(".")
                fraction = fraction.ljust(6, "0")[:6]  # Ensure microsecond precision
                timestamp = f"{base_time}.{fraction}"
            try:
                return datetime.fromisoformat(timestamp)
            except ValueError:
                print(f"Invalid ISO format: {timestamp}")
    return None


def parse_ibc_events(height, block_data):
    """IBCパケット情報を解析"""
    if not block_data:
        print(f"Warning: Block data is invalid for height {height}")
        return
    
    events = block_data.get("begin_block_events", []) + block_data.get("end_block_events", [])
    tx_fees = {}

    for tx in block_data.get("txs_results", []) or []:
        tx_hash = tx.get("hash", "unknown")
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
    packet_delays = [
        {
            "channel_id": key[0],
            "sequence": key[1],
            "send_height": send_packets[key],
            "send_time": block_timestamps.get(send_packets[key]).isoformat() if send_packets.get(key) in block_timestamps else None,
            "ack_height": ack_packets.get(key),
            "ack_time": block_timestamps.get(ack_packets[key]).isoformat() if ack_packets.get(key) in block_timestamps else None,
            "block_delay": ack_packets.get(key, 0) - send_packets[key] if ack_packets.get(key) else None,
            "fee_amount": fee_data.get(key, {}).get("fee_amount"),
            "fee_denom": fee_data.get(key, {}).get("fee_denom")
        }
        for key in send_packets.keys()
    ]
    
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
        if block_results:
            parse_ibc_events(height, block_results.get("result", {}))
        block_timestamps[height] = fetch_block_timestamp(height)
        
        elapsed_time = time.time() - start_time
        processed_blocks = height - START_HEIGHT + 1
        avg_time_per_block = elapsed_time / processed_blocks
        eta_seconds = avg_time_per_block * (END_HEIGHT - height)
        pbar.set_postfix({"ETA": str(timedelta(seconds=int(eta_seconds)))})
        pbar.update(1)
        
        if (height - START_HEIGHT) % BLOCK_INTERVAL == 0 or height == END_HEIGHT:
            save_csv(START_HEIGHT, height, TEMP_DIR)
        time.sleep(0.1)

save_csv(START_HEIGHT, END_HEIGHT, FINAL_DIR)
print("Final CSV file saved successfully.")
