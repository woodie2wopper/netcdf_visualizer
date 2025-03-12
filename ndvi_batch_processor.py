#!/usr/bin/env python3

import os
import csv
import subprocess
import argparse
import glob
import pandas as pd
from datetime import datetime
import concurrent.futures
import sys

def parse_arguments():
    """コマンドライン引数を解析する関数"""
    parser = argparse.ArgumentParser(description='複数の地点のNDVIを日付ごとに取得するラッパースクリプト')
    parser.add_argument('--points', '-p', type=str, required=True,
                        help='緯度経度リストのCSVファイル（No,Lat,Lon形式）')
    parser.add_argument('--nc-dir', '-d', type=str, required=True,
                        help='.ncファイルが格納されているディレクトリ')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='結果を保存するディレクトリ（指定しない場合は入力ディレクトリ内のndvi_resultsフォルダ）')
    parser.add_argument('--region-size', '-r', type=float, default=20.0,
                        help='抽出する領域のサイズ（km）（デフォルト: 20km）')
    parser.add_argument('--workers', '-w', type=int, default=1,
                        help='並列処理のワーカー数（デフォルト: 1）')
    parser.add_argument('--summary', '-s', action='store_true',
                        help='処理後に結果をまとめたCSVファイルを作成する')
    parser.add_argument('--test', '-t', action='store_true',
                        help='テストモード（最初の1つの.ncファイルのみ処理）')
    
    return parser.parse_args()

def read_points(csv_file):
    """CSVファイルから地点情報を読み込む関数"""
    points = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                point = {
                    'No': row['No'],
                    'Lat': float(row['Lat']),
                    'Lon': float(row['Lon'])
                }
                points.append(point)
            except (KeyError, ValueError) as e:
                print(f"警告: 行の解析に失敗しました: {row}, エラー: {e}")
                continue
    
    return points

def find_nc_files(nc_dir):
    """ディレクトリ内の.ncファイルを検索する関数"""
    nc_files = []
    for ext in ['*.nc', '*.NC']:
        # 絶対パスを使用してファイルを検索
        pattern = os.path.join(os.path.abspath(nc_dir), ext)
        found_files = glob.glob(pattern)
        if not found_files:
            print(f"警告: パターン '{pattern}' に一致するファイルが見つかりませんでした")
        nc_files.extend(found_files)
    
    if not nc_files:
        print(f"警告: ディレクトリ '{nc_dir}' に.ncファイルが見つかりませんでした")
        return []
    
    print(f"見つかった.ncファイル: {len(nc_files)}個")
    
    # 日付情報を抽出してソート
    nc_files_with_date = []
    for nc_file in nc_files:
        filename = os.path.basename(nc_file)
        date_str = None
        if "_" in filename:
            parts = filename.split("_")
            for part in parts:
                # 空白を削除して処理
                part = part.strip()
                if len(part) == 8 and part.isdigit():
                    try:
                        date = datetime.strptime(part, '%Y%m%d')
                        date_str = part
                        break
                    except ValueError:
                        continue
        
        if date_str:
            nc_files_with_date.append((nc_file, date_str))
        else:
            print(f"警告: ファイル '{filename}' から日付情報を抽出できませんでした")
    
    if not nc_files_with_date:
        print("警告: 日付情報を持つ.ncファイルが見つかりませんでした")
        return nc_files  # 日付情報がなくても、見つかったファイルを返す
    
    # 日付でソート
    nc_files_with_date.sort(key=lambda x: x[1])
    return [file for file, _ in nc_files_with_date]

