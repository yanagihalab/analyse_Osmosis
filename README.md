# IBC Transaction Analysis Tool / IBC トランザクション分析ツール

## Overview / 概要

This script analyzes IBC (Inter-Blockchain Communication) transactions on the Osmosis blockchain. It processes a CSV file containing transaction data, extracts block timestamps, calculates transaction delays, and generates histograms to visualize the delays.

このスクリプトは、Osmosis ブロックチェーン上の IBC (Inter-Blockchain Communication) トランザクションを
分析します。RPCノードからトランザクションデータを取得し、IBC transferを CSV ファイルにまとめます
まとめて CSV ファイルからブロックのタイムスタンプを取得し、トランザクションの遅延を計算し、
ヒストグラムを生成して視覚化します。

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
[mintscan](https://www.mintscan.io/osmosis/relayers/)より2025年2月22日現在の7日間データ<br>
OSMOSISとの主なIBCの接続先(Well-Knownでソート)

| Chain       | Well-Known      | Total IBC (times) | Receive : Send |
|------------|----------------|--------------|---------------|
| COSMOS HUB | [channel-0]    | 24,497       | 49:51        |
| AKASH      | [channel-1]    | 3,514        | 57:43        |
| STARGAZE   | [channel-75]   | 9,909        | 32:68        |
| INJECTIVE  | [channel-122]  | 6,036        | 50:50        |
| STRIDE     | [channel-326]  | 5,341        | 52:48        |
| DYMENSION  | [channel-19774] | 4,128       | 64:36        |
| AXELAR     | [channel-208]  | 8,026        | 49:51        |
| CELESTIA   | [channel-6994] | 13,450       | 42:58        |
| NOBLE      | [channel-750]  | 88,000       | 44:56        |
| NEUTRON    | [channel-874]  | 3,854        | 42:58        |
| MANTRA     | [channel-85077] | 5,707       | 56:44        |
| ATOMONE    | [channel-85309] | 3,858       | 72:28        |


