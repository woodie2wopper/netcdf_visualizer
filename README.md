# NetCDF 可視化ツール

このプロジェクトは、NOAAの地表面反射率データ（NetCDFファイル）をダウンロードし、植生指数（NDVI）を計算して可視化するためのツールです。

## 機能

1. NCEIのウェブサイトから.ncファイルを自動ダウンロード
2. NetCDFファイルから植生指数（NDVI）を計算
3. 計算した植生指数を地図上に可視化
4. 特定の緯度経度を中心とした領域の抽出と分析
5. NDVI統計情報のCSV出力と詳細分析
6. 複数地点の時系列NDVI値の一括処理

## 必要条件

- Python 3.6以上
- 必要なライブラリ（requirements.txtに記載）

## インストール方法

```bash
# リポジトリをクローン
git clone https://github.com/woodie2wopper/netcdf_visualizer.git
cd netcdf_visualizer

# 必要なライブラリをインストール
pip install -r requirements.txt
```

## 使用方法

### NetCDFファイルのダウンロード

```bash
# 基本的な使い方
python download_nc_files.py

# ヘルプを表示
python download_nc_files.py -h

# オプションを指定する場合
python download_nc_files.py --url https://www.ncei.noaa.gov/data/land-surface-reflectance/access/1990/ --output ./nc_files --limit 5 --workers 4
# または短いオプション名を使用
python download_nc_files.py -u https://www.ncei.noaa.gov/data/land-surface-reflectance/access/1990/ -o ./nc_files -l 5 -p 4
```

#### オプション

- `--url`, `-u`: ダウンロード元のURL（デフォルト: https://www.ncei.noaa.gov/data/land-surface-reflectance/access/1990/）
- `--output`, `-o`: ダウンロードしたファイルを保存するディレクトリ（デフォルト: ./nc_files）
- `--limit`, `-l`: ダウンロードするファイル数の上限（0は無制限、デフォルト: 0）
- `--overwrite`, `-w`: 既存のファイルを上書きする（デフォルト: False）
- `--workers`, `-p`: 並列ダウンロードのワーカー数（デフォルト: 3）

### NetCDFファイルの可視化

```bash
# 基本的な使い方
python netcdf_visualizer.py

# ヘルプを表示
python netcdf_visualizer.py -h

# 別のファイルを指定する場合
python netcdf_visualizer.py --file ./nc_files/AVHRR-Land_v005_AVH09C1_NOAA-11_19900101_c20170614215223.nc
# または短いオプション名を使用
python netcdf_visualizer.py -f ./nc_files/AVHRR-Land_v005_AVH09C1_NOAA-11_19900101_c20170614215223.nc -o custom_output.png -n

# 特定の緯度経度を中心とした領域を抽出する場合（例: 東京）
python netcdf_visualizer.py -f ./nc_files/AVHRR-Land_v005_AVH09C1_NOAA-11_19900101_c20170614215223.nc --lat 35.6895 --lon 139.6917 --region-size 20
# または短いオプション名を使用
python netcdf_visualizer.py -f ./nc_files/AVHRR-Land_v005_AVH09C1_NOAA-11_19900101_c20170614215223.nc -y 35.6895 -x 139.6917 -r 20

# NDVI統計情報をCSVファイルに出力する場合
python netcdf_visualizer.py -f ./nc_files/AVHRR-Land_v005_AVH09C1_NOAA-11_19900101_c20170614215223.nc -y 35.6895 -x 139.6917 -r 20 --ndvi-stats
# または短いオプション名を使用
python netcdf_visualizer.py -f ./nc_files/AVHRR-Land_v005_AVH09C1_NOAA-11_19900101_c20170614215223.nc -y 35.6895 -x 139.6917 -r 20 -s
```

#### オプション

