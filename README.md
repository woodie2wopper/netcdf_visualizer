# NetCDF 可視化ツール

このプロジェクトは、NOAAの地表面反射率データ（NetCDFファイル）をダウンロードし、植生指数（NDVI）を計算して可視化するためのツールです。

## 機能

1. NCEIのウェブサイトから.ncファイルを自動ダウンロード
2. NetCDFファイルから植生指数（NDVI）を計算
3. 計算した植生指数を地図上に可視化
4. 特定の緯度経度を中心とした領域の抽出と分析

## 必要条件

- Python 3.6以上
- 必要なライブラリ（requirements.txtに記載）

## インストール方法

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/netcdf_visualizer.git
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
```

#### オプション

- `--file`, `-f`: 処理するNetCDFファイルのパス
- `--output`, `-o`: 出力画像ファイルのパス（指定しない場合はファイル名から自動生成）
- `--no-display`, `-n`: プロットを表示しない（バッチ処理用）

## データについて

このツールは、NOAAの地表面反射率データを使用しています。データには以下の変数が含まれています：

- `SREFL_CH1`: チャンネル1の表面反射率（可視光）
- `SREFL_CH2`: チャンネル2の表面反射率（近赤外）
- `BT_CH3`, `BT_CH4`, `BT_CH5`: 輝度温度
- `SZEN`, `VZEN`, `RELAZ`: 太陽天頂角、視角天頂角、相対方位角
- `TIMEOFDAY`: 観測時刻
- `QA`: 品質管理フラグ

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細はLICENSEファイルを参照してください。

## 注意事項

- ダウンロードするデータは大容量になる可能性があります。ディスク容量に注意してください。
- データの使用にあたっては、NOAAのデータ使用ポリシーに従ってください。 