def process_point_file(point, nc_file, region_size, output_dir):
    """1つの地点と1つのファイルの組み合わせを処理する関数"""
    point_no = point['No']
    lat = point['Lat']
    lon = point['Lon']
    
    # ファイル名から日付を抽出
    filename = os.path.basename(nc_file)
    date_str = "unknown"
    if "_" in filename:
        parts = filename.split("_")
        for part in parts:
            # 空白を削除して処理
            part = part.strip()
            if len(part) == 8 and part.isdigit():
                date_str = part
                break
    
    print(f"処理中: 地点 {point_no} (緯度: {lat}, 経度: {lon}), ファイル: {os.path.basename(nc_file)}")
    
    # 地点ごとのディレクトリを作成
    point_dir = os.path.join(output_dir, f"point_{point_no}")
    os.makedirs(point_dir, exist_ok=True)
    
    # 出力ファイル名を生成
    base_name = os.path.splitext(os.path.basename(nc_file))[0]
    region_str = f"_region_lat{lat:.4f}_lon{lon:.4f}_{region_size}km"
    output_image = os.path.join(point_dir, f"{date_str}{region_str}_ndvi.png")
    output_stats = os.path.join(point_dir, f"{date_str}_ndvi_stats.csv")
    
    # netcdf_visualizer.pyの絶対パスを取得
    script_dir = os.path.dirname(os.path.abspath(__file__))
    visualizer_path = os.path.join(script_dir, 'netcdf_visualizer.py')
    
    print(f"  出力画像: {output_image}")
    print(f"  統計ファイル: {output_stats}")
    
    # netcdf_visualizer.pyを実行するコマンド
    cmd = [
        sys.executable,  # 現在のPythonインタプリタ
        visualizer_path,  # netcdf_visualizer.pyの絶対パス
        '-f', nc_file,
        '-y', str(lat),
        '-x', str(lon),
        '-r', str(region_size),
        '-o', output_image,  # 出力画像ファイルを明示的に指定
        '-s',  # NDVI統計情報をCSVファイルに出力
        '-n'   # プロットを表示しない
    ]
    
    try:
        # サブプロセスとして実行
        print(f"  実行コマンド: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"  コマンド実行結果: {result.returncode}")
        
        # 標準出力と標準エラー出力を表示
        if result.stdout:
            print(f"  標準出力:\n{result.stdout}")
        if result.stderr:
            print(f"  標準エラー出力:\n{result.stderr}")
        
        # 統計情報ファイルのパス（netcdf_visualizer.pyによって生成される）
        stats_file = os.path.splitext(output_image)[0] + "_stats.csv"
        
        # 統計情報ファイルが存在する場合、必要に応じて名前を変更
        if os.path.exists(stats_file) and stats_file != output_stats:
            # 統計情報ファイルを読み込む
            stats_data = {}
            with open(stats_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stats_data[row['統計量']] = row['値']
            
            # 地点情報を追加
            stats_data['地点No'] = point_no
            
            # 新しいファイルに保存
            with open(output_stats, 'w', encoding='utf-8', newline='') as f:
                fieldnames = ['統計量', '値']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for key, value in stats_data.items():
                    writer.writerow({'統計量': key, '値': value})
            
            # 元の統計情報ファイルを削除（オプション）
            if stats_file != output_stats:
                try:
                    os.remove(stats_file)
                except:
                    pass
            
            print(f"  結果を保存しました: {output_stats}")
            return {
                'point_no': point_no,
                'lat': lat,
                'lon': lon,
                'date': date_str,
                'stats_file': output_stats,
                'success': True
            }
        else:
            print(f"  警告: 統計情報ファイルが見つかりませんでした: {stats_file}")
            return {
                'point_no': point_no,
                'lat': lat,
                'lon': lon,
                'date': date_str,
                'success': False,
                'error': '統計情報ファイルが見つかりませんでした'
            }
    
    except subprocess.CalledProcessError as e:
        print(f"  エラー: 地点 {point_no}, ファイル {os.path.basename(nc_file)} の処理に失敗しました")
        print(f"  コマンド: {' '.join(cmd)}")
        print(f"  エラー出力: {e.stderr}")
        return {
            'point_no': point_no,
            'lat': lat,
            'lon': lon,
            'date': date_str,
            'success': False,
            'error': e.stderr
        }

def create_summary(results, output_dir):
    """処理結果をまとめたCSVファイルを作成する関数"""
    # 成功した結果のみ抽出
    successful_results = [r for r in results if r['success']]
    
    if not successful_results:
        print("警告: 成功した処理結果がありません。サマリーファイルは作成されません。")
        return
    
    # 各地点ごとの時系列データを作成
    points_data = {}
    for result in successful_results:
        point_no = result['point_no']
        date = result['date']
        stats_file = result.get('stats_file')
        
        if not stats_file or not os.path.exists(stats_file):
            continue
        
        # 統計情報ファイルを読み込む
        stats_data = {}
        with open(stats_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stats_data[row['統計量']] = row['値']
        
        # 地点データを初期化
        if point_no not in points_data:
            points_data[point_no] = {
                'No': point_no,
                'Lat': result['lat'],
                'Lon': result['lon']
            }
        
        # 日付ごとのNDVI値を追加
        try:
            ndvi_value = float(stats_data.get('平均NDVI', 'NaN'))
            points_data[point_no][date] = ndvi_value
        except (ValueError, TypeError):
            points_data[point_no][date] = 'NaN'
    
    # DataFrameに変換
    df = pd.DataFrame.from_dict(points_data, orient='index')
    
    # 列の順序を整理（No, Lat, Lon, 日付1, 日付2, ...）
    date_columns = sorted([col for col in df.columns if col not in ['No', 'Lat', 'Lon']])
    columns_order = ['No', 'Lat', 'Lon'] + date_columns
    df = df[columns_order]
    
    # CSVファイルに保存
    summary_file = os.path.join(output_dir, 'ndvi_summary.csv')
    df.to_csv(summary_file, index=False, encoding='utf-8')
    print(f"サマリーファイルを作成しました: {summary_file}")
    
    # 日付ごとのサマリーも作成
    df_by_date = df.melt(id_vars=['No', 'Lat', 'Lon'], 
                         var_name='Date', 
                         value_name='NDVI')
    df_by_date = df_by_date.sort_values(['Date', 'No'])
    
    date_summary_file = os.path.join(output_dir, 'ndvi_by_date.csv')
    df_by_date.to_csv(date_summary_file, index=False, encoding='utf-8')
    print(f"日付ごとのサマリーファイルを作成しました: {date_summary_file}")

def main():
    """メイン関数"""
    args = parse_arguments()
    
    # 地点情報の読み込み
    print(f"地点情報ファイルを読み込み中: {args.points}")
    points = read_points(args.points)
    print(f"  {len(points)}個の地点を読み込みました")
    
    # .ncファイルの検索
    print(f".ncファイルを検索中: {args.nc_dir}")
    nc_files = find_nc_files(args.nc_dir)
    print(f"  {len(nc_files)}個の.ncファイルを見つけました")
    
    # テストモードの場合は最初の1つのファイルのみ使用
    if args.test:
        if len(nc_files) > 0:
            nc_files = nc_files[:1]
            print(f"  テストモード: 最初の1つのファイルのみ使用します: {os.path.basename(nc_files[0])}")
        
        # テストモードでは最初の1つの地点のみ使用
        if len(points) > 0:
            points = points[:1]
            print(f"  テストモード: 最初の1つの地点のみ使用します: 地点 {points[0]['No']} (緯度: {points[0]['Lat']}, 経度: {points[0]['Lon']})")
    
    if not points or not nc_files:
        print("エラー: 地点情報または.ncファイルが見つかりませんでした。")
        return
    
    # 出力ディレクトリの設定
    if args.output is None:
        # 出力先が指定されていない場合は.ncファイルのディレクトリにndvi_resultsフォルダを作成
        nc_dir = os.path.abspath(args.nc_dir)
        output_dir = os.path.join(nc_dir, "ndvi_results")
        print(f"出力先が指定されていないため、.ncファイルのディレクトリに出力します: {output_dir}")
    else:
        # 絶対パスに変換
        if os.path.isabs(args.output):
            # 絶対パスの場合はそのまま使用
            output_dir = args.output
        else:
            # 相対パスの場合は.ncファイルのディレクトリからの相対パスとして扱う
            nc_dir = os.path.abspath(args.nc_dir)
            output_dir = os.path.join(nc_dir, args.output)
        print(f"指定された出力先を使用します: {output_dir}")
    
    # 出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)
    print(f"出力ディレクトリ: {output_dir}")
    
    # 処理の実行
    print(f"処理を開始します（ワーカー数: {args.workers}）")
    results = []
    
    # 並列処理
    if args.workers > 1:
        print(f"並列処理モード: {args.workers}ワーカー")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = []
            for point in points:
                for nc_file in nc_files:
                    future = executor.submit(
                        process_point_file, 
                        point, 
                        nc_file, 
                        args.region_size, 
                        output_dir
                    )
                    futures.append(future)
            
            # 結果の収集
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"エラー: 処理中に例外が発生しました: {e}")
    else:
        print("逐次処理モード")
        # 逐次処理
        for point in points:
            for nc_file in nc_files:
                try:
                    result = process_point_file(
                        point, 
                        nc_file, 
                        args.region_size, 
                        output_dir
                    )
                    results.append(result)
                except Exception as e:
                    print(f"エラー: 処理中に例外が発生しました: {e}")
    
    print(f"処理が完了しました。合計: {len(results)}件")
    
    # 成功・失敗の集計
    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count
    print(f"  成功: {success_count}件")
    print(f"  失敗: {fail_count}件")
    
    # サマリーファイルの作成
    if args.summary:
        print("サマリーファイルを作成中...")
        create_summary(results, output_dir)

if __name__ == "__main__":
    main() 