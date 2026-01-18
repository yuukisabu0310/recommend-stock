"""
CPI（消費者物価指数）データ取得
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from fredapi import Fred
import os
import requests
from dotenv import load_dotenv
from .base_fetcher import BaseFetcher

load_dotenv()


class CPIFetcher(BaseFetcher):
    """CPIデータを取得するクラス"""
    
    def __init__(self, market_code: str):
        """
        Args:
            market_code: 市場コード（"US" or "JP"）
        """
        super().__init__(market_code)
        
        if market_code == "US":
            # FRED APIキーの取得（環境変数から取得）
            api_key = os.getenv("FRED_API_KEY")
            if not api_key:
                raise RuntimeError("FRED_API_KEYが設定されていません（GitHub Secretsを確認してください）")
            self.fred = Fred(api_key=api_key)
            self.series_id = "CPIAUCSL"  # Consumer Price Index for All Urban Consumers: All Items
        elif market_code == "JP":
            # e-Stat APIキーの取得（環境変数から取得）
            self.estat_api_key = os.getenv("ESTAT_API_KEY")
            if not self.estat_api_key:
                raise RuntimeError("ESTAT_API_KEYが設定されていません（GitHub Secretsを確認してください）")
            # 消費者物価指数（全国・総合）の統計表ID
            # 2020年基準の消費者物価指数（全国・総合指数）の統計表ID
            # e-Statサイト: https://www.e-stat.go.jp/api/info-cat/news/cpi-info202107
            # 統計表ID: 0003427113（2020年基準）
            self.estat_stats_data_id = "0003427113"
        else:
            raise ValueError(f"サポートされていない市場コード: {market_code}")
    
    def _fetch_from_fred(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        FRED APIからCPIデータを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
        
        Returns:
            DataFrame: CPIデータ（CPI, CPI_YoY）
        """
        try:
            # FREDからデータ取得
            data = self.fred.get_series(self.series_id, start=start_date, end=end_date)
            
            if data.empty:
                return pd.DataFrame()
            
            # DataFrameに変換
            df = pd.DataFrame({
                'CPI': data
            })
            
            # 前年比（YoY）を計算
            df['CPI_YoY'] = df['CPI'].pct_change(periods=12, fill_method=None) * 100  # 12ヶ月前との比較
            
            # 日付をindexに設定
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            return df
            
        except Exception as e:
            print(f"FRED CPIデータ取得エラー: {e}")
            return pd.DataFrame()
    
    def _parse_estat_value_list(self, value_list) -> pd.DataFrame:
        """
        e-Stat APIのVALUEリストをパースしてDataFrameに変換
        
        Returns:
            DataFrame: CPIデータ（date index, CPI列）
        """
        if isinstance(value_list, dict):
            value_list = [value_list]
        
        data_points = []
        excluded_yearly = 0
        excluded_invalid = 0
        
        for value_info in value_list:
            date_str = value_info.get("@time") or value_info.get("time")
            value_str = value_info.get("$") or value_info.get("@value") or value_info.get("value")
            
            if not date_str or not value_str:
                excluded_invalid += 1
                continue
            
            try:
                if len(date_str) != 10:
                    excluded_invalid += 1
                    continue
                
                month_str = date_str[6:8]
                if month_str == "00":
                    excluded_yearly += 1
                    continue
                
                year = date_str[0:4]
                month = month_str
                date = datetime(int(year), int(month), 1)
                value = float(value_str)
                data_points.append({"date": date, "CPI": value})
                
            except Exception:
                excluded_invalid += 1
                continue
        
        print(f"DEBUG: 月次データ抽出 - 有効: {len(data_points)}件, 年平均除外: {excluded_yearly}件, 無効除外: {excluded_invalid}件")
        
        if not data_points:
            return pd.DataFrame()
        
        df = pd.DataFrame(data_points)
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)
        
        return df
    
    def _rebase_cpi_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        基準年ごとに分離されたCPIデータを再基準化して1本の系列に接続
        
        Args:
            df: 基準年ごとに分離されたCPIデータ（date index, CPI列）
        
        Returns:
            DataFrame: 再基準化されたCPIデータ（date index, CPI列）
        """
        if df.empty:
            return df
        
        # 基準年の切り替わりを検出（2020年1月を基準点とする）
        # 実際のe-Statデータでは、2020基準は2020年1月以降、2015基準は2015年1月〜2020年1月
        # ただし、statsDataId=0003427113は2020基準のみを含む可能性が高い
        
        # まず、データの期間を確認
        min_date = df.index.min()
        max_date = df.index.max()
        
        # 2020年1月を基準点として、それ以前と以降で分離
        rebase_date = datetime(2020, 1, 1)
        
        if min_date >= rebase_date:
            # 2020基準のみの場合
            print(f"DEBUG: 2020基準のみ検出（{min_date} 〜 {max_date}）")
            return df
        
        # 2015基準と2020基準が混在している場合
        df_2015 = df[df.index < rebase_date].copy()
        df_2020 = df[df.index >= rebase_date].copy()
        
        if df_2015.empty or df_2020.empty:
            # 片方しかない場合はそのまま返す
            print(f"DEBUG: 単一基準年検出（{min_date} 〜 {max_date}）")
            return df
        
        # 接続月（2020年1月）で両系列が存在するか確認
        if rebase_date not in df_2015.index or rebase_date not in df_2020.index:
            # 接続月が存在しない場合は、最も近い月を使用
            last_2015 = None
            first_2020 = None
            
            if rebase_date not in df_2015.index:
                # 2015基準の最後の月を取得
                last_2015 = df_2015.index.max()
                if last_2015 >= datetime(2019, 1, 1):
                    # 2019年以降のデータがあれば、2020年1月に最も近い月を探す
                    df_2015_near = df_2015[df_2015.index >= datetime(2019, 1, 1)]
                    if not df_2015_near.empty:
                        last_2015 = df_2015_near.index.max()
            else:
                last_2015 = rebase_date
            
            if rebase_date not in df_2020.index:
                # 2020基準の最初の月を取得
                first_2020 = df_2020.index.min()
            else:
                first_2020 = rebase_date
            
            # 接続月を決定
            if last_2015 is not None and first_2020 is not None:
                if last_2015 < first_2020:
                    # 期間が離れている場合は、2020年1月を使用
                    connect_date = rebase_date
                else:
                    connect_date = first_2020
            elif first_2020 is not None:
                connect_date = first_2020
            elif last_2015 is not None:
                connect_date = last_2015
            else:
                connect_date = rebase_date
        else:
            connect_date = rebase_date
        
        # 接続月の値を取得
        if connect_date in df_2015.index and connect_date in df_2020.index:
            cpi_2015_connect = df_2015.loc[connect_date, "CPI"]
            cpi_2020_connect = df_2020.loc[connect_date, "CPI"]
        else:
            # 接続月が存在しない場合は、最も近い月を使用
            if connect_date not in df_2015.index:
                # 2015基準の最後の月を取得
                df_2015_before = df_2015[df_2015.index < connect_date]
                if not df_2015_before.empty:
                    last_2015_date = df_2015_before.index.max()
                    cpi_2015_connect = df_2015.loc[last_2015_date, "CPI"]
                else:
                    # 2015基準データがない場合は2020基準のみを返す
                    print("DEBUG: 2015基準データが接続月付近に存在しないため、2020基準のみを使用")
                    return df_2020
            else:
                cpi_2015_connect = df_2015.loc[connect_date, "CPI"]
            
            if connect_date not in df_2020.index:
                # 2020基準の最初の月を取得
                df_2020_after = df_2020[df_2020.index > connect_date]
                if not df_2020_after.empty:
                    first_2020_date = df_2020_after.index.min()
                    cpi_2020_connect = df_2020.loc[first_2020_date, "CPI"]
                else:
                    # 2020基準データがない場合は2015基準のみを返す
                    print("DEBUG: 2020基準データが接続月付近に存在しないため、2015基準のみを使用")
                    return df_2015
            else:
                cpi_2020_connect = df_2020.loc[connect_date, "CPI"]
        
        # スケーリング係数を算出
        if cpi_2015_connect == 0:
            print("DEBUG: 2015基準の接続月値が0のため、2020基準のみを使用")
            return df_2020
        
        scale = cpi_2020_connect / cpi_2015_connect
        print(f"DEBUG: 基準年接続 - 接続月: {connect_date.strftime('%Y-%m')}, 2015基準値: {cpi_2015_connect:.2f}, 2020基準値: {cpi_2020_connect:.2f}, スケール: {scale:.6f}")
        
        # 2015基準データを2020基準に変換
        df_2015_adjusted = df_2015.copy()
        df_2015_adjusted["CPI"] = df_2015_adjusted["CPI"] * scale
        
        # 接続月以前は調整済み2015基準、接続月以降は2020基準
        df_combined = pd.concat([
            df_2015_adjusted[df_2015_adjusted.index < connect_date],
            df_2020[df_2020.index >= connect_date]
        ])
        
        df_combined.sort_index(inplace=True)
        
        print(f"DEBUG: 再基準化完了 - 2015基準: {len(df_2015)}件, 2020基準: {len(df_2020)}件, 結合後: {len(df_combined)}件")
        
        return df_combined
    
    def _fetch_from_estat(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        e-Stat APIからCPIデータを取得し、基準年接続処理を実施してTradingViewと一致させる
        """
        try:
            if not self.estat_api_key:
                raise RuntimeError("ESTAT_API_KEYが設定されていません")
            
            url = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
            
            # statsDataId=0003427113 (2020年基準 消費者物価指数) の構造:
            # - cat01: 品目 (0001 = 総合)
            # - area: 地域 (00000 = 全国)
            # - cat02: 存在しないため指定してはいけない
            # - 時間指定（timeFrom / timeTo / cdTime）は使用不可
            # - @time 形式: YYYY00MMMM（10桁）
            #   例: 2025001111 → 2025年1月、2025001010 → 2025年10月、2024000000 → 年平均（除外）
            # - 月次判定: time[6:8] != "00"
            # - sectionHeaderFlg を指定しないと VALUE 構造が不安定
            
            stats_id = "0003427113"
            cat01 = "0001"   # 総合
            area = "00000"   # 全国
            
            params = {
                "appId": self.estat_api_key,
                "lang": "J",
                "statsDataId": stats_id,
                "cdCat01": cat01,
                "cdArea": area,
                "metaGetFlg": "N",
                "cntGetFlg": "N",
                "sectionHeaderFlg": "1"   # ★必須
            }
            
            # データ取得
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data_json = response.json()
            
            get_stats_data = data_json.get("GET_STATS_DATA", {})
            if not get_stats_data:
                print(f"APIレスポンスエラー: {data_json}")  # エラー詳細を見るために出力変更
                return pd.DataFrame()

            statistical_data = get_stats_data.get("STATISTICAL_DATA", {})
            data_inf = statistical_data.get("DATA_INF", {})
            value_list = data_inf.get("VALUE")
            
            if not value_list:
                print(f"e-Stat CPI取得失敗: statsDataId={stats_id}, cat01={cat01}, area={area} (VALUEなし)")
                return pd.DataFrame()

            # リストか辞書かで分岐する処理（正規化してリストとして扱う）
            if isinstance(value_list, dict):
                value_list = [value_list]
            
            # ① APIレスポンスの生データ構造を全件ログ出力
            print(f"DEBUG: VALUE 件数: {len(value_list)}")
            for idx, value_info in enumerate(value_list[:5]):  # 最初の5件をサンプル表示
                time_key = "@time" if "@time" in value_info else "time"
                value_key = "$" if "$" in value_info else ("@value" if "@value" in value_info else "value")
                print(f"DEBUG: VALUE[{idx}] - {time_key}: {value_info.get(time_key)}, {value_key}: {value_info.get(value_key)}")

            # Step 2: VALUE の正しい解釈（月次データ抽出）
            df_raw = self._parse_estat_value_list(value_list)
            
            if df_raw.empty:
                print("有効なデータポイントが見つかりませんでした")
                return pd.DataFrame()
            
            print(f"DEBUG: 月次データ抽出完了: {len(df_raw)}件（{df_raw.index.min()} 〜 {df_raw.index.max()}）")
            
            # Step 3-4: 基準年の分離取得と再基準化ロジック
            df_rebased = self._rebase_cpi_series(df_raw)
            
            if df_rebased.empty:
                print("再基準化後のデータが空です")
                return pd.DataFrame()
            
            # Step 5: 単一 CPI レベル系列の完成
            print(f"DEBUG: 再基準化後: {len(df_rebased)}件（{df_rebased.index.min()} 〜 {df_rebased.index.max()}）")
            
            # Step 7: TradingView との検証（必須ログ）
            if datetime(2019, 4, 1) in df_rebased.index:
                print(f"DEBUG: 2019-04 CPIレベル: {df_rebased.loc[datetime(2019, 4, 1), 'CPI']:.2f}")
            if datetime(2020, 1, 1) in df_rebased.index:
                print(f"DEBUG: 2020-01 CPIレベル: {df_rebased.loc[datetime(2020, 1, 1), 'CPI']:.2f}")
            if not df_rebased.empty:
                latest_date = df_rebased.index.max()
                print(f"DEBUG: 直近月({latest_date.strftime('%Y-%m')}) CPIレベル: {df_rebased.loc[latest_date, 'CPI']:.2f}")
            
            # 直近10年フィルタ（Python側で実施）
            ten_years_ago = pd.Timestamp.today() - pd.DateOffset(years=10)
            df_filtered = df_rebased[df_rebased.index >= ten_years_ago]
            
            print(f"DEBUG: 直近10年フィルタ後: {len(df_filtered)}件")
            
            # Step 6: YoY 計算（最後に行う）
            df_filtered = df_filtered.copy()
            df_filtered['CPI_YoY'] = df_filtered['CPI'].pct_change(12) * 100
            
            # YoY検証ログ（2022〜2024）
            for year in [2022, 2023, 2024]:
                check_date = datetime(year, 6, 1)  # 6月をサンプル
                if check_date in df_filtered.index:
                    cpi_yoy = df_filtered.loc[check_date, 'CPI_YoY']
                    print(f"DEBUG: {year}-06 YoY: {cpi_yoy:.2f}%")
            
            return df_filtered

        except Exception as e:
            print(f"e-Stat CPIデータ取得エラー: {e}")
            return pd.DataFrame()
    
    def fetch(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        CPIデータを取得し、前年比（YoY）を計算
        
        Args:
            start_date: 開始日（USのみ有効、JPの場合は無視して直近10年を自動取得）
            end_date: 終了日（USのみ有効、JPの場合は無視して直近10年を自動取得）
        
        Returns:
            DataFrame: CPI前年比データ
                - index: 日付（月次）
                - columns: ['CPI', 'CPI_YoY']
        """
        try:
            # 市場コードに応じて取得元を切り替え
            if self.market_code == "US":
                df = self._fetch_from_fred(start_date, end_date)
            elif self.market_code == "JP":
                # JPの場合はstart_date/end_dateを無視し、API側で直近10年を自動計算
                df = self._fetch_from_estat(start_date=None, end_date=None)
            else:
                print(f"サポートされていない市場コード: {self.market_code}")
                return pd.DataFrame()
            
            if df.empty:
                return pd.DataFrame()
            
            # 生データを保存
            self.save_raw_data(df, "cpi_yoy")
            
            return df
            
        except Exception as e:
            print(f"CPIデータ取得エラー ({self.market_code}): {e}")
            return pd.DataFrame()

