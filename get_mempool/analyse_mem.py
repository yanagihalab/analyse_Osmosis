import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

CSV_FILE = "unconfirmed_txs.csv"

# ファイル名の設定
NORMAL_SCATTER_N_TXS = "normal_scatter_n_txs.png"
SEMI_LOG_SCATTER_N_TXS = "semilog_scatter_n_txs.png"
NORMAL_BAR_N_TXS = "normal_bar_n_txs.png"
SEMI_LOG_BAR_N_TXS = "semilog_bar_n_txs.png"
NORMAL_HIST_N_TXS = "normal_hist_n_txs.png"
SEMI_LOG_HIST_N_TXS = "semilog_hist_n_txs.png"

NORMAL_SCATTER_TOTAL_BYTES = "normal_scatter_total_bytes.png"
SEMI_LOG_SCATTER_TOTAL_BYTES = "semilog_scatter_total_bytes.png"
NORMAL_BAR_TOTAL_BYTES = "normal_bar_total_bytes.png"
SEMI_LOG_BAR_TOTAL_BYTES = "semilog_bar_total_bytes.png"
NORMAL_HIST_TOTAL_BYTES = "normal_hist_total_bytes.png"
SEMI_LOG_HIST_TOTAL_BYTES = "semilog_hist_total_bytes.png"

def analyze_csv():
    try:
        # CSVファイルを読み込む
        df = pd.read_csv(CSV_FILE, parse_dates=["timestamp"])

        # データの確認
        print("データの先頭行:")
        print(df.head())

        # データの統計情報
        print("\nデータの基本統計量:")
        print(df.describe())

        # 数値型に変換
        df["n_txs"] = pd.to_numeric(df["n_txs"], errors="coerce")
        df["total_bytes"] = pd.to_numeric(df["total_bytes"], errors="coerce")

        # 0を避けるために1を足して対数変換
        df["n_txs_log"] = df["n_txs"] + 1
        df["total_bytes_log"] = df["total_bytes"] + 1

        # X軸の間隔を均等にするためのインデックス
        x_indexes = np.arange(len(df))

        # ==== 散布図 & 棒グラフ & ヒストグラム ====
        for metric, normal_scatter, semilog_scatter, normal_bar, semilog_bar, normal_hist, semilog_hist in [
            ("n_txs", NORMAL_SCATTER_N_TXS, SEMI_LOG_SCATTER_N_TXS, NORMAL_BAR_N_TXS, SEMI_LOG_BAR_N_TXS, NORMAL_HIST_N_TXS, SEMI_LOG_HIST_N_TXS),
            ("total_bytes", NORMAL_SCATTER_TOTAL_BYTES, SEMI_LOG_SCATTER_TOTAL_BYTES, NORMAL_BAR_TOTAL_BYTES, SEMI_LOG_BAR_TOTAL_BYTES, NORMAL_HIST_TOTAL_BYTES, SEMI_LOG_HIST_TOTAL_BYTES)
        ]:
            # --- (1) 通常の散布図 ---
            plt.figure(figsize=(10, 5))
            plt.scatter(x_indexes, df[metric], label=f"{metric} (scatter)", color="red", alpha=0.7)
            plt.xlabel("Timestamp")
            plt.ylabel("Value")
            plt.title(f"Unconfirmed Transactions ({metric}) - Normal Scatter")
            plt.xticks(rotation=45)
            plt.grid(True, linestyle="--", linewidth=0.5)
            plt.savefig(normal_scatter)
            print(f"通常の散布図を保存: {normal_scatter}")

            # --- (2) 片対数の散布図 (Y軸のみ対数) ---
            plt.figure(figsize=(10, 5))
            plt.scatter(x_indexes, df[f"{metric}_log"], label=f"{metric} (scatter, log)", color="red", alpha=0.7)
            plt.xlabel("Timestamp")
            plt.ylabel("Log Value")
            plt.yscale("log")
            plt.title(f"Unconfirmed Transactions ({metric}) - Semi-Log Scatter")
            plt.xticks(rotation=45)
            plt.grid(True, which="both", linestyle="--", linewidth=0.5)
            plt.savefig(semilog_scatter)
            print(f"片対数の散布図を保存: {semilog_scatter}")

            # --- (3) 通常の棒グラフ ---
            plt.figure(figsize=(10, 5))
            plt.bar(x_indexes, df[metric], label=f"{metric} (bar)", alpha=0.6, color="blue")
            plt.xlabel("Timestamp")
            plt.ylabel("Value")
            plt.title(f"Unconfirmed Transactions ({metric}) - Normal Bar")
            plt.xticks(rotation=45)
            plt.grid(True, linestyle="--", linewidth=0.5)
            plt.savefig(normal_bar)
            print(f"通常の棒グラフを保存: {normal_bar}")

            # --- (4) 片対数の棒グラフ (Y軸のみ対数) ---
            plt.figure(figsize=(10, 5))
            plt.bar(x_indexes, df[f"{metric}_log"], label=f"{metric} (bar, log)", alpha=0.6, color="blue")
            plt.xlabel("Timestamp")
            plt.ylabel("Log Value")
            plt.yscale("log")
            plt.title(f"Unconfirmed Transactions ({metric}) - Semi-Log Bar")
            plt.xticks(rotation=45)
            plt.grid(True, which="both", linestyle="--", linewidth=0.5)
            plt.savefig(semilog_bar)
            print(f"片対数の棒グラフを保存: {semilog_bar}")

            # --- (5) 通常のヒストグラム ---
            plt.figure(figsize=(10, 5))
            plt.hist(df[metric], bins=30, alpha=0.7, color="green", edgecolor="black")
            plt.xlabel("Value")
            plt.ylabel("Frequency")
            plt.title(f"Frequency Distribution of {metric} - Normal Histogram")
            plt.grid(True, linestyle="--", linewidth=0.5)
            plt.savefig(normal_hist)
            print(f"通常のヒストグラムを保存: {normal_hist}")

            # --- (6) 片対数のヒストグラム (Y軸のみ対数) ---
            plt.figure(figsize=(10, 5))
            plt.hist(df[f"{metric}_log"], bins=30, alpha=0.7, color="green", edgecolor="black")
            plt.xlabel("Log Value")
            plt.ylabel("Frequency")
            plt.yscale("log")
            plt.title(f"Frequency Distribution of {metric} - Semi-Log Histogram")
            plt.grid(True, which="both", linestyle="--", linewidth=0.5)
            plt.savefig(semilog_hist)
            print(f"片対数のヒストグラムを保存: {semilog_hist}")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    analyze_csv()
