import requests
import time
import pandas as pd
import json
from datetime import datetime, timedelta
import tqdm
import os
import traceback

# RPCエンドポイント
RPC_URL = "https://celestia-mainnet-rpc.itrocket.net/block_results?height="
BLOCK_HEADER_URL = "https://celestia-mainnet-rpc.itrocket.net/block?height="

# 解析対象のブロック範囲
START_HEIGHT = 4518200
END_HEIGHT = 4520000
BLOCK_INTERVAL = 50

# ディレクトリ設定
TEMP_DIR = "current"
FINAL_DIR = "."
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(FINAL_DIR, exist_ok=True)

print(f"Analyzing {START_HEIGHT} to {END_HEIGHT} ({END_HEIGHT - START_HEIGHT} blocks)")

# データ保存用辞書
send_packets = {}
ack_packets = {}
recv_packets = {}
block_timestamps = {}
send_tx_data = {}
ack_tx_data = {}  # 追加: acknowledge_packet のデータを保存

def fetch_json(url, timeout=5, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
        retries += 1
        time.sleep(0.5)
    print(f"Max retries reached for {url}, skipping...")
    return None

def parse_ibc_events(height, block_data):
    if not block_data or not isinstance(block_data, dict):
        return
    
    events = block_data.get("txs_results", [])
    for tx in events:
        tx_events = tx.get("events", [])
        for event in tx_events:
            event_type = event.get("type", "")
            attributes = {attr.get("key"): attr.get("value") for attr in event.get("attributes", [])}
            
            if event_type == "send_packet":
                key = (attributes.get("packet_src_channel"), attributes.get("packet_sequence"))
                if key[0] and key[1]:
                    send_packets[key] = height
                    send_tx_data[key] = {
                        "denom": attributes.get("packet_denom"),
                        "amount": attributes.get("packet_amount"),
                        "sender": attributes.get("packet_sender"),
                        "receiver": attributes.get("packet_receiver"),
                    }
            
            elif event_type == "acknowledge_packet":
                key = (attributes.get("packet_src_channel"), attributes.get("packet_sequence"))
                if key[0] and key[1]:
                    ack_packets[key] = height
                    ack_tx_data[key] = {
                        "success": "success" in attributes,
                        "acknowledgement": attributes.get("acknowledgement"),
                    }
            
            elif event_type == "recv_packet":
                key = (attributes.get("packet_src_channel"), attributes.get("packet_sequence"))
                if key[0] and key[1]:
                    recv_packets[key] = height

def fetch_block_timestamp(height):
    """ブロックのタイムスタンプを取得"""
    data = fetch_json(BLOCK_HEADER_URL + str(height))
    if data:
        timestamp = data.get("result", {}).get("block", {}).get("header", {}).get("time", None)
        if timestamp:
            timestamp = timestamp.rstrip("Z")  # UTC表記のZを削除
            if "." in timestamp:
                base_time, fraction = timestamp.split(".")
                fraction = fraction[:6]  # マイクロ秒まで（ナノ秒は削除）
                timestamp = f"{base_time}.{fraction}"
            else:
                timestamp = f"{timestamp}.000000"  # 小数点がない場合はマイクロ秒を追加
            try:
                return datetime.fromisoformat(timestamp)
            except ValueError:
                print(f"[ERROR] Invalid ISO format: {timestamp}")
    return None


def save_csv(start_height, end_height, directory):
    print(directory)
    if not send_packets:
        return
    
    data = []
    for key, send_height in send_packets.items():
        send_data = send_tx_data.get(key, {})
        ack_data = ack_tx_data.get(key, {})
        
        data.append({
            "channel_id": key[0],
            "sequence": key[1],
            "send_height": send_height,
            "ack_height": ack_packets.get(key, None),
            "recv_height": recv_packets.get(key, None),
            "denom": send_data.get("denom", None),
            "amount": send_data.get("amount", None),
            "sender": send_data.get("sender", None),
            "receiver": send_data.get("receiver", None),
            "ack_success": ack_data.get("success", None),
            "ack_data": ack_data.get("acknowledgement", None),
        })
    
    df = pd.DataFrame(data)
    csv_filename = os.path.join(directory, f"ibc_packet_data_{start_height}-{end_height}.csv")
    df.to_csv(csv_filename, index=False)
    print(f"CSV file saved: {csv_filename}")

def process_blocks():
    """ブロックを処理してIBCデータを収集する"""
    start_time = time.time()
    last_saved_height = START_HEIGHT  # 最後に保存したブロックの高さ

    with tqdm.tqdm(total=(END_HEIGHT - START_HEIGHT + 1), desc="Processing Blocks") as pbar:
        for height in range(START_HEIGHT, END_HEIGHT + 1):
            try:
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

                # BLOCK_INTERVAL ごとに保存するよう修正
                if height >= last_saved_height + BLOCK_INTERVAL or height == END_HEIGHT:
                    print(f"[INFO] Saving CSV at block {height} (Last saved at {last_saved_height})")
                    save_csv(last_saved_height, height, TEMP_DIR)
                    last_saved_height = height  # 最後に保存したブロックの高さを更新

                time.sleep(0.1)
            except Exception as e:
                print(f"[ERROR] Exception occurred at block {height}: {e}")
                traceback.print_exc()  # スタックトレースを表示


process_blocks()
save_csv(START_HEIGHT, END_HEIGHT, FINAL_DIR)
print("Final CSV file saved successfully.")
