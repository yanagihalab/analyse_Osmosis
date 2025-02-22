# IBC Transaction Analysis Tool / IBC トランザクション分析ツール

## Overview / 概要

This script analyzes IBC (Inter-Blockchain Communication) transactions on the Osmosis blockchain. It processes a CSV file containing transaction data, extracts block timestamps, calculates transaction delays, and generates histograms to visualize the delays.

このスクリプトは、Osmosis ブロックチェーン上の IBC (Inter-Blockchain Communication) トランザクションを分析します。トランザクションデータを含む CSV ファイルを処理し、ブロックのタイムスタンプを取得し、トランザクションの遅延を計算し、ヒストグラムを生成して視覚化します。

## Features / 機能

- **Filtering by Channel / チャネルごとのフィルタリング**: Users can choose to filter transactions by a specific IBC channel. / 特定の IBC チャネルのトランザクションをフィルタリングできます。
- **Block Timestamp Retrieval / ブロックタイムスタンプの取得**: Fetches timestamps from the Osmosis blockchain for transaction processing. / Osmosis ブロックチェーンからタイムスタンプを取得し、トランザクション処理に活用します。
- **Transaction Delay Calculation / トランザクション遅延の計算**: Computes the time and block delay between `send_packet` and `acknowledge_packet` transactions. / `send_packet` と `acknowledge_packet` トランザクション間の時間遅延とブロック遅延を計算します。
- **Visualization / 可視化**: Generates histograms of `time_delay_sec` and `block_delay` distributions. / `time_delay_sec` と `block_delay` の分布を示すヒストグラムを生成します。
- **CSV Output / CSV 出力**: Saves the processed data with delay calculations for further analysis. / 処理後のデータを CSV に保存し、さらなる分析を可能にします。

## Installation / インストール

Ensure you have Python installed along with the required dependencies:
以下の手順で Python 環境を整えます。

```bash
pip install -r requirements.txt
```

## Usage / 使い方

1. Prepare an IBC transaction CSV file (e.g., `ibc_packet_delay_analysis30116000-30118000.csv`).
   IBC トランザクションの CSV ファイル (例: `ibc_packet_delay_analysis30116000-30118000.csv`) を用意します。
2. Run the script:
   スクリプトを実行します。
   ```bash
   python script.py
   ```
3. Choose whether to apply a filter (`yes/no`). If `yes`, specify the channel number.
   フィルターを適用するか (`yes/no`) を選択し、`yes` の場合はチャネル番号を入力します。
4. The script processes the data and saves results.
   スクリプトがデータを処理し、結果を保存します。

## Output / 出力

- Processed CSV file: `ibc_time_delay_analysis_{channel}.csv`
  処理後の CSV ファイル: `ibc_time_delay_analysis_{channel}.csv`
- Time delay histogram: `time_delay_distribution_{channel}.png`
  時間遅延のヒストグラム: `time_delay_distribution_{channel}.png`
- Block delay histogram: `block_delay_distribution_{channel}.png`
  ブロック遅延のヒストグラム: `block_delay_distribution_{channel}.png`

## Example / 実行例

```
利用可能なチャネルID: 0, 122, 208
フィルターを適用しますか？ (yes/no): yes
対象のチャネル番号を入力してください (例: 0, 122, 208): 0
Filtered IBC transactions count: 150
CSV file saved: ibc_time_delay_analysis_channel-0.csv
Histogram saved as time_delay_distribution_ibc_packet_delay_analysis30116000-30118000channel-0.png
Histogram saved as block_delay_distribution_ibc_packet_delay_analysis30116000-30118000channel-0.png
```

## Notes / 注意事項

- Ensure the RPC endpoint is accessible. / RPC エンドポイントがアクセス可能であることを確認してください。
- Large datasets may take time to process. / 大規模なデータセットの処理には時間がかかる場合があります。
- Modify `base_file` to reflect the correct CSV filename. / `base_file` を適切な CSV ファイル名に変更してください。

## License / ライセンス

This project is licensed under the MIT License.
このプロジェクトは MIT ライセンスのもとで提供されます。

## 付録
# Networks Overview

| Chain       | Status  | Well-Known       | Channels | Receive         | Send          | Total          |
|------------|--------|----------------|----------|----------------|--------------|---------------|
| AKASH      | Opened | [channel-1](#) | 3 / 7    | 2,002 ($1,087,547) | 1,512 ($845,816)  | 3,514 ($1,933,463) |
| NEUTRON    | Opened | [channel-874](#) | 4 / 4    | 1,620 ($614,527)  | 2,234 ($458,551)  | 3,854 ($1,073,078) |
| ATOMONE    | Opened | [channel-85309](#) | 2 / 2    | 2,766 ($0)        | 1,092 ($0)        | 3,858 ($0)        |
| DYMENSION  | Opened | [channel-19774](#) | 1 / 1    | 2,637 ($32)       | 1,491 ($4,569)    | 4,128 ($4,600)    |
| STRIDE     | Opened | [channel-326](#) | 2 / 2    | 2,794 ($912,504)  | 2,547 ($1,193,035) | 5,341 ($2,105,540) |
| MANTRA     | Opened | [channel-85077](#) | 1 / 1    | 3,171 ($1,969,068) | 2,536 ($3,780,330) | 5,707 ($5,749,397) |
| INJECTIVE  | Opened | [channel-122](#) | 3 / 3    | 3,047 ($132,411)  | 2,989 ($8,978)    | 6,036 ($141,389)  |
| AXELAR     | Opened | [channel-208](#) | 1 / 1    | 3,964 ($3,773,241) | 4,062 ($6,400,801) | 8,026 ($10,174,042) |
| STARGAZE   | Opened | [channel-75](#)  | 11 / 13  | 3,144 ($488,881)  | 6,765 ($552,527)  | 9,909 ($1,041,408) |
| NOBLE      | Opened | [channel-750](#) | 1 / 1    | 38,616 ($10,768,023) | 49,382 ($12,253,964) | 88,000 ($23,021,986) |
| CELESTIA   | Opened | [channel-6994](#) | 4 / 4    | 5,608 ($2,916,392) | 7,842 ($3,326,017) | 13,450 ($6,237,037) |
| COSMOS HUB | Opened | [channel-0](#) | 28 / 53  | 11,999 ($6,726,212) | 12,498 ($7,172,539) | 24,497 ($13,898,751) |