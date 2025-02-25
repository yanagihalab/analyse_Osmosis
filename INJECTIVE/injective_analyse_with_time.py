import requests
import time
import re
import pandas as pd
from datetime import datetime

# RPCエンドポイント
RPC_URL = "https://rpc.lavenderfive.com:443/injective/block_results?height="
BLOCK_HEADER_URL = "https://rpc.lavenderfive.com:443/injective/block?height="

# 解析対象のブロック範囲
START_HEIGHT = 106000000
END_HEIGHT = 107180000# 24546166

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
    for attempt in range(retries):
        try:
            response = requests.get(RPC_URL + str(height))
            if response.status_code == 200:
                return response.json()
            time.sleep(0.1)
        except Exception as e:
            print(f"Error fetching block {height}, attempt {attempt+1}: {e}")
    return None

def fetch_block_timestamp(height):
    try:
        response = requests.get(BLOCK_HEADER_URL + str(height))
        if response.status_code == 200:
            block_data = response.json()
            timestamp = block_data["result"]["block"]["header"]["time"]
            timestamp = timestamp.replace("Z", "")
            
            if "." in timestamp:
                base_time, fraction = timestamp.split(".")
                fraction = fraction[:6]  # 6桁までに切り捨て（マイクロ秒まで対応）
                timestamp = f"{base_time}.{fraction}"

            return datetime.fromisoformat(timestamp)
    except Exception as e:
        print(f"Error fetching timestamp for block {height}: {e}")
    return None

def parse_ibc_events(height, block_data):
    if not block_data or not isinstance(block_data, dict):
        print(f"Warning: Block data is invalid for height {height}")
        return
    
    txs_results = block_data.get("txs_results", [])
    
    if not isinstance(txs_results, list):
        print(f"Warning: txs_results is invalid for height {height}")
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

for height in range(START_HEIGHT, END_HEIGHT + 1):
    print(f"Fetching block {height}...")
    print(f"Query block {height-START_HEIGHT} 残り {END_HEIGHT-height}")
    block_results = fetch_block_results(height)
    if block_results:
        parse_ibc_events(height, block_results.get("result", {}))
    block_timestamps[height] = fetch_block_timestamp(height)
    time.sleep(0.1)

for key in send_packets.keys():
    send_height = send_packets[key]
    ack_height = ack_packets.get(key)
    send_time = block_timestamps.get(send_height)
    ack_time = block_timestamps.get(ack_height) if ack_height else None
    delay_blocks = (ack_height - send_height) if ack_height else None
    delay_time = (ack_time - send_time).total_seconds() if send_time and ack_time else None
    
    fee_info = fee_data.get(key, {"fee_amount": None, "fee_denom": None})
    send_tx_info = send_tx_data.get(key, {
        "send_tx_hash": None
    })
    ack_tx_info = ack_tx_data.get(key, {
        "ack_tx_hash": None
    })
    
    packet_delays.append({
        "channel_id": key[0],
        "sequence": key[1],
        "send_height": send_height,
        "send_time": send_time.isoformat() if send_time else None,
        "ack_height": ack_height,
        "ack_time": ack_time.isoformat() if ack_time else None,
        "block_delay": delay_blocks,
        "time_delay_sec": delay_time,
        "fee_amount": fee_info["fee_amount"],
        "fee_denom": fee_info["fee_denom"],
        "send_tx_hash": send_tx_info["send_tx_hash"],
        "ack_tx_hash": ack_tx_info["ack_tx_hash"]
    })

df = pd.DataFrame(packet_delays)
csv_filename = f"ibc_packet_delay_analysis_{START_HEIGHT}-{END_HEIGHT}.csv"
df.to_csv(csv_filename, index=False)
print(f"CSV file saved: {csv_filename}")