- `--file`, `-f`: 処理するNetCDFファイルのパス
- `--output`, `-o`: 出力画像ファイルのパス（指定しない場合はファイル名から自動生成）
- `--no-display`, `-n`: プロットを表示しない（バッチ処理用）
- `--lat`, `-y`: 抽出する領域の中心緯度（例: 35.6895 for 東京）
- `--lon`, `-x`: 抽出する領域の中心経度（例: 139.6917 for 東京）
- `--region-size`, `-r`: 抽出する領域のサイズ（km）（デフォルト: 20km）
- `--ndvi-stats`, `-s`: NDVI統計情報をCSVファイルに出力する

### 複数地点の一括処理

複数の地点のNDVIを日付ごとに一括で取得するには、`ndvi_batch_processor.py`スクリプトを使用します。このスクリプトは、緯度経度のリスト（CSVファイル）と.ncファイルが格納されているディレクトリを入力として、すべての組み合わせに対してnetcdf_visualizer.pyを実行します。

```bash
# 基本的な使い方
python ndvi_batch_processor.py -p master.csv -d /path/to/nc_files -o ndvi_output -s

# ヘルプを表示
python ndvi_batch_processor.py -h

# テストモードで実行（最初の2つの.ncファイルのみ処理）
python ndvi_batch_processor.py -p master.csv -d /path/to/nc_files -o ndvi_output -s -t

# 並列処理を使用する場合（4つのワーカーを使用）
python ndvi_batch_processor.py -p master.csv -d /path/to/nc_files -o ndvi_output -s -w 4

# テストモードと並列処理を組み合わせる場合
python ndvi_batch_processor.py -p master.csv -d /path/to/nc_files -o ndvi_output -s -t -w 2
```

#### オプション

- `--points`, `-p`: 緯度経度リストのCSVファイル（No,Lat,Lon形式）
- `--nc-dir`, `-d`: .ncファイルが格納されているディレクトリ
- `--output`, `-o`: 結果を保存するディレクトリ（デフォルト: ndvi_results）
- `--region-size`, `-r`: 抽出する領域のサイズ（km）（デフォルト: 20km）
- `--workers`, `-w`: 並列処理のワーカー数（デフォルト: 1）
- `--summary`, `-s`: 処理後に結果をまとめたCSVファイルを作成する
- `--test`, `-t`: テストモード（最初の2つの.ncファイルのみ処理）

#### 入力CSVファイル形式

緯度経度リストのCSVファイルは以下の形式である必要があります：

```csv
No,Lat,Lon,Description
1,35.6895,139.6917,東京
2,34.6937,135.5022,大阪
3,43.0618,141.3545,札幌
...
```

必須列は `No`, `Lat`, `Lon` の3つです。`Description` 列はオプションで、処理には使用されません。

#### 出力結果

このスクリプトを実行すると、以下のような出力が生成されます：

1. 各地点ごとのディレクトリ（例：`ndvi_output/point_1/`、`ndvi_output/point_2/`など）
2. 各地点ディレクトリ内に、日付ごとのNDVI統計情報ファイル（例：`19900101_ndvi_stats.csv`）
3. `-s`オプションを指定した場合、以下のサマリーファイルも生成されます：
   - `ndvi_summary.csv`：地点ごとの時系列NDVI値をまとめたファイル
   - `ndvi_by_date.csv`：日付ごとのNDVI値をまとめたファイル

### 日本の主要都市の緯度経度

以下は日本の主要都市の緯度経度の参考値です：

| 都市 | 緯度 | 経度 |
|------|------|------|
| 東京 | 35.6895 | 139.6917 |
| 大阪 | 34.6937 | 135.5022 |
| 名古屋 | 35.1815 | 136.9066 |
| 札幌 | 43.0618 | 141.3545 |
| 福岡 | 33.5902 | 130.4017 |
| 仙台 | 38.2682 | 140.8694 |
| 広島 | 34.3853 | 132.4553 |
| 那覇 | 26.2124 | 127.6809 |

## データについて

このツールは、NOAAの地表面反射率データを使用しています。データには以下の変数が含まれています：

- `SREFL_CH1`: チャンネル1の表面反射率（可視光）
- `SREFL_CH2`: チャンネル2の表面反射率（近赤外）
- `BT_CH3`, `BT_CH4`, `BT_CH5`: 輝度温度
- `SZEN`, `VZEN`, `RELAZ`: 太陽天頂角、視角天頂角、相対方位角
- `TIMEOFDAY`: 観測時刻
- `QA`: 品質管理フラグ

