#!/usr/bin/env python3

import os
import requests
from bs4 import BeautifulSoup
import urllib.parse
import argparse
from tqdm import tqdm
import concurrent.futures

def download_file(url, output_dir, overwrite=False):
    """
    指定されたURLからファイルをダウンロードする関数
    
    Args:
        url (str): ダウンロードするファイルのURL
        output_dir (str): ダウンロードしたファイルを保存するディレクトリ
        overwrite (bool): 既存のファイルを上書きするかどうか
    
    Returns:
        bool: ダウンロードが成功したかどうか
    """
    # URLからファイル名を取得
    filename = urllib.parse.unquote(os.path.basename(url))
    output_path = os.path.join(output_dir, filename)
    
    # 既にファイルが存在し、上書きしない設定の場合はスキップ
    if os.path.exists(output_path) and not overwrite:
        print(f"ファイルが既に存在します: {filename} (スキップ)")
        return False
    
    try:
        # ファイルのダウンロード
        response = requests.get(url, stream=True)
        response.raise_for_status()  # エラーがあれば例外を発生させる
        
        # ファイルサイズを取得（ヘッダーに含まれている場合）
        total_size = int(response.headers.get('content-length', 0))
        
        # ファイルを保存
        with open(output_path, 'wb') as f:
            if total_size == 0:  # ファイルサイズが不明の場合
                f.write(response.content)
            else:
                # プログレスバー付きでダウンロード
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
        
        print(f"ダウンロード完了: {filename}")
        return True
    
    except Exception as e:
        print(f"ダウンロード失敗: {filename} - エラー: {str(e)}")
        # 部分的にダウンロードされたファイルを削除
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

def get_nc_file_urls(base_url):
    """
    指定されたURLからNetCDFファイル(.nc)のURLリストを取得する関数
    
    Args:
        base_url (str): スクレイピング対象のベースURL
    
    Returns:
        list: NetCDFファイルのURLリスト
    """
    try:
        # ウェブページを取得
        response = requests.get(base_url)
        response.raise_for_status()
        
        # HTMLを解析
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # リンクを抽出
        links = soup.find_all('a')
        
        # .ncファイルのURLリストを作成
        nc_urls = []
        for link in links:
            href = link.get('href')
            if href and href.endswith('.nc'):
                # 相対URLを絶対URLに変換
                full_url = urllib.parse.urljoin(base_url, href)
                nc_urls.append(full_url)
        
        return nc_urls
    
    except Exception as e:
        print(f"URLの取得に失敗しました: {str(e)}")
        return []

def main():
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='NCEIのウェブサイトからNetCDFファイルをダウンロードするスクリプト')
    parser.add_argument('--url', '-u', type=str, default='https://www.ncei.noaa.gov/data/land-surface-reflectance/access/1990/',
                        help='ダウンロード元のURL')
    parser.add_argument('--output', '-o', type=str, default='./nc_files',
                        help='ダウンロードしたファイルを保存するディレクトリ')
    parser.add_argument('--limit', '-l', type=int, default=0,
                        help='ダウンロードするファイル数の上限（0は無制限）')
    parser.add_argument('--overwrite', '-w', action='store_true',
                        help='既存のファイルを上書きする')
    parser.add_argument('--workers', '-p', type=int, default=3,
                        help='並列ダウンロードのワーカー数')
    
    args = parser.parse_args()
    
    # 出力ディレクトリの作成
    os.makedirs(args.output, exist_ok=True)
    
    # NetCDFファイルのURLリストを取得
    print(f"{args.url} からファイルリストを取得中...")
    nc_urls = get_nc_file_urls(args.url)
    
    if not nc_urls:
        print("ダウンロード可能なNetCDFファイルが見つかりませんでした。")
        return
    
    # ダウンロード数の制限を適用
    if args.limit > 0 and args.limit < len(nc_urls):
        print(f"ダウンロード数を {args.limit} 件に制限します（全 {len(nc_urls)} 件）")
        nc_urls = nc_urls[:args.limit]
    else:
        print(f"合計 {len(nc_urls)} 件のファイルをダウンロードします")
    
    # 並列ダウンロードの実行
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        # ダウンロードタスクを作成
        futures = [executor.submit(download_file, url, args.output, args.overwrite) for url in nc_urls]
        
        # 結果を集計
        success_count = 0
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                success_count += 1
    
    print(f"ダウンロード完了: {success_count}/{len(nc_urls)} ファイル")

if __name__ == "__main__":
    main() 