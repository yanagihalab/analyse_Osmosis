import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

NUMBER_OF_TRIALS = 50000
MEMPOOL_WAIT_FREQUENCY = 0.5
#MEMPOOL_WAIT_FREQUENCY = 0.0
NBINS = 1000
MU = 0.0066*180*np.log(180)
BETA = 0.006*180
# MU   = 1.3
# BETA = 0.2

# フィルターモードを選択
filter_mode = input("フィルターを適用しますか？ (yes/no): ").strip().lower()
apply_filter = filter_mode in ["yes", "y"]

# チャネルを指定してデータを取得
base_file = "Cosmos_merged_output"
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

def gumbel(x, mu, eta):
    return (1/eta) * np.exp( -(x-mu)/eta ) * np.exp( - np.exp( -(x-mu)/eta ) )

def frechet(x, mu, eta, alpha):
    return (alpha / eta) * np.power( ((x-mu) / eta), -1-alpha ) * np.exp( - np.power( ((x-mu) / eta), -alpha) )

def normal(x, mu, sigma):
    return (1 / (np.sqrt(2*np.pi) * sigma)) * np.exp( - ((x - mu)**2 / (2*(sigma**2))) )

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

df_list = df["time_delay_sec"].tolist()
# print(type(df_list))
# print(df_list)

filename = f"time_delay_distribution_{base_file}_{target_channel if target_channel else 'all'}.png"

ibc_transfer_times_list = []
rng = np.random.default_rng()
for _ in range(NUMBER_OF_TRIALS):
    block_time = rng.gumbel(MU, BETA)
    block_time_lag = block_time * np.random.rand()
    #print(block_time_lag)
    mempool_waiting_time = 0.0
    while np.random.rand() < MEMPOOL_WAIT_FREQUENCY:
        mempool_waiting_time += block_time * np.random.rand()
    #print(mempool_waiting_time)
    sampled_diff_time = np.random.choice(df_list)
    #print(sampled_diff_time)

    ibc_transfer_time = block_time_lag + mempool_waiting_time + sampled_diff_time
    ibc_transfer_times_list.append(ibc_transfer_time)
#print(ibc_transfer_times_list, len(ibc_transfer_times_list))

n, bins, patches = plt.hist(ibc_transfer_times_list, bins=NBINS, density=True, label='data')
#plt.show()

bins_mod = []
for i in range(len(bins)-1):
    bins_mod.append( (bins[i] + bins[i+1])/2 )

# gumbel
p0 = [1, 1]
popt, pcov = curve_fit(gumbel, bins_mod, n, p0=p0)
print('gumbel:', popt, pcov)
gumbel_x_fit = np.linspace(min(bins_mod), max(bins_mod), NBINS)
gumbel_y_fit = gumbel(gumbel_x_fit, *popt)
plt.plot(gumbel_x_fit, gumbel_y_fit, label='fitted gumbel dist.', lw=4)
gumbel_error_tmp = 0.0
for i in range(len(n)):
    gumbel_error_tmp += (n[i] - gumbel_y_fit[i])**2
gumbel_AIC = gumbel_error_tmp / np.var(n) + 2*2
print('gumbel mean squared error:', np.sqrt(gumbel_error_tmp))
print('gumbel AIC:', gumbel_AIC)

# frechet
p0 = [1, 1, 1]
popt, pcov = curve_fit(frechet, bins_mod, n, p0=p0)
print('frechet:', popt, pcov)
frechet_x_fit = np.linspace(min(bins_mod), max(bins_mod), NBINS)
frechet_y_fit = frechet(frechet_x_fit, *popt)
plt.plot(frechet_x_fit, frechet_y_fit, label='fitted frechet dist.')
frechet_error_tmp = 0.0
for i in range(len(n)):
    frechet_error_tmp += (n[i] - frechet_y_fit[i])**2
print('frechet mean squared error:', np.sqrt(frechet_error_tmp))
frechet_AIC = frechet_error_tmp / np.var(n) + 2*3
print('frechet AIC:', frechet_AIC)

# normal
#p0 = [1, 1]
p0 = [10, 1]
popt, pcov = curve_fit(normal, bins_mod, n, p0=p0)
print('normal:', popt, pcov)
normal_x_fit = np.linspace(min(bins_mod), max(bins_mod), NBINS)
normal_y_fit = normal(normal_x_fit, *popt)
plt.plot(normal_x_fit, normal_y_fit, label='fitted normal dist.')
normal_error_tmp = 0.0
for i in range(len(n)):
    normal_error_tmp += (n[i] - normal_y_fit[i])**2
print('normal mean squared error:', np.sqrt(normal_error_tmp))
normal_AIC = normal_error_tmp / np.var(n) + 2*2 
print('normal AIC:', normal_AIC)
print(len(n))

# plt.figure(figsize=(10, 6))
# plt.hist(data.dropna(), bins=bins, edgecolor='black', alpha=0.7)
# plt.xlabel(xlabel)
# plt.ylabel("Frequency")
# plt.title(title)
# plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.xlabel('IBC token transfer time')
plt.ylabel('density')
plt.legend()
# x軸の範囲を0から95%分位点までに設定（隙間をなくすために調整）
lower_bound = 0
upper_bound = upper_bound = df["time_delay_sec"].quantile(0.99) + 30
plt.xlim(lower_bound, upper_bound if upper_bound > lower_bound else None)
plt.savefig(filename)
print(f"Histogram saved as {filename}")



# # ヒストグラムの作成
# plot_histogram(df["time_delay_sec"], "Time Delay (seconds)", "Distribution of Time Delay (seconds)",
#                f"time_delay_distribution_{base_file}_{target_channel if target_channel else 'all'}.png")
# plot_histogram(df["block_delay"], "Block Delay (blocks)", "Distribution of Block Delay (blocks)",
#                f"block_delay_distribution_{base_file}_{target_channel if target_channel else 'all'}.png")
