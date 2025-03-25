import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import mpmath  # Fréchetのガンマ関数計算で便利（scipy.special.gammaでも可）

NBINS = 500

def gumbel(x, mu, eta):
    return (1/eta) * np.exp(-(x-mu)/eta) * np.exp(-np.exp(-(x-mu)/eta))

def frechet(x, mu, eta, alpha):
    """
    mu: 位置パラメータ
    eta: スケールパラメータ (> 0)
    alpha: 形状パラメータ (> 0)
    """
    eta = np.abs(eta) + 1e-6
    alpha = np.abs(alpha) + 1e-6
    valid_mask = (x > mu)
    y = np.zeros_like(x)
    # pdf = alpha/eta * ((x - mu)/eta)^(-1 - alpha) * exp(-((x - mu)/eta)^(-alpha))  for x > mu
    y[valid_mask] = (alpha / eta) * ((x[valid_mask] - mu) / eta)**(-1 - alpha) \
                    * np.exp(-((x[valid_mask] - mu) / eta)**(-alpha))
    return y

def normal(x, mu, sigma):
    return (1 / (np.sqrt(2 * np.pi) * sigma)) * np.exp(-((x - mu)**2) / (2 * sigma**2))

# CSVの読み込み
df = pd.read_csv("ibc_time_delay_analysis_0.csv")
df["send_time"] = pd.to_datetime(df["send_time"], errors='coerce')
df["ack_time"] = pd.to_datetime(df["ack_time"], errors='coerce')

df = df.dropna(subset=["send_time", "ack_time"])
df["time_delay_sec"] = (df["ack_time"] - df["send_time"]).dt.total_seconds()

# ヒストグラムの作成（確率密度）
n, bins, _ = plt.hist(df["time_delay_sec"], bins=NBINS, density=True, 
                      label='Data', alpha=0.6, color='blue')

# bin の中央値を取得
bins_mod = 0.5 * (bins[:-1] + bins[1:])

#---------------------------#
#    1. Gumbel 分布
#---------------------------#
p0_gumbel = [bins_mod[np.argmax(n)], np.std(df["time_delay_sec"])]
popt_gumbel, _ = curve_fit(gumbel, bins_mod, n, p0=p0_gumbel, maxfev=10000)
gumbel_mu, gumbel_eta = popt_gumbel

# 平均, 分散, 標準偏差を計算
gumbel_mean = gumbel_mu + 0.5772156649 * gumbel_eta  # gamma ≈ 0.5772
gumbel_var = (np.pi**2 / 6.0) * (gumbel_eta**2)
gumbel_std = np.sqrt(gumbel_var)

print("---------- Gumbel ----------")
print(f"Fitted parameters: mu={gumbel_mu:.4f}, eta={gumbel_eta:.4f}")
print(f"Mean    = {gumbel_mean:.4f}")
print(f"Variance= {gumbel_var:.4f}")
print(f"Std Dev = {gumbel_std:.4f}")

# 描画用
gumbel_x_fit = np.linspace(bins_mod.min(), bins_mod.max(), 300)
gumbel_y_fit = gumbel(gumbel_x_fit, *popt_gumbel)
plt.plot(gumbel_x_fit, gumbel_y_fit, label='Fitted Gumbel', color='orange', linewidth=2)

#---------------------------#
#    2. Fréchet 分布
#---------------------------#
p0_frechet = [
    np.min(df["time_delay_sec"]), 
    (np.percentile(df["time_delay_sec"], 75) - np.percentile(df["time_delay_sec"], 25)), 
    4.5
]
try:
    popt_frechet, _ = curve_fit(
        frechet, bins_mod, n, p0=p0_frechet, 
        bounds=([0, 0, 0.1], [np.inf, np.inf, np.inf]), 
        maxfev=10000
    )
    frechet_mu, frechet_eta, frechet_alpha = popt_frechet
    
    print("---------- Fréchet ----------")
    print(f"Fitted parameters: mu={frechet_mu:.4f}, eta={frechet_eta:.4f}, alpha={frechet_alpha:.4f}")
    
    # Fréchet分布の平均・分散(存在すれば)を計算
    if frechet_alpha > 1:
        frechet_mean = frechet_mu + frechet_eta * mpmath.gamma(1 - 1.0/frechet_alpha)
    else:
        frechet_mean = float('nan')  # 存在しない
    
    if frechet_alpha > 2:
        term1 = mpmath.gamma(1 - 2.0/frechet_alpha)
        term2 = mpmath.gamma(1 - 1.0/frechet_alpha)
        frechet_var = (frechet_eta**2) * (term1 - term2**2)
        frechet_std = float(mpmath.sqrt(frechet_var))
    else:
        frechet_var = float('nan')  # 存在しない
        frechet_std = float('nan')
    
    print(f"Mean    = {frechet_mean:.4f}" if not np.isnan(frechet_mean) else "Mean    = 不存在(α ≤ 1)")
    print(f"Variance= {frechet_var:.4f}" if not np.isnan(frechet_var) else "Variance= 不存在(α ≤ 2)")
    print(f"Std Dev = {frechet_std:.4f}" if not np.isnan(frechet_std) else "Std Dev = 不存在(α ≤ 2)")
    
    # 描画用
    frechet_x_fit = np.linspace(bins_mod.min(), bins_mod.max(), 300)
    frechet_y_fit = frechet(frechet_x_fit, *popt_frechet)
    plt.plot(frechet_x_fit, frechet_y_fit, label='Fitted Frechet', color='green', linewidth=2)

except Exception as e:
    print("Frechet fit failed:", e)

#---------------------------#
#    3. 正規分布
#---------------------------#
p0_normal = [bins_mod[np.argmax(n)], np.std(df["time_delay_sec"])]
popt_normal, _ = curve_fit(normal, bins_mod, n, p0=p0_normal, 
                           bounds=([0, 0], [np.inf, np.inf]), 
                           maxfev=10000)
normal_mu, normal_sigma = popt_normal

# 平均, 分散, 標準偏差を計算
normal_mean = normal_mu
normal_var = normal_sigma**2
normal_std = normal_sigma

print("---------- Normal ----------")
print(f"Fitted parameters: mu={normal_mu:.4f}, sigma={normal_sigma:.4f}")
print(f"Mean    = {normal_mean:.4f}")
print(f"Variance= {normal_var:.4f}")
print(f"Std Dev = {normal_std:.4f}")

# 描画用
normal_x_fit = np.linspace(bins_mod.min(), bins_mod.max(), 300)
normal_y_fit = normal(normal_x_fit, *popt_normal)
plt.plot(normal_x_fit, normal_y_fit, label='Fitted Normal', color='red', linewidth=3)

#---------------------------#
#    プロット仕上げ
#---------------------------#
plt.xlabel('Time Delay (seconds)')
plt.ylabel('Probability Density')
plt.xlim(0, 100)
plt.legend()
plt.title("Distribution of Time Delay (seconds)")
plt.grid(True)
plt.savefig('transfer_time_improved.png')
plt.show()
