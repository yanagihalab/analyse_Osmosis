import pandas as pd
import requests
from datetime import datetime
import time
from tqdm import tqdm  # 進捗バーを表示するライブラリ

# APIのエンドポイント
BLOCK_HEADER_URL = "https://osmosis-rpc.publicnode.com/block?height="

# 設定: デバッグモード
DEBUG_MODE = False  # True: 詳細ログ, False: 最小限のログ

# APIのリクエスト制限
REQUEST_DELAY = 0.5  # APIの負荷を考慮して遅延
MAX_RETRIES = 30  # 500エラー時の最大リトライ回数
RETRY_DELAY = 2  # リトライ時の待機時間（秒）

def fetch_block_timestamp(height):
    """指定されたブロックのタイムスタンプを取得（500エラー時はリトライ）"""
    height = int(height)  # 確実に整数型に変換
    retries = 0

    while retries < MAX_RETRIES:
        try:
            response = requests.get(BLOCK_HEADER_URL + str(height), timeout=10)

            if response.status_code == 200:
                block_data = response.json()
                if "result" in block_data and "block" in block_data["result"]:
                    timestamp = block_data["result"]["block"]["header"]["time"]
                    timestamp = timestamp.replace("Z", "")  # "Z" を削除
                    parts = timestamp.split(".")
                    if len(parts) == 2:
                        microseconds = parts[1][:6]  # 6桁まで取得
                        microseconds = microseconds.ljust(6, "0")  # 足りない場合はゼロ埋め
                        timestamp = f"{parts[0]}.{microseconds}"
                    dt = datetime.fromisoformat(timestamp)

                    if DEBUG_MODE:
                        print(f"[DEBUG] Fetched timestamp for block {height}: {dt}")

                    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")  # ミリ秒までフォーマットして返す

            elif response.status_code == 500:
                print(f"[WARNING] Server error (500) for block {height}, retrying... ({retries + 1}/{MAX_RETRIES})")
                retries += 1
                time.sleep(RETRY_DELAY)  # リトライ前に待機
                continue  # 再試行

            else:
                print(f"Failed to fetch timestamp for block {height}, status code: {response.status_code}")
                return None

        except ValueError:
            print(f"[ERROR] Invalid timestamp format: {timestamp}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching timestamp for block {height}: {e}")
            return None

    print(f"[ERROR] Failed to retrieve timestamp for block {height} after {MAX_RETRIES} retries.")
    return None

def update_missing_times(input_file, output_file, debug_file="test.csv"):
    """
    `send_time` および `ack_time` が欠損している場合に、API から取得して補完する。
    途中経過を `test.csv` に追記する。
    """
    df = pd.read_csv(input_file)
    df["send_height"] = df["send_height"].astype("Int64")
    df["ack_height"] = df["ack_height"].astype("Int64")
    unique_send_heights = df["send_height"].dropna().unique()
    unique_ack_heights = df["ack_height"].dropna().unique()
    send_time_map = {}
    ack_time_map = {}

    with tqdm(total=len(unique_send_heights) + len(unique_ack_heights), desc="Processing", unit="req") as pbar:
        for height in unique_send_heights:
            if pd.isna(height) or height in send_time_map:
                continue
            timestamp = fetch_block_timestamp(height)
            if timestamp:
                send_time_map[height] = timestamp
                time.sleep(REQUEST_DELAY)
                if DEBUG_MODE:
                    pd.DataFrame([[height, timestamp]], columns=["send_height", "send_time"]).to_csv(debug_file, mode='a', header=False, index=False)
            pbar.update(1)

        for height in unique_ack_heights:
            if pd.isna(height) or height in ack_time_map:
                continue
            timestamp = fetch_block_timestamp(height)
            if timestamp:
                ack_time_map[height] = timestamp
                time.sleep(REQUEST_DELAY)
                if DEBUG_MODE:
                    pd.DataFrame([[height, timestamp]], columns=["ack_height", "ack_time"]).to_csv(debug_file, mode='a', header=False, index=False)
            pbar.update(1)

    df["send_time"] = df["send_height"].map(send_time_map)
    df["ack_time"] = df["ack_height"].map(ack_time_map)
    df.to_csv(output_file, index=False)
    print(f"send_time と ack_time を補完したデータを {output_file} に保存しました。")

