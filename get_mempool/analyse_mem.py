import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

CSV_FILE = "unconfirmed_txs.csv"
NORMAL_SCATTER_FILE = "normal_scatter.png"
SEMI_LOG_SCATTER_FILE = "semilog_scatter.png"  # 片対数プロット（点）
NORMAL_BAR_FILE = "normal_bar.png"
SEMI_LOG_BAR_FILE = "semilog_bar.png"  # 片対数プロット（棒）

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

        # 0を避けるために1を足して対数変換（log(0)は定義されないため）
        df["n_txs_log"] = df["n_txs"] + 1

        # X軸の間隔を均等にするためのインデックス
        x_indexes = np.arange(len(df))

        # --- (1) 通常の点プロット ---
        plt.figure(figsize=(10, 5))
        plt.scatter(x_indexes, df["n_txs"], label="n_txs", color="red", alpha=0.8)
        plt.xlabel("Timestamp")
        plt.ylabel("Value")
        plt.legend()
        plt.title("Unconfirmed Transactions Over Time (Normal Scatter)")
        plt.xticks(x_indexes[::max(len(x_indexes)//10, 1)], df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")[::max(len(x_indexes)//10, 1)], rotation=45)
        plt.grid(True, linestyle="--", linewidth=0.5)
        plt.savefig(NORMAL_SCATTER_FILE)  # 画像を保存
        print(f"通常の点プロットを保存: {NORMAL_SCATTER_FILE}")

        # --- (2) 片対数の点プロット (Y軸のみ対数) ---
        plt.figure(figsize=(10, 5))
        plt.scatter(x_indexes, df["n_txs_log"], label="n_txs (log)", color="red", alpha=0.8)
        plt.xlabel("Timestamp")
        plt.ylabel("Log Value")
        plt.yscale("log")  # Y軸のみ対数スケール
        plt.legend()
        plt.title("Unconfirmed Transactions Over Time (Semi-Log Scatter)")
        plt.xticks(x_indexes[::max(len(x_indexes)//10, 1)], df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")[::max(len(x_indexes)//10, 1)], rotation=45)
        plt.grid(True, which="both", linestyle="--", linewidth=0.5)
        plt.savefig(SEMI_LOG_SCATTER_FILE)  # 画像を保存
        print(f"片対数の点プロットを保存: {SEMI_LOG_SCATTER_FILE}")

        # --- (3) 通常の棒グラフ ---
        plt.figure(figsize=(10, 5))
        plt.bar(x_indexes, df["n_txs"], label="n_txs", alpha=0.6, color="blue")
        plt.xlabel("Timestamp")
        plt.ylabel("Value")
        plt.legend()
        plt.title("Unconfirmed Transactions Over Time (Normal Bar)")
        plt.xticks(x_indexes[::max(len(x_indexes)//10, 1)], df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")[::max(len(x_indexes)//10, 1)], rotation=45)
        plt.grid(True, linestyle="--", linewidth=0.5)
        plt.savefig(NORMAL_BAR_FILE)  # 画像を保存
        print(f"通常の棒グラフを保存: {NORMAL_BAR_FILE}")

        # --- (4) 片対数の棒グラフ (Y軸のみ対数) ---
        plt.figure(figsize=(10, 5))
        plt.bar(x_indexes, df["n_txs_log"], label="n_txs (log)", alpha=0.6, color="blue")
        plt.xlabel("Timestamp")
        plt.ylabel("Log Value")
        plt.yscale("log")  # Y軸のみ対数スケール
        plt.legend()
        plt.title("Unconfirmed Transactions Over Time (Semi-Log Bar)")
        plt.xticks(x_indexes[::max(len(x_indexes)//10, 1)], df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")[::max(len(x_indexes)//10, 1)], rotation=45)
        plt.grid(True, which="both", linestyle="--", linewidth=0.5)
        plt.savefig(SEMI_LOG_BAR_FILE)  # 画像を保存
        print(f"片対数の棒グラフを保存: {SEMI_LOG_BAR_FILE}")


    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    analyze_csv()
