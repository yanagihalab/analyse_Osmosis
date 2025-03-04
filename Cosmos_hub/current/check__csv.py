import pandas as pd
import os
import glob

def merge_all_csv_in_directory(directory, output_file):
    """
    指定ディレクトリ内のすべてのCSVファイルを統合し、完全に一致する行を削除する関数
    カラムの順番を固定する。

    :param directory: str - CSVファイルが保存されているディレクトリ
    :param output_file: str - 統合後のCSVファイルの出力パス
    """
    # ディレクトリ内のすべてのCSVファイルを取得
    csv_files = glob.glob(os.path.join(directory, "*.csv"))

    if not csv_files:
        print("CSVファイルが見つかりません。")
        return

    # 空でないデータフレームのみをリストに追加
    df_list = []
    for file in csv_files:
        df = pd.read_csv(file)

        # 空のデータフレームを除外
        if not df.empty:
            df_list.append(df)

    if not df_list:
        print("統合可能なデータがありません。")
        return

    # 指定されたカラムの順番
    desired_columns = ['channel_id', 'sequence', 'send_height', 'send_time', 
                       'ack_height', 'ack_time', 'block_delay', 'fee_amount', 'fee_denom']

    # カラムを統一（足りないカラムは NaN で埋める）
    df_list = [df.reindex(columns=desired_columns, fill_value=None) for df in df_list]

    # データを統合
    merged_df = pd.concat(df_list, ignore_index=True)
    print(f"統合前のデータ行数: {len(merged_df)}")

    # 完全一致する行を削除（最初の1つを残す）
    deduplicated_df = merged_df.drop_duplicates(keep='first')
    print(f"統合後のデータ行数: {len(deduplicated_df)}")

    # 結果をCSVに出力（指定カラム順で保存）
    deduplicated_df.to_csv(output_file, index=False, columns=desired_columns)
    print(f"統合されたCSVファイルを {output_file} に保存しました。")

# current/ ディレクトリのCSVファイルを統合し、完全一致する行を削除
merge_all_csv_in_directory('/home/admin-y/tmp/analyse_osmosis/current', 'merged_output.csv')
