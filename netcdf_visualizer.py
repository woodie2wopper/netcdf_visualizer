#!/usr/bin/env python3

from netCDF4 import Dataset
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as colors
import argparse
import os
from matplotlib.patches import Rectangle
import csv
import datetime
import sys
import matplotlib as mpl

# 日本語フォント設定
def setup_japanese_font():
    """
    matplotlibで日本語フォントを使用するための設定を行う関数
    """
    # macOSの場合
    if sys.platform.startswith('darwin'):
        font_dirs = ['/System/Library/Fonts', '/Library/Fonts', os.path.expanduser('~/Library/Fonts')]
        font_files = []
        
        # 一般的な日本語フォント名のリスト
        jp_font_names = [
            'Hiragino Sans GB.ttc',
            'Hiragino Sans.ttc',
            'HiraginoSans-W3.ttc',
            'HiraginoSans-W6.ttc',
            'ヒラギノ角ゴシック W3.ttc',
            'ヒラギノ角ゴシック W6.ttc',
            'Hiragino Kaku Gothic Pro.ttc',
            'Hiragino Kaku Gothic ProN.ttc',
            'ヒラギノ角ゴ Pro.ttc',
            'ヒラギノ角ゴ ProN.ttc',
            'AppleGothic.ttf',
            'YuGothic.ttc',
            'YuGo-Medium.otf',
            'YuGo-Bold.otf'
        ]
        
        # フォントファイルを探す
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                for font_name in jp_font_names:
                    font_path = os.path.join(font_dir, font_name)
                    if os.path.exists(font_path):
                        font_files.append(font_path)
                        break
                if font_files:
                    break
        
        # 見つかったフォントがあれば設定
        if font_files:
            print(f"日本語フォントを設定します: {os.path.basename(font_files[0])}")
            mpl.rc('font', family='sans-serif')
            # 'sans-serif'をキーワード引数として渡す代わりに辞書を使用
            font_dict = {'font.sans-serif': [os.path.splitext(os.path.basename(font_files[0]))[0]]}
            plt.rcParams.update(font_dict)
        else:
            print("警告: 日本語フォントが見つかりませんでした。テキストが正しく表示されない可能性があります。")
    
    # Linuxの場合
    elif sys.platform.startswith('linux'):
        try:
            # IPAフォントがインストールされているか確認
            plt.rcParams['font.family'] = 'IPAPGothic'
            print("日本語フォントを設定しました: IPAPGothic")
        except Exception:
            try:
                # Notoフォントを試す
                plt.rcParams['font.family'] = 'Noto Sans CJK JP'
                print("日本語フォントを設定しました: Noto Sans CJK JP")
            except Exception:
                print("警告: 日本語フォントが見つかりませんでした。テキストが正しく表示されない可能性があります。")
    
    # Windowsの場合
    elif sys.platform.startswith('win'):
        try:
            plt.rcParams['font.family'] = 'MS Gothic'
            print("日本語フォントを設定しました: MS Gothic")
        except Exception:
            print("警告: 日本語フォントが見つかりませんでした。テキストが正しく表示されない可能性があります。")
    
    # フォントキャッシュをクリア
    try:
        import matplotlib.font_manager as fm
        fm._rebuild()
    except Exception:
        # 新しいバージョンのmatplotlibでは_rebuild()が非推奨または引数が必要な場合がある
        try:
            fm.fontManager.findfont('DejaVu Sans')  # キャッシュを再構築するためのダミー呼び出し
            print("フォントキャッシュを更新しました")
        except Exception:
            print("警告: フォントキャッシュの更新に失敗しました")

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    2点間の距離をhaversine公式で計算する関数（単位: km）
    
    Args:
        lat1, lon1: 地点1の緯度・経度（度）
        lat2, lon2: 地点2の緯度・経度（度）
    
    Returns:
        float: 2点間の距離（km）
    """
    # 地球の半径（km）
    R = 6371.0
    
    # 度からラジアンに変換
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    
    # 緯度と経度の差分
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # haversine公式
    a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    distance = R * c
    
    return distance

def get_region_indices(lats, lons, center_lat, center_lon, region_size_km):
    """
    指定された中心点から特定の距離（km）内の領域のインデックスを取得する関数
    
    Args:
        lats: 緯度の配列
        lons: 経度の配列
        center_lat: 中心点の緯度
        center_lon: 中心点の経度
        region_size_km: 領域のサイズ（km）
    
    Returns:
        tuple: (lat_indices, lon_indices) - 条件を満たすインデックスの配列
    """
    # 半径（km）
    radius = region_size_km / 2
    
    # 緯度1度あたりの距離は約111km
    # 経度1度あたりの距離は緯度によって異なる（赤道で約111km、極で0km）
    lat_range = radius / 111.0
    lon_range = radius / (111.0 * np.cos(np.radians(center_lat)))
    
    # 緯度・経度の範囲
    lat_min, lat_max = center_lat - lat_range, center_lat + lat_range
    lon_min, lon_max = center_lon - lon_range, center_lon + lon_range
    
    # インデックスの取得
    lat_indices = np.where((lats >= lat_min) & (lats <= lat_max))[0]
    lon_indices = np.where((lons >= lon_min) & (lons <= lon_max))[0]
    
    return lat_indices, lon_indices

def save_ndvi_stats(stats, output_file):
    """
    NDVI統計情報をCSVファイルに保存する関数
    
    Args:
        stats: 統計情報の辞書
        output_file: 出力ファイルパス
    """
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['統計量', '値']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for key, value in stats.items():
            writer.writerow({'統計量': key, '値': value})
    
    print(f"NDVI統計情報をCSVファイルに保存しました: {output_file}")

def visualize_ndvi(nc_file_path, output_file=None, show_plot=True, center_lat=None, center_lon=None, region_size_km=20, ndvi_stats=False):
    """
    NetCDFファイルから植生指数（NDVI）を計算して可視化する関数
    
    Args:
        nc_file_path (str): NetCDFファイルのパス
        output_file (str, optional): 出力画像ファイルのパス
        show_plot (bool): プロットを表示するかどうか
        center_lat (float, optional): 抽出する領域の中心緯度
        center_lon (float, optional): 抽出する領域の中心経度
        region_size_km (float): 抽出する領域のサイズ（km）
        ndvi_stats (bool): NDVI統計情報を出力するかどうか
    
    Returns:
        dict: NDVI統計情報（ndvi_stats=Trueの場合）
    """
    # 日本語フォントの設定
    setup_japanese_font()
    
    # NetCDFファイルの読み込み
    print(f"ファイルを読み込み中: {nc_file_path}")
    nc_data = Dataset(nc_file_path, 'r')

    # 変数の取得
    lons = nc_data.variables['longitude'][:]
    lats = nc_data.variables['latitude'][:]

    # 表面反射率データの取得（チャンネル1と2）
    srefl_ch1 = nc_data.variables['SREFL_CH1'][0, :, :]  # 可視光
    srefl_ch2 = nc_data.variables['SREFL_CH2'][0, :, :]  # 近赤外

    # スケールファクターの確認（必要に応じて）
    print("SREFL_CH1の属性:")
    for attr in nc_data.variables['SREFL_CH1'].ncattrs():
        print(f"- {attr}: {nc_data.variables['SREFL_CH1'].getncattr(attr)}")

    print("\nSREFL_CH2の属性:")
    for attr in nc_data.variables['SREFL_CH2'].ncattrs():
        print(f"- {attr}: {nc_data.variables['SREFL_CH2'].getncattr(attr)}")

    # 無効値のマスク処理
    # 一般的に-9999や-32768などの値が無効値として使われることが多い
    # 属性から正確な無効値を取得
    if hasattr(nc_data.variables['SREFL_CH1'], '_FillValue'):
        fill_value = nc_data.variables['SREFL_CH1']._FillValue
        srefl_ch1 = np.ma.masked_equal(srefl_ch1, fill_value)
        srefl_ch2 = np.ma.masked_equal(srefl_ch2, fill_value)

    # スケールファクターとオフセットの適用（必要に応じて）
    if hasattr(nc_data.variables['SREFL_CH1'], 'scale_factor'):
        scale_factor_ch1 = nc_data.variables['SREFL_CH1'].scale_factor
        offset_ch1 = nc_data.variables['SREFL_CH1'].add_offset if hasattr(nc_data.variables['SREFL_CH1'], 'add_offset') else 0
        
        scale_factor_ch2 = nc_data.variables['SREFL_CH2'].scale_factor
        offset_ch2 = nc_data.variables['SREFL_CH2'].add_offset if hasattr(nc_data.variables['SREFL_CH2'], 'add_offset') else 0
        
        srefl_ch1 = srefl_ch1 * scale_factor_ch1 + offset_ch1
        srefl_ch2 = srefl_ch2 * scale_factor_ch2 + offset_ch2

    # NDVI（正規化植生指数）の計算
    # NDVI = (NIR - RED) / (NIR + RED)
    # ゼロ除算を避けるためのマスク処理
    denominator = srefl_ch2 + srefl_ch1
    ndvi = np.zeros_like(denominator)
    valid_idx = denominator != 0
    ndvi[valid_idx] = (srefl_ch2[valid_idx] - srefl_ch1[valid_idx]) / denominator[valid_idx]

    # NDVIの範囲は通常-1から1だが、データによっては調整が必要
    ndvi = np.clip(ndvi, -1, 1)

    # カラーマップの設定（植生表示に適したもの）
    cmap = plt.cm.RdYlGn  # 赤-黄-緑のカラーマップ（植生によく使われる）
    norm = colors.Normalize(vmin=-1, vmax=1)

    # 図の作成
    plt.figure(figsize=(12, 8))

    # ファイル名から日付を抽出（ファイル名のフォーマットに依存）
    filename = os.path.basename(nc_file_path)
    date_str = "不明"
    date_obj = None
    if "_" in filename:
        parts = filename.split("_")
        for part in parts:
            if len(part) == 8 and part.isdigit():
                year = part[:4]
                month = part[4:6]
                day = part[6:8]
                date_str = f"{year}年{month}月{day}日"
                try:
                    date_obj = datetime.datetime(int(year), int(month), int(day))
                except ValueError:
                    pass
                break

    # 統計情報を格納する辞書
    stats = {}
    
    # 特定の領域を抽出する場合
    if center_lat is not None and center_lon is not None:
        # 指定された中心点から特定の距離内の領域を抽出
        lat_indices, lon_indices = get_region_indices(lats, lons, center_lat, center_lon, region_size_km)
        
        if len(lat_indices) == 0 or len(lon_indices) == 0:
            print(f"警告: 指定された中心点（緯度: {center_lat}, 経度: {center_lon}）から{region_size_km}km四方の領域が見つかりませんでした。")
            print("全体マップを表示します。")
            # 全体マップのプロット
            plt.subplot(1, 1, 1)
            im = plt.pcolormesh(lons, lats, ndvi, cmap=cmap, norm=norm)
            plt.colorbar(im, label='NDVI')
            
            # 指定された中心点をマーク
            plt.plot(center_lon, center_lat, 'ro', markersize=8, label='指定された中心点')
            
            # 領域の範囲を示す矩形を描画
            lat_range = region_size_km / 111.0 / 2
            lon_range = region_size_km / (111.0 * np.cos(np.radians(center_lat))) / 2
            rect = Rectangle((center_lon - lon_range, center_lat - lat_range), 
                            lon_range * 2, lat_range * 2, 
                            linewidth=2, edgecolor='r', facecolor='none')
            plt.gca().add_patch(rect)
            
            plt.legend()
            
            # 統計情報を全体から計算
            valid_ndvi = ndvi[~np.ma.getmaskarray(ndvi)]
            if len(valid_ndvi) > 0:
                stats = {
                    "対象地域": f"全体（指定領域が見つからないため）",
                    "中心緯度": center_lat,
                    "中心経度": center_lon,
                    "メッシュサイズ(km)": region_size_km,
                    "日付": date_str,
                    "平均NDVI": float(np.mean(valid_ndvi)),
                    "最大NDVI": float(np.max(valid_ndvi)),
                    "最小NDVI": float(np.min(valid_ndvi)),
                    "中央値NDVI": float(np.median(valid_ndvi)),
                    "標準偏差": float(np.std(valid_ndvi)),
                    "有効ピクセル数": int(len(valid_ndvi)),
                    "総ピクセル数": int(ndvi.size),
                    "有効データ率(%)": float(len(valid_ndvi) / ndvi.size * 100)
                }
        else:
            # 抽出された領域のプロット
            plt.subplot(1, 2, 1)
            im1 = plt.pcolormesh(lons, lats, ndvi, cmap=cmap, norm=norm)
            plt.colorbar(im1, label='NDVI')
            
            # 指定された中心点をマーク
            plt.plot(center_lon, center_lat, 'ro', markersize=8)
            
            # 領域の範囲を示す矩形を描画
            lat_range = region_size_km / 111.0 / 2
            lon_range = region_size_km / (111.0 * np.cos(np.radians(center_lat))) / 2
            rect = Rectangle((center_lon - lon_range, center_lat - lat_range), 
                            lon_range * 2, lat_range * 2, 
                            linewidth=2, edgecolor='r', facecolor='none')
            plt.gca().add_patch(rect)
            
            plt.title('全体マップ')
            plt.xlabel('経度')
            plt.ylabel('緯度')
            plt.grid(True, linestyle='--', alpha=0.5)
            
            # 抽出された領域の拡大表示
            plt.subplot(1, 2, 2)
            region_lons = lons[lon_indices]
            region_lats = lats[lat_indices]
            region_ndvi = ndvi[np.ix_(lat_indices, lon_indices)]
            
            im2 = plt.pcolormesh(region_lons, region_lats, region_ndvi, cmap=cmap, norm=norm)
            plt.colorbar(im2, label='NDVI')
            plt.title(f'抽出領域（中心: {center_lat:.4f}°N, {center_lon:.4f}°E, 範囲: {region_size_km}km四方）')
            plt.xlabel('経度')
            plt.ylabel('緯度')
            plt.grid(True, linestyle='--', alpha=0.5)
            
            # 抽出領域の統計情報
            valid_ndvi = region_ndvi[~np.ma.getmaskarray(region_ndvi)]
            if len(valid_ndvi) > 0:
                print(f"\n抽出領域の統計情報:")
                print(f"- 平均NDVI: {np.mean(valid_ndvi):.4f}")
                print(f"- 最大NDVI: {np.max(valid_ndvi):.4f}")
                print(f"- 最小NDVI: {np.min(valid_ndvi):.4f}")
                print(f"- 中央値NDVI: {np.median(valid_ndvi):.4f}")
                print(f"- 標準偏差: {np.std(valid_ndvi):.4f}")
                print(f"- 有効ピクセル数: {len(valid_ndvi)}")
                print(f"- 総ピクセル数: {region_ndvi.size}")
                print(f"- 有効データ率: {len(valid_ndvi) / region_ndvi.size * 100:.2f}%")
                
                # 統計情報を辞書に格納
                stats = {
                    "対象地域": f"緯度{center_lat:.4f}°N, 経度{center_lon:.4f}°E 周辺 {region_size_km}km四方",
                    "中心緯度": center_lat,
                    "中心経度": center_lon,
                    "メッシュサイズ(km)": region_size_km,
                    "日付": date_str,
                    "平均NDVI": float(np.mean(valid_ndvi)),
                    "最大NDVI": float(np.max(valid_ndvi)),
                    "最小NDVI": float(np.min(valid_ndvi)),
                    "中央値NDVI": float(np.median(valid_ndvi)),
                    "標準偏差": float(np.std(valid_ndvi)),
                    "有効ピクセル数": int(len(valid_ndvi)),
                    "総ピクセル数": int(region_ndvi.size),
                    "有効データ率(%)": float(len(valid_ndvi) / region_ndvi.size * 100)
                }
    else:
        # 全体マップのプロット
        plt.subplot(1, 1, 1)
        im = plt.pcolormesh(lons, lats, ndvi, cmap=cmap, norm=norm)
        plt.colorbar(im, label='NDVI')
        plt.title(f'正規化植生指数 (NDVI) - {date_str}')
        plt.xlabel('経度')
        plt.ylabel('緯度')
        plt.grid(True, linestyle='--', alpha=0.5)
        
        # 全体の統計情報
        valid_ndvi = ndvi[~np.ma.getmaskarray(ndvi)]
        if len(valid_ndvi) > 0:
            stats = {
                "対象地域": "全体",
                "日付": date_str,
                "平均NDVI": float(np.mean(valid_ndvi)),
                "最大NDVI": float(np.max(valid_ndvi)),
                "最小NDVI": float(np.min(valid_ndvi)),
                "中央値NDVI": float(np.median(valid_ndvi)),
                "標準偏差": float(np.std(valid_ndvi)),
                "有効ピクセル数": int(len(valid_ndvi)),
                "総ピクセル数": int(ndvi.size),
                "有効データ率(%)": float(len(valid_ndvi) / ndvi.size * 100)
            }

    # 図の保存と表示
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300)
        print(f"画像を保存しました: {output_file}")
    
    if show_plot:
        plt.show()
    
    # ファイルを閉じる
    nc_data.close()
    
    print("処理が完了しました。")
    
    # NDVI統計情報を返す
    return stats

def main():
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='NetCDFファイルから植生指数（NDVI）を計算して可視化するスクリプト')
    parser.add_argument('--file', '-f', type=str, 
                        default='example/AVHRR-Land_v005_AVH09C1_NOAA-11_19900101_c20170614215223.nc',
                        help='処理するNetCDFファイルのパス')
    parser.add_argument('--output', '-o', type=str, 
                        help='出力画像ファイルのパス（指定しない場合はファイル名から自動生成）')
    parser.add_argument('--no-display', '-n', action='store_true',
                        help='プロットを表示しない（バッチ処理用）')
    parser.add_argument('--lat', '-y', type=float,
                        help='抽出する領域の中心緯度（例: 35.6895 for 東京）')
    parser.add_argument('--lon', '-x', type=float,
                        help='抽出する領域の中心経度（例: 139.6917 for 東京）')
    parser.add_argument('--region-size', '-r', type=float, default=20.0,
                        help='抽出する領域のサイズ（km）（デフォルト: 20km）')
    parser.add_argument('--ndvi-stats', '-s', action='store_true',
                        help='NDVI統計情報をCSVファイルに出力する')
    
    # 引数がない場合は簡易ヘルプを表示
    if len(sys.argv) == 1:
        print("NetCDF 可視化ツール - 簡易ヘルプ")
        print("\n基本的な使い方:")
        print("  python netcdf_visualizer.py -f <NetCDFファイル> [オプション]")
        print("\n主なオプション:")
        print("  -f, --file <ファイル>      処理するNetCDFファイルのパス")
        print("  -o, --output <ファイル>    出力画像ファイルのパス")
        print("  -n, --no-display          プロットを表示しない")
        print("  -y, --lat <緯度>          抽出する領域の中心緯度（例: 35.6895 for 東京）")
        print("  -x, --lon <経度>          抽出する領域の中心経度（例: 139.6917 for 東京）")
        print("  -r, --region-size <サイズ> 抽出する領域のサイズ（km）（デフォルト: 20km）")
        print("  -s, --ndvi-stats          NDVI統計情報をCSVファイルに出力する")
        print("\n詳細なヘルプを表示するには:")
        print("  python netcdf_visualizer.py -h")
        print("\n日本の主要都市の緯度経度:")
        print("  東京: 35.6895, 139.6917")
        print("  大阪: 34.6937, 135.5022")
        print("  札幌: 43.0618, 141.3545")
        print("  福岡: 33.5902, 130.4017")
        return
    
    args = parser.parse_args()
    
    # ファイルの存在確認
    if not os.path.exists(args.file):
        print(f"エラー: 指定されたファイル '{args.file}' が見つかりません。")
        print("正しいファイルパスを指定するか、ファイルをダウンロードしてください。")
        print("\nファイルのダウンロード方法:")
        print("  python download_nc_files.py --help")
        return
    
    # 入力ファイルのディレクトリとファイル名を取得
    input_dir = os.path.dirname(os.path.abspath(args.file))
    base_name = os.path.splitext(os.path.basename(args.file))[0]
    
    # 出力ファイル名が指定されていない場合は自動生成
    output_file = args.output
    if not output_file:
        # 出力ディレクトリの作成（必要に応じて）
        output_dir = os.path.join(input_dir, "ndvi_results")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"出力ディレクトリを作成しました: {output_dir}")
        
        region_str = ""
        if args.lat and args.lon:
            region_str = f"_region_lat{args.lat:.4f}_lon{args.lon:.4f}_{args.region_size}km"
        output_file = os.path.join(output_dir, f"{base_name}{region_str}_ndvi.png")
    else:
        # 出力ファイルが指定されている場合、そのディレクトリを確認して作成
        output_dir = os.path.dirname(os.path.abspath(output_file))
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"出力ディレクトリを作成しました: {output_dir}")
    
    print(f"出力ファイル: {output_file}")
    
    # 可視化の実行
    stats = visualize_ndvi(args.file, output_file, not args.no_display, args.lat, args.lon, args.region_size, args.ndvi_stats)
    
    # NDVI統計情報をCSVファイルに出力
    if args.ndvi_stats and stats:
        # 出力ファイル名の生成
        stats_file = os.path.splitext(output_file)[0] + "_stats.csv"
        save_ndvi_stats(stats, stats_file)

if __name__ == "__main__":
    main()