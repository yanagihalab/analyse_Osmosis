import pandas as pd
import matplotlib.pyplot as plt
import os

# フィルターモードを選択
filter_mode = input("フィルターを適用しますか？ (yes/no): ").strip().lower()
apply_filter = filter_mode in ["yes", "y"]

# ファイルの存在確認
base_file = "ibc_packet_delay_22529000-22619000"
target_csv = base_file + ".csv"
if not os.path.exists(target_csv):
    print(f"Error: CSV file '{target_csv}' not found.")
    exit()

# CSVの読み込み
try:
    df = pd.read_csv(target_csv)
except Exception as e:
    print(f"Error reading CSV file: {e}")
    exit()

# チャネルIDを取得
df["channel_id"] = df["channel_id"].astype(str)
df = df.dropna(subset=["channel_id"])
available_channels = sorted(set(df["channel_id"].str.replace("channel-", "").astype(int)))
print("利用可能なチャネルID:", ", ".join(map(str, available_channels)))

if apply_filter:
    target_channel = input("対象のチャネル番号を入力してください (例: 0, 122, 208): ").strip()
    try:
        target_channel = int(target_channel)
        if target_channel not in available_channels:
            print("無効なチャネルIDが入力されました。利用可能なチャネルを確認してください。")
            exit()
    except ValueError:
        print("無効な入力形式です。数値を入力してください。")
        exit()
else:
    target_channel = "all"

# フィルター適用
df_filtered = df[df["channel_id"] == f"channel-{target_channel}"].copy() if apply_filter else df.copy()

# 日付変換
df_filtered["send_time"] = pd.to_datetime(df_filtered["send_time"], errors="coerce")
df_filtered["ack_time"] = pd.to_datetime(df_filtered["ack_time"], errors="coerce")

# NaTを削除
df_filtered = df_filtered.dropna(subset=["send_time", "ack_time"])

# 遅延を計算
df_filtered["delay"] = (df_filtered["ack_time"] - df_filtered["send_time"]).dt.total_seconds()

# 手数料を処理
df_filtered["fee_amount"] = df_filtered["fee_amount"].astype(str).str.extract("([0-9]+)").astype(float, errors="ignore")
df_filtered = df_filtered.dropna(subset=["fee_amount"])

# 遅延と手数料のプロット
plt.figure(figsize=(10, 6))
plt.scatter(df_filtered["delay"], df_filtered["fee_amount"], alpha=0.7, color='black', marker='x')
plt.xlabel("Delay (seconds)")
plt.ylabel("Fee Amount")
plt.title(f"Relationship between Delay and Fee Amount (Channel-{target_channel})")
plt.xlim(0, 50)
plt.grid(True)
plt.savefig(f"lim50_delay_vs_fee_channel_{target_channel}.png", dpi=300, bbox_inches="tight")

# 送信時間と手数料のプロット
plt.figure(figsize=(10, 6))
plt.scatter(df_filtered["send_time"], df_filtered["fee_amount"], alpha=0.7, color='black', marker='x')
plt.xlabel("Send Time")
plt.ylabel("Fee Amount")
plt.title(f"Relationship between Send Time and Fee Amount (Channel-{target_channel})")
plt.xticks(rotation=45)
plt.grid(True)
plt.savefig(f"sendtime_vs_fee_channel_{target_channel}.png", dpi=300, bbox_inches="tight")

# プロット
plt.figure(figsize=(10, 6))
plt.scatter(df_filtered["delay"], df_filtered["fee_amount"], alpha=0.7, color='black', marker='x')
plt.xlabel("Delay (seconds)")
plt.ylabel("Fee Amount")
plt.title(f"Relationship between Delay and Fee Amount (Channel-{target_channel})")
plt.grid(True)
plt.savefig(f"delay_vs_fee_channel_{target_channel}.png", dpi=300, bbox_inches="tight")

# 遅延と送信時間の関係図
plt.figure(figsize=(10, 6))
plt.scatter(df_filtered["send_time"], df_filtered["delay"], alpha=0.7, color='black', marker='x')
plt.xlabel("Send Time")
plt.ylabel("Delay (seconds)")
plt.title(f"Relationship between Send Time and Delay (Channel-{target_channel})")
plt.xticks(rotation=45)
plt.grid(True)
plt.savefig(f"sendtime_vs_delay_channel_{target_channel}.png", dpi=300, bbox_inches="tight")

# 送信時間と手数料のプロット
plt.figure(figsize=(10, 6))
plt.scatter(df_filtered["send_time"], df_filtered["fee_amount"], alpha=0.7, color='black', marker='x')
plt.xlabel("Send Time")
plt.ylabel("Fee Amount")
plt.title(f"Relationship between Send Time and Fee Amount (Channel-{target_channel})")
plt.xticks(rotation=45)
plt.grid(True)
plt.savefig(f"sendtime_vs_fee_channel_{target_channel}.png", dpi=300, bbox_inches="tight")