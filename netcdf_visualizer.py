#!/usr/bin/env python3

from netCDF4 import Dataset
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as colors
import argparse
import os
from matplotlib.patches import Rectangle

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

def visualize_ndvi(nc_file_path, output_file=None, show_plot=True, center_lat=None, center_lon=None, region_size_km=20):
    """
    NetCDFファイルから植生指数（NDVI）を計算して可視化する関数
    
    Args:
        nc_file_path (str): NetCDFファイルのパス
        output_file (str, optional): 出力画像ファイルのパス
        show_plot (bool): プロットを表示するかどうか
        center_lat (float, optional): 抽出する領域の中心緯度
        center_lon (float, optional): 抽出する領域の中心経度
        region_size_km (float): 抽出する領域のサイズ（km）
    """
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
                print(f"- 標準偏差: {np.std(valid_ndvi):.4f}")
                print(f"- 有効ピクセル数: {len(valid_ndvi)}")
    else:
        # 全体マップのプロット
        plt.subplot(1, 1, 1)
        im = plt.pcolormesh(lons, lats, ndvi, cmap=cmap, norm=norm)
        plt.colorbar(im, label='NDVI')
    
    # ファイル名から日付を抽出（ファイル名のフォーマットに依存）
    filename = os.path.basename(nc_file_path)
    date_str = "不明"
    if "_" in filename:
        parts = filename.split("_")
        for part in parts:
            if len(part) == 8 and part.isdigit():
                year = part[:4]
                month = part[4:6]
                day = part[6:8]
                date_str = f"{year}年{month}月{day}日"
                break
    
    if center_lat is None or center_lon is None:
        plt.title(f'正規化植生指数 (NDVI) - {date_str}')
        plt.xlabel('経度')
        plt.ylabel('緯度')
        plt.grid(True, linestyle='--', alpha=0.5)

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
    
    args = parser.parse_args()
    
    # 出力ファイル名が指定されていない場合は自動生成
    output_file = args.output
    if not output_file:
        base_name = os.path.splitext(os.path.basename(args.file))[0]
        region_str = f"_region_{args.lat}_{args.lon}_{args.region_size}km" if args.lat and args.lon else ""
        output_file = f"{base_name}{region_str}_ndvi.png"
    
    # 可視化の実行
    visualize_ndvi(args.file, output_file, not args.no_display, args.lat, args.lon, args.region_size)

if __name__ == "__main__":
    main()