update_missing_times("merged_output.csv", "updated_output.csv")

# import pandas as pd
# import requests
# from datetime import datetime
# import time
# from tqdm import tqdm  # 進捗バーを表示するライブラリ

# # APIのエンドポイント
# BLOCK_HEADER_URL = "https://osmosis-rpc.publicnode.com/block?height="

# # 設定: デバッグモード
# DEBUG_MODE = True  # True: 詳細ログ, False: 最小限のログ

# # APIのリクエスト制限
# REQUEST_DELAY = 0.5  # APIの負荷を考慮して遅延
# MAX_RETRIES = 5  # 500エラー時の最大リトライ回数
# RETRY_DELAY = 1  # リトライ時の待機時間（秒）

# def fetch_block_timestamp(height):
#     """指定されたブロックのタイムスタンプを取得（500エラー時はリトライ）"""
#     height = int(height)  # 確実に整数型に変換
#     retries = 0

#     while retries < MAX_RETRIES:
#         try:
#             response = requests.get(BLOCK_HEADER_URL + str(height), timeout=10)

#             if response.status_code == 200:
#                 block_data = response.json()
#                 if "result" in block_data and "block" in block_data["result"]:
#                     timestamp = block_data["result"]["block"]["header"]["time"]
#                     timestamp = timestamp.replace("Z", "")  # "Z" を削除
#                     parts = timestamp.split(".")
#                     if len(parts) == 2:
#                         microseconds = parts[1][:6]  # 6桁まで取得
#                         microseconds = microseconds.ljust(6, "0")  # 足りない場合はゼロ埋め
#                         timestamp = f"{parts[0]}.{microseconds}"
#                     dt = datetime.fromisoformat(timestamp)

#                     if DEBUG_MODE:
#                         print(f"[DEBUG] Fetched timestamp for block {height}: {dt}")

#                     return dt.strftime("%Y-%m-%d %H:%M:%S.%f")  # ミリ秒までフォーマットして返す

#             elif response.status_code == 500:
#                 print(f"[WARNING] Server error (500) for block {height}, retrying... ({retries + 1}/{MAX_RETRIES})")
#                 retries += 1
#                 time.sleep(RETRY_DELAY)  # リトライ前に待機
#                 continue  # 再試行

#             else:
#                 print(f"Failed to fetch timestamp for block {height}, status code: {response.status_code}")
#                 return None

#         except ValueError:
#             print(f"[ERROR] Invalid timestamp format: {timestamp}")
#             return None

#         except requests.exceptions.RequestException as e:
#             print(f"Error fetching timestamp for block {height}: {e}")
#             return None

#     print(f"[ERROR] Failed to retrieve timestamp for block {height} after {MAX_RETRIES} retries.")
#     return None

# def update_missing_times(input_file, output_file):
#     """
#     `send_time` および `ack_time` が欠損している場合に、API から取得して補完する。
#     :param input_file: str - 補完対象のCSVファイル
#     :param output_file: str - 更新後のCSVファイルの出力パス
#     """
#     # CSVデータの読み込み
#     df = pd.read_csv(input_file)

#     # `send_height` と `ack_height` を整数型に変換
#     df["send_height"] = df["send_height"].astype("Int64")
#     df["ack_height"] = df["ack_height"].astype("Int64")

#     # `send_height` と `ack_height` のユニークな値を取得（NaNを除外）
#     unique_send_heights = df["send_height"].dropna().unique()
#     unique_ack_heights = df["ack_height"].dropna().unique()

#     # 取得済みのブロックタイムスタンプをキャッシュする辞書
#     send_time_map = {}
#     ack_time_map = {}

#     if DEBUG_MODE:
#         print(f"[DEBUG] Processing {len(unique_send_heights)} unique send heights and {len(unique_ack_heights)} unique ack heights.")

