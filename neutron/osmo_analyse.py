import requests
import time
import pandas as pd

# RPCエンドポイント
RPC_URL = "https://rpc.lavenderfive.com/osmosis/block_results?height="

# 解析対象のブロック範囲
START_HEIGHT = 30131000  # 例: 調査開始ブロック
END_HEIGHT = 30159694   # 例: 調査終了ブロック
print(f"{START_HEIGHT} から {END_HEIGHT} までの {END_HEIGHT-START_HEIGHT} ブロック分の分析")
# IBCパケット情報を保存する辞書
send_packets = {}
ack_packets = {}

def fetch_block_results(height, retries=3):
    """指定されたブロックのデータを取得する。失敗した場合は再試行"""
    for attempt in range(retries):
        try:
            response = requests.get(RPC_URL + str(height))
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch block {height}, attempt {attempt+1}")
        except Exception as e:
            print(f"Error fetching block {height}, attempt {attempt+1}: {e}")
        time.sleep(1)  # 再試行の前に待機
    return None

def parse_ibc_events(height, block_data):
    """ブロックデータから IBC の send_packet と acknowledge_packet を解析"""
    if not block_data:
        return
    
    events = []
    if "begin_block_events" in block_data:
        events.extend(block_data["begin_block_events"])
    if "end_block_events" in block_data:
        events.extend(block_data["end_block_events"])
    
    # トランザクションごとのイベント
    txs_results = block_data.get("txs_results", [])
    if txs_results:
        for tx in txs_results:
            if "events" in tx:
                events.extend(tx["events"])
    
    for event in events:
        if event["type"] == "send_packet":
            packet_data = {attr["key"]: attr["value"] for attr in event["attributes"]}
            sequence = packet_data.get("packet_sequence")
            channel_id = packet_data.get("packet_src_channel")
            if sequence and channel_id:
                send_packets[(channel_id, sequence)] = height
        
        elif event["type"] == "acknowledge_packet":
            packet_data = {attr["key"]: attr["value"] for attr in event["attributes"]}
            sequence = packet_data.get("packet_sequence")
            channel_id = packet_data.get("packet_src_channel")
            if sequence and channel_id:
                ack_packets[(channel_id, sequence)] = height

# 指定範囲のブロックを取得して解析
for height in range(START_HEIGHT, END_HEIGHT + 1):
    print(f"Fetching block {height}...")
    print(f"Query block {height-START_HEIGHT}")
    block_results = fetch_block_results(height)
    while block_results is None:
        print(f"Retrying block {height}...")
        block_results = fetch_block_results(height)
    
    parse_ibc_events(height, block_results.get("result", {}))
    time.sleep(0.1)  # API負荷軽減のため

# send_packet と acknowledge_packet の遅延分析
packet_delays = []
for key in send_packets.keys():
    send_height = send_packets[key]
    ack_height = ack_packets.get(key)
    if ack_height:
        delay = ack_height - send_height
        packet_delays.append({
            "channel_id": key[0],
            "sequence": key[1],
            "send_height": send_height,
            "ack_height": ack_height,
            "block_delay": delay
        })

# 結果を DataFrame に保存してCSVファイルとして出力
df = pd.DataFrame(packet_delays)
csv_filename = "ibc_packet_delay_analysis_" + str(START_HEIGHT) + "-" + str(END_HEIGHT) + ".csv"
df.to_csv(csv_filename, index=False)

print(f"CSV file saved: {csv_filename}")
