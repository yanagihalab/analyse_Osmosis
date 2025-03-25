import pandas as pd
import matplotlib.pyplot as plt
import os

# フィルターモードを選択
filter_mode = input("フィルターを適用しますか？ (yes/no): ").strip().lower()
apply_filter = filter_mode in ["yes", "y"]

# ファイルの存在確認
base_file = "merged_output"
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

# チャネルIDの処理
df["channel_id"] = df["channel_id"].astype(str)
df = df.dropna(subset=["channel_id"])
df["channel_id_clean"] = df["channel_id"].str.replace("channel-", "", regex=True)
df = df[df["channel_id_clean"].str.isnumeric()]  # 数値のみを抽出
df["channel_id_clean"] = df["channel_id_clean"].astype(int)
available_channels = sorted(set(df["channel_id_clean"]))
print("利用可能なチャネルID:", ", ".join(map(str, available_channels)))

# ユーザー入力
if apply_filter:
    target_channel = input("対象のチャネル番号を入力してください (例: 0, 122, 208): ").strip()
    if not target_channel.isnumeric():
        print("無効な入力形式です。数値を入力してください。")
        exit()
    
    target_channel = int(target_channel)
    if target_channel not in available_channels:
        print("無効なチャネルIDが入力されました。利用可能なチャネルを確認してください。")
        exit()
else:
    target_channel = "all"

# フィルター適用
df_filtered = df[df["channel_id_clean"] == target_channel].copy() if apply_filter else df.copy()

# `send_time` と `ack_time` の "T" を スペース " " に置換
df_filtered["send_time"] = df_filtered["send_time"].astype(str).str.replace("T", " ", regex=False)
df_filtered["ack_time"] = df_filtered["ack_time"].astype(str).str.replace("T", " ", regex=False)

# 日付変換
df_filtered["send_time"] = pd.to_datetime(df_filtered["send_time"], errors="coerce")
df_filtered["ack_time"] = pd.to_datetime(df_filtered["ack_time"], errors="coerce")

# 欠損データの削除（NaT のデータを完全に除外）
before_drop = len(df_filtered)
df_filtered = df_filtered.dropna(subset=["send_time", "ack_time"])
after_drop = len(df_filtered)
print(f"欠損データが {before_drop - after_drop} 件削除されました。")

# 遅延を計算
df_filtered["delay"] = (df_filtered["ack_time"] - df_filtered["send_time"]).dt.total_seconds()

# 手数料データ (`fee_amount`) の処理
df_filtered["fee_amount"] = df_filtered["fee_amount"].astype(str).str.extract("([0-9]+)")
df_filtered["fee_amount"] = pd.to_numeric(df_filtered["fee_amount"], errors="coerce")

# 手数料データの欠損は無視（`NaN` のままプロット）

# プロット
plt.figure(figsize=(10, 6))
plt.scatter(df_filtered["delay"], df_filtered["fee_amount"], alpha=0.7, color='black', marker='x')
plt.xlabel("Delay (seconds)")
plt.ylabel("Fee Amount")
plt.title(f"Relationship between Delay and Fee Amount (Channel-{target_channel})")
plt.xlim(0, 50)
plt.grid(True)
plt.savefig(f"lim50_delay_vs_fee_channel_{target_channel}.png", dpi=300, bbox_inches="tight")

plt.figure(figsize=(10, 6))
plt.scatter(df_filtered["send_time"], df_filtered["fee_amount"], alpha=0.7, color='black', marker='x')
plt.xlabel("Send Time")
plt.ylabel("Fee Amount")
plt.title(f"Relationship between Send Time and Fee Amount (Channel-{target_channel})")
plt.xticks(rotation=45)
plt.grid(True)
plt.savefig(f"sendtime_vs_fee_channel_{target_channel}.png", dpi=300, bbox_inches="tight")

plt.figure(figsize=(10, 6))
plt.scatter(df_filtered["send_time"], df_filtered["delay"], alpha=0.7, color='black', marker='x')
plt.xlabel("Send Time")
plt.ylabel("Delay (seconds)")
plt.title(f"Relationship between Send Time and Delay (Channel-{target_channel})")
plt.xticks(rotation=45)
plt.grid(True)
plt.savefig(f"sendtime_vs_delay_channel_{target_channel}.png", dpi=300, bbox_inches="tight")

print("プロットが完了しました。")