#     # tqdmで進捗バーを作成
#     total_requests = len(unique_send_heights) + len(unique_ack_heights)  # 予想されるAPIリクエストの総数
#     with tqdm(total=total_requests, desc="Processing", unit="req") as pbar:
#         # `send_height` から `send_time` を取得
#         for height in unique_send_heights:
#             if pd.isna(height) or height in send_time_map:
#                 continue  # 既に取得済みならスキップ
#             timestamp = fetch_block_timestamp(height)
#             if timestamp:
#                 send_time_map[height] = timestamp
#                 time.sleep(REQUEST_DELAY)  # API制限を考慮して遅延
#             pbar.update(1)  # 進捗バーを更新

#         # `ack_height` から `ack_time` を取得
#         for height in unique_ack_heights:
#             if pd.isna(height) or height in ack_time_map:
#                 continue  # 既に取得済みならスキップ
#             timestamp = fetch_block_timestamp(height)
#             if timestamp:
#                 ack_time_map[height] = timestamp
#                 time.sleep(REQUEST_DELAY)  # API制限を考慮して遅延
#             pbar.update(1)  # 進捗バーを更新

#     # `send_time` と `ack_time` を適用（ミリ秒までフォーマット）
#     df["send_time"] = df["send_height"].map(send_time_map)
#     df["ack_time"] = df["ack_height"].map(ack_time_map)

#     # `ack_time` の `NaN` をカウント
#     missing_ack_time = df["ack_time"].isna().sum()
#     if DEBUG_MODE and missing_ack_time > 0:
#         print(f"[DEBUG] Warning: {missing_ack_time} rows still have missing ack_time!")

#     # CSV保存時のフォーマットを維持
#     df.to_csv(output_file, index=False)
#     print(f"send_time と ack_time を補完したデータを {output_file} に保存しました。")

# # 実行: 'merged_output.csv' の `send_time` と `ack_time` をAPIから取得して補完
# update_missing_times("merged_output.csv", "updated_output.csv")

# # import pandas as pd
# # import requests
# # from datetime import datetime
# # import time
# # from tqdm import tqdm  # 進捗バーを表示するライブラリ

# # # APIのエンドポイント
# # BLOCK_HEADER_URL = "https://osmosis-rpc.publicnode.com/block?height="

# # # 設定: デバッグモード
# # DEBUG_MODE = False  # True: 詳細ログ, False: 最小限のログ

# # # APIのリクエスト制限
# # REQUEST_DELAY = 0.5  # APIの負荷を考慮して遅延
# # MAX_RETRIES = 5  # 500エラー時の最大リトライ回数
# # RETRY_DELAY = 2  # リトライ時の待機時間（秒）

# # def fetch_block_timestamp(height):
# #     """指定されたブロックのタイムスタンプを取得（500エラー時はリトライ）"""
# #     height = int(height)  # 確実に整数型に変換
# #     retries = 0

# #     while retries < MAX_RETRIES:
# #         try:
# #             response = requests.get(BLOCK_HEADER_URL + str(height), timeout=10)

# #             if response.status_code == 200:
# #                 block_data = response.json()
# #                 if "result" in block_data and "block" in block_data["result"]:
# #                     timestamp = block_data["result"]["block"]["header"]["time"]
# #                     timestamp = timestamp.replace("Z", "")  # "Z" を削除
# #                     parts = timestamp.split(".")
# #                     if len(parts) == 2:
# #                         microseconds = parts[1][:6]  # 6桁まで取得
# #                         microseconds = microseconds.ljust(6, "0")  # 足りない場合はゼロ埋め
# #                         timestamp = f"{parts[0]}.{microseconds}"
# #                     dt = datetime.fromisoformat(timestamp)

# #                     if DEBUG_MODE:
# #                         print(f"[DEBUG] Fetched timestamp for block {height}: {dt}")

# #                     return dt.strftime("%Y-%m-%d %H:%M:%S")  # 文字列フォーマットで返す