## 抽出領域の分析

特定の緯度経度を中心とした領域を抽出すると、以下の統計情報が表示されます：

- 平均NDVI: 領域内の平均植生指数
- 最大NDVI: 領域内の最大植生指数
- 最小NDVI: 領域内の最小植生指数
- 中央値NDVI: 領域内のNDVI中央値
- 標準偏差: 植生指数のばらつき
- 有効ピクセル数: 分析に使用されたピクセル数
- 総ピクセル数: 領域内の全ピクセル数
- 有効データ率: 有効なデータの割合（%）

これらの情報を使用して、特定地域の植生状況を時系列で分析することができます。

## NDVI統計情報のCSV出力

`--ndvi-stats`または`-s`オプションを使用すると、NDVI統計情報がCSVファイルに出力されます。出力ファイル名は自動的に生成され、以下の形式になります：

```
[元ファイル名]_region_lat[緯度]_lon[経度]_[サイズ]km_ndvi_stats.csv
```

例：`AVHRR-Land_v005_AVH09C1_NOAA-11_19900101_region_lat35.6895_lon139.6917_20km_ndvi_stats.csv`

CSVファイルには以下の情報が含まれます：

| 統計量 | 値 |
|--------|-----|
| 対象地域 | 緯度35.6895°N, 経度139.6917°E 周辺 20km四方 |
| 中心緯度 | 35.6895 |
| 中心経度 | 139.6917 |
| メッシュサイズ(km) | 20.0 |
| 日付 | 1990年01月01日 |
| 平均NDVI | 0.1234 |
| 最大NDVI | 0.8765 |
| 最小NDVI | -0.3456 |
| 中央値NDVI | 0.2345 |
| 標準偏差 | 0.1234 |
| 有効ピクセル数 | 100 |
| 総ピクセル数 | 120 |
| 有効データ率(%) | 83.33 |

## 出力ファイル名の形式

出力ファイル名は以下の形式で自動生成されます：

1. 画像ファイル：
   ```
   [元ファイル名]_region_lat[緯度]_lon[経度]_[サイズ]km_ndvi.png
   ```

2. 統計情報ファイル：
   ```
   [元ファイル名]_region_lat[緯度]_lon[経度]_[サイズ]km_ndvi_stats.csv
   ```

これにより、どの地域のどのサイズのデータかが一目でわかるようになっています。

## バッチ処理の例

複数の地点や時系列データを一括処理する例：

```bash
#!/bin/bash

# 処理対象のファイル
FILES="./nc_files/AVHRR-Land_v005_AVH09C1_NOAA-11_1990*.nc"

# 処理対象の都市（緯度、経度、名前）
CITIES=(
  "35.6895 139.6917 Tokyo"
  "34.6937 135.5022 Osaka"
  "43.0618 141.3545 Sapporo"
)

# 各ファイルと都市の組み合わせで処理
for file in $FILES; do
  for city in "${CITIES[@]}"; do
    read -r lat lon name <<< "$city"
    echo "処理中: $file - $name (緯度: $lat, 経度: $lon)"
    python netcdf_visualizer.py -f "$file" -y "$lat" -x "$lon" -r 20 -s -n
  done
done

echo "処理完了"
```

より効率的な方法として、`ndvi_batch_processor.py`を使用することもできます：

```bash
# CSVファイルを作成
cat > cities.csv << EOF
No,Lat,Lon,Description
1,35.6895,139.6917,東京
2,34.6937,135.5022,大阪
3,43.0618,141.3545,札幌
EOF

# バッチ処理を実行
python ndvi_batch_processor.py -p cities.csv -d ./nc_files -o ndvi_results -s -w 3
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細はLICENSEファイルを参照してください。

## 注意事項

- ダウンロードするデータは大容量になる可能性があります。ディスク容量に注意してください。
- データの使用にあたっては、NOAAのデータ使用ポリシーに従ってください。 