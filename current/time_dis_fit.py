import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

NUMBER_OF_TRIALS = 10000
MEMPOOL_WAIT_FREQUENCY = 0.5
NBINS = 100
MU = 0.0066*180*np.log(180)
BETA = 0.006*180

def gumbel(x, mu, eta):
    return (1/eta) * np.exp( -(x-mu)/eta ) * np.exp( - np.exp( -(x-mu)/eta ) )

def frechet(x, mu, eta, alpha):
    return (alpha / eta) * np.power( ((x-mu) / eta), -1-alpha ) * np.exp( - np.power( ((x-mu) / eta), -alpha) )

def normal(x, mu, sigma):
    return (1 / (np.sqrt(2*np.pi) * sigma)) * np.exp( - ((x - mu)**2 / (2*(sigma**2))) )

# Load and process CSV data 
df = pd.read_csv("ibc_time_delay_analysis_0.csv")
df["send_time"] = pd.to_datetime(df["send_time"], errors='coerce')
df["ack_time"] = pd.to_datetime(df["ack_time"], errors='coerce')
df = df.dropna(subset=["send_time", "ack_time"])
df["time_delay_sec"] = (df["ack_time"] - df["send_time"]).dt.total_seconds()
for i in df["time_delay_sec"]:
    print(i)
n, bins, _ = plt.hist(df["time_delay_sec"], bins=NBINS, density=True, label='data')
bins_mod = [(bins[i] + bins[i+1]) / 2 for i in range(len(bins)-1)]

# # Normalize data
# bins_mod = (bins_mod - np.mean(bins_mod)) / np.std(bins_mod)
# n = (n - np.mean(n)) / np.std(n)

# # Fit Gumbel distribution
# p0 = [0, 1]
# popt, pcov = curve_fit(gumbel, bins_mod, n, p0=p0, maxfev=10000)
# print('gumbel:', popt, pcov)
# gumbel_x_fit = np.linspace(min(bins_mod), max(bins_mod), NBINS)
# gumbel_y_fit = gumbel(gumbel_x_fit, *popt)
# plt.plot(gumbel_x_fit, gumbel_y_fit, label='fitted gumbel dist.')
# gumbel_error_tmp = np.sum((n - gumbel_y_fit)**2)
# gumbel_AIC = gumbel_error_tmp / np.var(n) + 2*2
# print('gumbel mean squared error:', np.sqrt(gumbel_error_tmp))
# print('gumbel AIC:', gumbel_AIC)

# # Fit Frechet distribution
# p0 = [0, 1, 1]
# popt, pcov = curve_fit(frechet, bins_mod, n, p0=p0, maxfev=10000)
# print('frechet:', popt, pcov)
# frechet_x_fit = np.linspace(min(bins_mod), max(bins_mod), NBINS)
# frechet_y_fit = frechet(frechet_x_fit, *popt)
# plt.plot(frechet_x_fit, frechet_y_fit, label='fitted frechet dist.')
# frechet_error_tmp = np.sum((n - frechet_y_fit)**2)
# frechet_AIC = frechet_error_tmp / np.var(n) + 2*3
# print('frechet mean squared error:', np.sqrt(frechet_error_tmp))
# print('frechet AIC:', frechet_AIC)

# # Fit Normal distribution
# p0 = [0, 1]
# popt, pcov = curve_fit(normal, bins_mod, n, p0=p0, maxfev=10000)
# print('normal:', popt, pcov)
# normal_x_fit = np.linspace(min(bins_mod), max(bins_mod), NBINS)
# normal_y_fit = normal(normal_x_fit, *popt)
# plt.plot(normal_x_fit, normal_y_fit, label='fitted normal dist.')
# normal_error_tmp = np.sum((n - normal_y_fit)**2)
# normal_AIC = normal_error_tmp / np.var(n) + 2*2 
# print('normal mean squared error:', np.sqrt(normal_error_tmp))
# print('normal AIC:', normal_AIC)

plt.xlabel('IBC token transfer time')
plt.ylabel('density')
plt.xlim(0, 100)
plt.legend()
plt.savefig('transfer_time.png')
plt.savefig('cosmos_ibc_token_transfer_time.eps', transparent=False)
plt.clf()
