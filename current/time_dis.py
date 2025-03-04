import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# フィルターモードを選択
filter_mode = input("フィルターを適用しますか？ (yes/no): ").strip().lower()
apply_filter = filter_mode in ["yes", "y"]

# チャネルを指定してデータを取得
base_file = "updated_output"
target_csv = base_file + ".csv"
df = pd.read_csv(target_csv)

# 各チャネルのIBCトランザクション数を集計
top7_channels = df["channel_id"].value_counts().head(7)
print("Top 7 IBC Channels:")
print(top7_channels)

available_channels = sorted(set(df["channel_id"].str.replace("channel-", "").astype(int)))
print("利用可能なチャネルID:", ", ".join(map(str, available_channels)))

if apply_filter:
    target_channel = input("対象のチャネル番号を入力してください (例: 0, 122, 208): ").strip()
    if target_channel not in map(str, available_channels):
        print("無効なチャネルIDが入力されました。利用可能なチャネルを確認してください。")
        exit()
else:
    target_channel = None

# 指定チャネルのデータをフィルタリング
if target_channel:
    df = df[df["channel_id"] == f"channel-{target_channel}"]

# 差分計算
df["send_time"] = pd.to_datetime(df["send_time"], errors='coerce')
df["ack_time"] = pd.to_datetime(df["ack_time"], errors='coerce')

# NaNの処理
df = df.dropna(subset=["send_time", "ack_time"])

df["time_delay_sec"] = (df["ack_time"] - df["send_time"]).dt.total_seconds()
df["block_delay"] = df["ack_height"] - df["send_height"]

# 結果を保存
output_csv = f"ibc_time_delay_analysis_{target_channel if target_channel else 'all'}.csv"
df.to_csv(output_csv, index=False)
print(f"CSV file saved: {output_csv}")

# 大幅な外れ値の除去（3σルールを適用）
def remove_extreme_outliers(data):
    mean = data.mean()
    std_dev = data.std()
    lower_bound = mean - 3 * std_dev
    upper_bound = mean + 3 * std_dev
    return data[(data >= lower_bound) & (data <= upper_bound)]

df = df[df["time_delay_sec"].between(df["time_delay_sec"].mean() - 3 * df["time_delay_sec"].std(),
                                       df["time_delay_sec"].mean() + 3 * df["time_delay_sec"].std())]

valid_data_count = len(df)
print(f"Valid data count after extreme outlier removal: {valid_data_count}")


# ヒストグラムの描画
def plot_histogram(data, xlabel, title, filename):
    if data.dropna().empty:
        print(f"No valid data available for {title}, skipping histogram.")
        return
    
    # binsの適切な設定（Freedman-Diaconisルール）
    q25, q75 = np.percentile(data.dropna(), [25, 75])
    bin_width = 2 * (q75 - q25) / (len(data) ** (1/3))
    bins = max(10, int((data.max() - data.min()) / bin_width))
    
    plt.figure(figsize=(10, 6))
    plt.hist(data.dropna(), bins=bins, edgecolor='black', alpha=0.7)
    plt.xlabel(xlabel)
    plt.ylabel("Frequency")
    plt.title(title)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # x軸の範囲を0から95%分位点までに設定（隙間をなくすために調整）
    lower_bound = 0
    upper_bound = data.quantile(0.99) + 30
    plt.xlim(lower_bound, upper_bound if upper_bound > lower_bound else None)
    
    plt.savefig(filename)
    print(f"Histogram saved as {filename}")
    plt.close()

# ヒストグラムの作成
plot_histogram(df["time_delay_sec"], "Time Delay (seconds)", "Distribution of Time Delay (seconds)",
               f"time_delay_distribution_{base_file}_{target_channel if target_channel else 'all'}.png")
plot_histogram(df["block_delay"], "Block Delay (blocks)", "Distribution of Block Delay (blocks)",
               f"block_delay_distribution_{base_file}_{target_channel if target_channel else 'all'}.png")
