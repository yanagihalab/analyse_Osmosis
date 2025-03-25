import networkx as nx
import matplotlib.pyplot as plt
import requests
import time
import os
import imageio.v2 as imageio
import numpy as np
import PIL.Image  # 低メモリモード用

# noble-rpc.polkachu.com から最新の net_info データを取得
url = "https://noble-rpc.polkachu.com/net_info"
response = requests.get(url)
net_info = response.json()

# フィルター設定（通信量の閾値をMB単位で指定）
MIN_TRAFFIC_MB = 1.0  # 最低通信量（MB）

# モード設定
DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"
ANIMATION_ONLY_MODE = os.getenv("ANIMATION_ONLY_MODE", "False").lower() == "true"
LOW_MEMORY_MODE = os.getenv("LOW_MEMORY_MODE", "False").lower() == "true"
GIF_STEP_INTERVAL = int(os.getenv("GIF_STEP_INTERVAL", "1000"))  # 1000ステップごとにGIF作成

# 画像保存ディレクトリ
image_dir = "block_propagation_images"
output_gif_template = "block_propagation_part_{}.gif"

# 既存の画像からアニメーションを作成するモード
if ANIMATION_ONLY_MODE:
    print("Creating animations from existing images...")
    image_files = sorted([os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith(".png")])
    if not image_files:
        print("No images found in", image_dir)
    else:
        for part, start in enumerate(range(0, len(image_files), GIF_STEP_INTERVAL)):
            output_gif = output_gif_template.format(part + 1)
            with imageio.get_writer(output_gif, mode='I', duration=0.1) as writer:
                for filename in image_files[start:start + GIF_STEP_INTERVAL]:
                    image = np.array(PIL.Image.open(filename))  # 修正: imageio.core.asarray を使わず numpy を使用
                    
                    # 低メモリモードで解像度を縮小
                    if LOW_MEMORY_MODE:
                        image = PIL.Image.fromarray(image)
                        image = image.resize((image.width // 2, image.height // 2), PIL.Image.LANCZOS)
                        image = np.array(image)
                    
                    writer.append_data(image)
            print(f"Animation saved as {output_gif}")
    exit()

# グラフの作成
G = nx.DiGraph()  # 有向グラフに変更

# ピアノードの追加と接続情報の取得
for peer in net_info.get("result", {}).get("peers", []):
    peer_id = peer.get("node_info", {}).get("id", "Unknown")
    remote_ip = peer.get("remote_ip", "Unknown")
    is_outbound = peer.get("is_outbound", False)
    send_bytes = int(peer.get("connection_status", {}).get("SendMonitor", {}).get("Bytes", 0))
    recv_bytes = int(peer.get("connection_status", {}).get("RecvMonitor", {}).get("Bytes", 0))
    
    # 通信量に基づいたエッジの重み（MB単位）
    edge_weight = (send_bytes + recv_bytes) / (1024 * 1024)  
    
    # 指定した通信量の閾値以上でない場合はスキップ
    if edge_weight < MIN_TRAFFIC_MB:
        continue
    
    edge_weight = max(0.1, min(edge_weight, 5.0))  # 重みの範囲を制限
    
    # ノードの追加（色を設定）
    G.add_node(peer_id, color='blue', ip=remote_ip)
    
    # ピアノード間の接続を追加（有向グラフに変更し、方向を可視化）
    for other_peer in net_info.get("result", {}).get("peers", []):
        other_peer_id = other_peer.get("node_info", {}).get("id", "Unknown")
        if peer_id != other_peer_id:
            direction = (peer_id, other_peer_id) if is_outbound else (other_peer_id, peer_id)
            G.add_edge(*direction, weight=edge_weight, edge_color='blue' if is_outbound else 'green')

# ノードの色設定
colors = ['red' if n in hub_nodes else 'blue' for n in G.nodes]

# ノードの数を表示
print(f"Total number of nodes: {len(G.nodes)}")

# エッジの設定
edges = list(G.edges())
weights = [G[u][v].get('weight', 1.0) for u, v in edges]
edge_colors = [G[u][v].get('edge_color', 'gray') for u, v in edges]

# 実行時間の計測開始
total_steps = len(edges)
start_time = time.time()
STEP_INTERVAL = 1  # すべてのステップを保存

# グラフのレイアウト計算（負荷軽減）
pos = nx.kamada_kawai_layout(G)
plt.figure(figsize=(15, 10))

# 画像保存ディレクトリ作成
os.makedirs(image_dir, exist_ok=True)
image_files = []

if DEBUG_MODE:
    # すべてのステップを保存
    for i, (u, v) in enumerate(edges):
        elapsed_time = time.time() - start_time
        remaining_time_sec = (elapsed_time / (i + 1)) * (total_steps - (i + 1)) if i > 0 else 0
        remaining_time_min = remaining_time_sec / 60
        print(f"Step {i+1}/{total_steps} - Estimated remaining time: {remaining_time_min:.2f} minutes")
        
        plt.clf()
        nx.draw(G, pos, with_labels=False, node_color=colors, node_size=50, edge_color='gray', alpha=0.6, width=weights)
        nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], edge_color=edge_colors[i], width=weights[i])
        plt.title(f"Block Propagation - Step {i+1}/{len(edges)}")
        filename = os.path.join(image_dir, f"block_propagation_step_{i+1}.png")
        plt.savefig(filename)  # 各ステップの画像を保存
        image_files.append(filename)
        print(f"Saved: {filename}")


