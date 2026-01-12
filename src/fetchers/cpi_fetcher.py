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
            # cat02コード（指数）を取得（初期化時に取得）
            self.estat_cat02_code = self._get_cat02_code_for_index()
        else:
            raise ValueError(f"サポートされていない市場コード: {market_code}")
    
    def _get_cat02_code_for_index(self) -> Optional[str]:
        """
        getMetaInfo APIを使用して、statsDataId=0003427113のcat02定義を取得し、
        「指数」に該当するcat02コードを特定する
        
        Returns:
            str: 指数に該当するcat02コード（見つからない場合はNone）
        """
        try:
            if not self.estat_api_key:
                return None
            
            # getMetaInfo APIのエンドポイント
            url = "https://api.e-stat.go.jp/rest/3.0/app/json/getMetaInfo"
            
            # パラメータ設定
            params = {
                "appId": self.estat_api_key,
                "statsDataId": self.estat_stats_data_id,
                "lang": "J"
            }
            
            # メタ情報取得
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            meta_json = response.json()
            
            # フルパスでアクセス
            meta_data = meta_json.get("GET_META_INFO", {})
            if not meta_data:
                print("e-Stat getMetaInfo APIからメタ情報を取得できませんでした")
                return None
            
            class_obj = meta_data.get("METADATA_INF", {}).get("CLASS_INF", {})
            if not class_obj:
                print("e-Stat getMetaInfo APIにCLASS_INFがありません")
                return None
            
            # CLASS_OBJを取得（配列または辞書）
            class_objs = class_obj.get("CLASS_OBJ", [])
            if not isinstance(class_objs, list):
                if isinstance(class_objs, dict):
                    class_objs = [class_objs]
                else:
                    print("e-Stat getMetaInfo APIにCLASS_OBJがありません")
                    return None
            
            # cat02（時系列分類）を探す
            for class_item in class_objs:
                class_id = class_item.get("@id", "")
                if class_id == "cat02":
                    # CLASS内のITEMを確認
                    items = class_item.get("CLASS", {}).get("ITEM", [])
                    if not isinstance(items, list):
                        if isinstance(items, dict):
                            items = [items]
                        else:
                            continue
                    
                    # 「指数」に該当するITEMを探す
                    for item in items:
                        item_code = item.get("@code", "")
                        item_name = item.get("@name", "")
                        item_name_alt = item.get("$", "")
                        
                        # 「指数」を含む名前を探す
                        name_to_check = item_name or item_name_alt or ""
                        if "指数" in name_to_check:
                            print(f"e-Stat cat02コード（指数）を特定: {item_code} ({name_to_check})")
                            return item_code
            
            print("e-Stat getMetaInfo APIから「指数」に該当するcat02コードが見つかりませんでした")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"e-Stat getMetaInfo APIリクエストエラー: {e}")
            return None
        except Exception as e:
            print(f"e-Stat getMetaInfo API取得エラー: {e}")
            return None
    
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
    
    def _fetch_from_estat(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        e-Stat APIからCPIデータを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
        
        Returns:
            DataFrame: CPIデータ（CPI, CPI_YoY）
        """
        try:
            # APIキーは初期化時にチェック済みだが、念のため再確認
            if not self.estat_api_key:
                raise RuntimeError("ESTAT_API_KEYが設定されていません")
            
            # e-Stat APIのエンドポイント
            url = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
            
            # cat02コードが取得できていない場合はエラー
            if not self.estat_cat02_code:
                print("エラー: cat02コード（指数）が取得できていません。getMetaInfo APIを確認してください。")
                return pd.DataFrame()
            
            # パラメータ設定（API側でフィルタリング）
            params = {
                "appId": self.estat_api_key,
                "statsDataId": self.estat_stats_data_id,
                "lang": "J",
                "metaGetFlg": "N",
                "cntGetFlg": "N",
                "cdCat01": "0001",        # 総合
                "cdCat02": self.estat_cat02_code,  # 指数（getMetaInfoから取得）
                "cdArea": "00000"          # 全国
            }
            
            # データ取得
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data_json = response.json()
            
            # フルパスでアクセス（必須修正点①）
            get_stats_data = data_json.get("GET_STATS_DATA", {})
            if not get_stats_data:
                print("e-Stat APIからGET_STATS_DATAを取得できませんでした")
                return pd.DataFrame()
            
            statistical_data = get_stats_data.get("STATISTICAL_DATA", {})
            if not statistical_data:
                print("e-Stat APIからSTATISTICAL_DATAを取得できませんでした")
                return pd.DataFrame()
            
            # 統計表情報を確認（デバッグ用）
            table_inf = statistical_data.get("TABLE_INF", {})
            stat_name = table_inf.get("STAT_NAME", {})
            if isinstance(stat_name, dict):
                stat_name_value = stat_name.get("$", "")
                if "国勢調査" in stat_name_value or "人口" in stat_name_value:
                    print(f"警告: 統計表ID {self.estat_stats_data_id} は国勢調査データです。正しいCPI統計表IDを設定してください。")
                    return pd.DataFrame()
            
            # データポイントを抽出（フルパスでアクセス）
            data_points = []
            data_inf = statistical_data.get("DATA_INF", {})
            if not data_inf:
                print("e-Stat APIからDATA_INFを取得できませんでした")
                return pd.DataFrame()
            
            value_list = data_inf.get("VALUE")
            if not value_list:
                print("e-Stat APIからVALUEを取得できませんでした")
                return pd.DataFrame()
            
            # VALUEが配列の場合
            if isinstance(value_list, list):
                for value_info in value_list:
                    # 必須修正点③：VALUEパース処理の強化
                    # time取得順序: @time → time
                    date_str = value_info.get("@time") or value_info.get("time")
                    
                    # value取得順序: @value → value → $
                    value_str = value_info.get("@value") or value_info.get("value") or value_info.get("$")
                    
                    if date_str and value_str:
                        try:
                            # 年次データ（YYYY000000形式）をスキップ
                            if len(date_str) == 10 and date_str.endswith("000000"):
                                continue
                            
                            # 月次データ（YYYYMM形式）を処理
                            if len(date_str) == 6:
                                # 月初日として設定
                                date = datetime.strptime(date_str, "%Y%m")
                                value = float(value_str)
                                data_points.append({"date": date, "CPI": value})
                        except (ValueError, TypeError) as e:
                            # デバッグログを残す
                            print(f"デバッグ: VALUEパースエラー - date_str: {date_str}, value_str: {value_str}, エラー: {e}")
                            continue
            
            # VALUEが単一オブジェクトの場合
            elif isinstance(value_list, dict):
                value_info = value_list
                # 必須修正点③：VALUEパース処理の強化
                date_str = value_info.get("@time") or value_info.get("time")
                value_str = value_info.get("@value") or value_info.get("value") or value_info.get("$")
                
                if date_str and value_str:
                    try:
                        # 年次データをスキップ
                        if len(date_str) == 10 and date_str.endswith("000000"):
                            pass
                        elif len(date_str) == 6:
                            date = datetime.strptime(date_str, "%Y%m")
                            value = float(value_str)
                            data_points.append({"date": date, "CPI": value})
                    except (ValueError, TypeError) as e:
                        # デバッグログを残す
                        print(f"デバッグ: VALUEパースエラー - date_str: {date_str}, value_str: {value_str}, エラー: {e}")
            
            if not data_points:
                print("e-Stat APIから有効なCPIデータを取得できませんでした")
                stat_name_value = ""
                if isinstance(stat_name, dict):
                    stat_name_value = stat_name.get("$", "")
                print(f"デバッグ: 統計表名: {stat_name_value}, 取得データポイント数: 0")
                return pd.DataFrame()
            
            # DataFrameに変換
            df = pd.DataFrame(data_points)
            if df.empty:
                return pd.DataFrame()
            
            df.set_index("date", inplace=True)
            df.sort_index(inplace=True)  # 昇順ソート
            
            # API側でフィルタリング済みのため、ローカル側でのフィルタリングは行わない
            # （start_date, end_dateは使用しない）
            
            # 前年比（YoY）を計算（12ヶ月差分で算出）
            df['CPI_YoY'] = df['CPI'].pct_change(periods=12, fill_method=None) * 100
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"e-Stat APIリクエストエラー: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"e-Stat CPIデータ取得エラー: {e}")
            return pd.DataFrame()
    
    def fetch(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        CPIデータを取得し、前年比（YoY）を計算
        
        Args:
            start_date: 開始日
            end_date: 終了日
        
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
                df = self._fetch_from_estat(start_date, end_date)
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

