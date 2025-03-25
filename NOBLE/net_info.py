import requests
import json
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import matplotlib

# 非インタラクティブ環境用の設定
matplotlib.use("Agg")

# --- 1. JSON 取得関数 ---
RPC_URL = "https://cosmos-rpc.publicnode.com"

def fetch_block_data(height):
    """ 指定したブロック高さのデータを取得 """
    url = f"{RPC_URL}/block?height={height}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "result" not in data or "block" not in data["result"]:
            print(f"Invalid response format for block {height}")
            return None
        print(f"Fetched block {height} successfully")  # デバッグ
        return data
    except requests.RequestException as e:
        print(f"Error fetching block {height}: {e}")
        return None

# --- 2. バリデータの署名データを抽出 ---
def extract_validator_timestamps(data):
    """ 各ブロックからバリデータの署名タイムスタンプを抽出 """
    if not data or "result" not in data:
        return None

    block_header = data["result"]["block"]["header"]
    proposer_address = block_header.get("proposer_address")
    block_time = block_header.get("time")
    
    if not proposer_address or not block_time:
        print("Invalid block header format")
        return None
    
    # 余分なナノ秒部分をカットしてブロック時間をパース
    block_time = block_time[:26] + "Z"
    block_timestamp = datetime.strptime(block_time, "%Y-%m-%dT%H:%M:%S.%fZ")

    signatures = data["result"]["block"]["last_commit"].get("signatures", [])
    print(f"Signatures found: {len(signatures)}")  # デバッグ追加

    validators = []
    for sig in signatures:
        validator_address = sig.get("validator_address")
        timestamp = sig.get("timestamp")
        if validator_address and timestamp and validator_address != proposer_address:
            try:
                # 余分なナノ秒部分をカット（6桁のマイクロ秒に変換）
                timestamp = timestamp[:26] + "Z"
                parsed_timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                delay_ms = (parsed_timestamp - block_timestamp).total_seconds() * 1000
                
                validators.append({
                    "validator_address": validator_address,
                    "timestamp": parsed_timestamp,
                    "delay_ms": delay_ms
                })
            except ValueError:
                print(f"Invalid timestamp format after trimming: {timestamp}")

    print(f"Extracted {len(validators)} validators")  # デバッグ追加
    return validators if validators else None

# --- 3. ブロックデータを収集 ---
def collect_block_data(start_height, end_height):
    """ 指定したブロック範囲のデータを収集 """
    num_blocks = start_height - end_height
    if num_blocks <= 0:
        print("Error: start_height must be greater than end_height")
        return []
    
    all_validators = []
    for height in tqdm(range(start_height, end_height, -1)):
        block_data = fetch_block_data(height)
        if block_data:
            validators = extract_validator_timestamps(block_data)
            if validators:
                all_validators.append((height, validators))
                print(f"Block {height}: {len(validators)} validators")  # デバッグ
    print(f"Collected {len(all_validators)} blocks")  # デバッグ
    return all_validators

# --- 4. ネットワークモデルの構築 ---
def build_network(all_validators):
    """ バリデータのネットワークグラフを構築 """
    G = nx.Graph()
    edges = []
    for _, validators in all_validators:
        validator_addresses = [v["validator_address"] for v in validators]
        for i, v1 in enumerate(validator_addresses):
            for v2 in validator_addresses[i+1:]:
                if G.has_edge(v1, v2):
                    G[v1][v2]["weight"] += 1
                else:
                    G.add_edge(v1, v2, weight=1)
                edges.append((v1, v2, G[v1][v2]["weight"]))
    print(f"Total edges: {len(edges)}")  # デバッグ
    print("Edges in network:", G.edges(data=True))  # デバッグ用
    return G

# --- 5. ネットワークの可視化 & 座標保存 ---
def plot_network(G):
    """ ネットワークグラフを描画し、座標データをCSVに保存 """
    if G.number_of_nodes() == 0:
        print("Warning: The network graph is empty and will not be visualized.")
        return
    
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, seed=42) if G.number_of_nodes() > 5 else nx.kamada_kawai_layout(G)
    
    # ノードの座標をCSVに保存
    df_positions = pd.DataFrame([(node, pos[node][0], pos[node][1]) for node in G.nodes()],
                                 columns=["Validator", "X", "Y"])
    df_positions.to_csv("validator_positions.csv", index=False)
    print("Node positions saved to 'validator_positions.csv'")
    
    # エッジの描画
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    max_weight = max(edge_weights) if edge_weights else 1
    edge_widths = [(w / max_weight) * 5 for w in edge_weights]
    
    nx.draw_networkx_nodes(G, pos, node_size=500)
    nx.draw_networkx_edges(G, pos, width=edge_widths, edge_color="gray")
    nx.draw_networkx_labels(G, pos, font_size=6, verticalalignment='bottom', horizontalalignment='left')
    
    plt.title("Validator Network Graph")
    plt.savefig("validator_network_cosmosss.png")
    print("Network graph saved as 'validator_networkCss.png'")

# --- 6. 実行 ---
def main():
    start_height = 24765149
    end_height = 24765149 - 3000
    all_validators = collect_block_data(start_height, end_height)
    G = build_network(all_validators)
    plot_network(G)

if __name__ == "__main__":
    main()