# import networkx as nx
# import matplotlib.pyplot as plt
# import requests
# import time
# import os
# import imageio

# # noble-rpc.polkachu.com から最新の net_info データを取得
# url = "https://noble-rpc.polkachu.com/net_info"
# response = requests.get(url)
# net_info = response.json()

# # フィルター設定（通信量の閾値をMB単位で指定）
# MIN_TRAFFIC_MB = 1.0  # 最低通信量（MB）

# # デバッグモード判定（デフォルトは True）
# DEBUG_MODE = True

# # グラフの作成
# G = nx.DiGraph()  # 有向グラフに変更

# # ピアノードの追加と接続情報の取得
# for peer in net_info.get("result", {}).get("peers", []):
#     peer_id = peer.get("node_info", {}).get("id", "Unknown")
#     remote_ip = peer.get("remote_ip", "Unknown")
#     is_outbound = peer.get("is_outbound", False)
#     send_bytes = int(peer.get("connection_status", {}).get("SendMonitor", {}).get("Bytes", 0))
#     recv_bytes = int(peer.get("connection_status", {}).get("RecvMonitor", {}).get("Bytes", 0))
    
#     # 通信量に基づいたエッジの重み（MB単位）
#     edge_weight = (send_bytes + recv_bytes) / (1024 * 1024)  
    
#     # 指定した通信量の閾値以上でない場合はスキップ
#     if edge_weight < MIN_TRAFFIC_MB:
#         continue
    
#     edge_weight = max(0.1, min(edge_weight, 5.0))  # 重みの範囲を制限
    
#     # ノードの追加（色を設定）
#     G.add_node(peer_id, color='blue', ip=remote_ip)
    
#     # ピアノード間の接続を追加（有向グラフに変更し、方向を可視化）
#     for other_peer in net_info.get("result", {}).get("peers", []):
#         other_peer_id = other_peer.get("node_info", {}).get("id", "Unknown")
#         if peer_id != other_peer_id:
#             direction = (peer_id, other_peer_id) if is_outbound else (other_peer_id, peer_id)
#             G.add_edge(*direction, weight=edge_weight, edge_color='blue' if is_outbound else 'green')

# # ノードの色設定
# colors = [G.nodes[n].get('color', 'blue') for n in G.nodes]

# # エッジの設定
# edges = list(G.edges())
# weights = [G[u][v].get('weight', 1.0) for u, v in edges]
# edge_colors = [G[u][v].get('edge_color', 'gray') for u, v in edges]

# # 実行時間の計測開始
# total_steps = len(edges)
# start_time = time.time()
# STEP_INTERVAL = 1  # すべてのステップを保存

# # グラフのレイアウト計算（負荷軽減）
# pos = nx.kamada_kawai_layout(G)
# plt.figure(figsize=(15, 10))

# # 画像保存ディレクトリ
# image_dir = "block_propagation_images"
# os.makedirs(image_dir, exist_ok=True)
# image_files = []

# if DEBUG_MODE:
#     # すべてのステップを保存
#     for i, (u, v) in enumerate(edges):
#         elapsed_time = time.time() - start_time
#         remaining_time_sec = (elapsed_time / (i + 1)) * (total_steps - (i + 1)) if i > 0 else 0
#         remaining_time_min = remaining_time_sec / 60
#         print(f"Step {i+1}/{total_steps} - Estimated remaining time: {remaining_time_min:.2f} minutes")
        
#         plt.clf()
#         nx.draw(G, pos, with_labels=False, node_color=colors, node_size=50, edge_color='gray', alpha=0.6, width=weights)
#         nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], edge_color=edge_colors[i], width=weights[i])
#         plt.title(f"Block Propagation - Step {i+1}/{len(edges)}")
#         filename = os.path.join(image_dir, f"block_propagation_step_{i+1}.png")
#         plt.savefig(filename)  # 各ステップの画像を保存
#         image_files.append(filename)
#         print(f"Saved: {filename}")

# # すべての画像からアニメーションを作成
# print("Creating animation...")
# output_gif = "block_propagation.gif"
# with imageio.get_writer(output_gif, mode='I', duration=0.1) as writer:
#     for filename in image_files:
#         image = imageio.imread(filename)
#         writer.append_data(image)
# print(f"Animation saved as {output_gif}")

# import networkx as nx
# import matplotlib.pyplot as plt
# import requests
# import time
# from matplotlib.animation import FuncAnimation
# import os