# #             elif response.status_code == 500:
# #                 print(f"[WARNING] Server error (500) for block {height}, retrying... ({retries + 1}/{MAX_RETRIES})")
# #                 retries += 1
# #                 time.sleep(RETRY_DELAY)  # リトライ前に待機
# #                 continue  # 再試行

# #             else:
# #                 print(f"Failed to fetch timestamp for block {height}, status code: {response.status_code}")
# #                 return None

# #         except ValueError:
# #             print(f"[ERROR] Invalid timestamp format: {timestamp}")
# #             return None

# #         except requests.exceptions.RequestException as e:
# #             print(f"Error fetching timestamp for block {height}: {e}")
# #             return None

# #     print(f"[ERROR] Failed to retrieve timestamp for block {height} after {MAX_RETRIES} retries.")
# #     return None

# # def update_missing_times(input_file, output_file):
# #     """
# #     `send_time` および `ack_time` が欠損している場合に、API から取得して補完する。
# #     :param input_file: str - 補完対象のCSVファイル
# #     :param output_file: str - 更新後のCSVファイルの出力パス
# #     """
# #     # CSVデータの読み込み
# #     df = pd.read_csv(input_file)

# #     # `send_height` と `ack_height` を整数型に変換
# #     df["send_height"] = df["send_height"].astype("Int64")
# #     df["ack_height"] = df["ack_height"].astype("Int64")

# #     # `send_height` と `ack_height` のユニークな値を取得（NaNを除外）
# #     unique_send_heights = df["send_height"].dropna().unique()
# #     unique_ack_heights = df["ack_height"].dropna().unique()

# #     # 取得済みのブロックタイムスタンプをキャッシュする辞書
# #     send_time_map = {}
# #     ack_time_map = {}

# #     if DEBUG_MODE:
# #         print(f"[DEBUG] Processing {len(unique_send_heights)} unique send heights and {len(unique_ack_heights)} unique ack heights.")

# #     # tqdmで進捗バーを作成
# #     total_requests = len(unique_send_heights) + len(unique_ack_heights)  # 予想されるAPIリクエストの総数
# #     with tqdm(total=total_requests, desc="Processing", unit="req") as pbar:
# #         # `send_height` から `send_time` を取得
# #         for height in unique_send_heights:
# #             if pd.isna(height) or height in send_time_map:
# #                 continue  # 既に取得済みならスキップ
# #             timestamp = fetch_block_timestamp(height)
# #             if timestamp:
# #                 send_time_map[height] = timestamp
# #                 time.sleep(REQUEST_DELAY)  # API制限を考慮して遅延
# #             pbar.update(1)  # 進捗バーを更新

# #         # `ack_height` から `ack_time` を取得
# #         for height in unique_ack_heights:
# #             if pd.isna(height) or height in ack_time_map:
# #                 continue  # 既に取得済みならスキップ
# #             timestamp = fetch_block_timestamp(height)
# #             if timestamp:
# #                 ack_time_map[height] = timestamp
# #                 time.sleep(REQUEST_DELAY)  # API制限を考慮して遅延
# #             pbar.update(1)  # 進捗バーを更新

# #     # `send_time` と `ack_time` を適用
# #     df["send_time"] = df["send_height"].map(send_time_map)
# #     df["ack_time"] = df["ack_height"].map(ack_time_map)

# #     # `ack_time` の `NaN` をカウント
# #     missing_ack_time = df["ack_time"].isna().sum()
# #     if DEBUG_MODE and missing_ack_time > 0:
# #         print(f"[DEBUG] Warning: {missing_ack_time} rows still have missing ack_time!")

# #     # `ack_time` を文字列型に変換（CSV保存時の誤変換防止）
# #     df["ack_time"] = df["ack_time"].astype(str)

# #     # 更新されたデータをCSVに出力
# #     df.to_csv(output_file, index=False)
# #     print(f"send_time と ack_time を補完したデータを {output_file} に保存しました。")

# # # 実行: 'merged_output.csv' の `send_time` と `ack_time` をAPIから取得して補完
# # update_missing_times("merged_output.csv", "updated_output.csv")