# # noble-rpc.polkachu.com から最新の net_info データを取得
# url = "https://noble-rpc.polkachu.com/net_info"
# response = requests.get(url)
# net_info = response.json()

# # フィルター設定（通信量の閾値をMB単位で指定）
# MIN_TRAFFIC_MB = 1.0  # 最低通信量（MB）

# # デバッグモード判定（環境変数 DEBUG_MODE が設定されている場合はデバッグモード）
# DEBUG_MODE = "true"

# # グラフの作成
# G = nx.DiGraph()  # 有向グラフに変更

# # ピアノードの追加と接続情報の取得
# for peer in net_info.get("result", {}).get("peers", []):
#     peer_id = peer.get("node_info", {}).get("id", "Unknown")
#     remote_ip = peer.get("remote_ip", "Unknown")
#     is_outbound = peer.get("is_outbound", False)
#     send_bytes = int(peer.get("connection_status", {}).get("SendMonitor", {}).get("Bytes", 0))
#     recv_bytes = int(peer.get("connection_status", {}).get("RecvMonitor", {}).get("Bytes", 0))
    
#     # 通信量に基づいたエッジの重み（MB単位）
#     edge_weight = (send_bytes + recv_bytes) / (1024 * 1024)  
    
#     # 指定した通信量の閾値以上でない場合はスキップ
#     if edge_weight < MIN_TRAFFIC_MB:
#         continue
    
#     edge_weight = max(0.1, min(edge_weight, 5.0))  # 重みの範囲を制限
    
#     # ノードの追加（色を設定）
#     G.add_node(peer_id, color='blue', ip=remote_ip)
    
#     # ピアノード間の接続を追加（有向グラフに変更し、方向を可視化）
#     for other_peer in net_info.get("result", {}).get("peers", []):
#         other_peer_id = other_peer.get("node_info", {}).get("id", "Unknown")
#         if peer_id != other_peer_id:
#             direction = (peer_id, other_peer_id) if is_outbound else (other_peer_id, peer_id)
#             G.add_edge(*direction, weight=edge_weight, edge_color='blue' if is_outbound else 'green')

# # ノードの色設定
# colors = [G.nodes[n].get('color', 'blue') for n in G.nodes]

# # エッジの設定
# edges = list(G.edges())
# weights = [G[u][v].get('weight', 1.0) for u, v in edges]
# edge_colors = [G[u][v].get('edge_color', 'gray') for u, v in edges]

# # 実行時間の計測開始
# total_steps = len(edges)
# start_time = time.time()
# STEP_INTERVAL = max(1, total_steps // 100)  # 100ステップごとに描画

# # グラフのレイアウト計算（負荷軽減）
# pos = nx.kamada_kawai_layout(G)
# plt.figure(figsize=(15, 10))

# if DEBUG_MODE:
#     # デバッグモード（100ステップごとに保存）
#     for i, (u, v) in enumerate(edges):
#         if i % STEP_INTERVAL != 0:
#             continue
#         elapsed_time = time.time() - start_time
#         remaining_time_sec = (elapsed_time / (i + 1)) * (total_steps - (i + 1)) if i > 0 else 0
#         remaining_time_min = remaining_time_sec / 60
#         print(f"Step {i+1}/{total_steps} - Estimated remaining time: {remaining_time_min:.2f} minutes")
        
#         plt.clf()
#         nx.draw(G, pos, with_labels=False, node_color=colors, node_size=50, edge_color='gray', alpha=0.6, width=weights)
#         nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], edge_color=edge_colors[i], width=weights[i])
#         plt.title(f"Block Propagation - Step {i+1}/{len(edges)}")
#         filename = f"block_propagation_step_{i+1}.png"
#         plt.savefig(filename)  # 各ステップの画像を保存
#         print(f"Saved: {filename}")
# else:
#     # 正規モード（アニメーション保存）
#     fig, ax = plt.subplots(figsize=(15, 10))
#     def update(i):
#         if i % STEP_INTERVAL != 0:
#             return
#         elapsed_time = time.time() - start_time
#         remaining_time_sec = (elapsed_time / (i + 1)) * (total_steps - (i + 1)) if i > 0 else 0
#         remaining_time_min = remaining_time_sec / 60
#         print(f"Step {i+1}/{total_steps} - Estimated remaining time: {remaining_time_min:.2f} minutes")
        
#         ax.clear()
#         nx.draw(G, pos, with_labels=False, node_color=colors, node_size=50, edge_color='gray', alpha=0.6, width=weights)
#         nx.draw_networkx_edges(G, pos, edgelist=[edges[i]], edge_color=edge_colors[i], width=weights[i])
#         ax.set_title(f"Block Propagation - Step {i+1}/{len(edges)}")
#     ani = FuncAnimation(fig, update, frames=len(edges), repeat=False)
#     ani.save("block_propagation.mp4", writer="ffmpeg")  # MP4として保存

