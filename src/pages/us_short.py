"""
米国 - 短期ページ
"""
from .base_page import BasePage
from typing import Dict, Any
from src.fetchers.price_fetcher import PriceFetcher
from src.fetchers.rate_fetcher import RateFetcher
from src.fetchers.cpi_fetcher import CPIFetcher
from src.fetchers.eps_per_fetcher import EPSPERFetcher
from src.facts.price_fact import PriceFact
from src.facts.rate_fact import RateFact
from src.facts.cpi_fact import CPIFact
from src.facts.eps_per_fact import EPSPERFact
from src.interpretations.price_interpretation import PriceInterpretation
from src.interpretations.rate_interpretation import RateInterpretation
from src.interpretations.cpi_interpretation import CPIIntepretation
from src.interpretations.eps_per_interpretation import EPSPERInterpretation
from src.charts.price_chart import PriceChart
from src.charts.rate_chart import RateChart
from src.charts.cpi_chart import CPIChart
from src.charts.eps_per_chart import EPSPERChart


class USShortPage(BasePage):
    """米国 - 短期ページクラス"""
    
    def __init__(self):
        super().__init__("US", "short")
    
    def build(self) -> Dict[str, Any]:
        """ページを組み立てる"""
        years = self.get_years()
        switchable_years = self.get_switchable_years()
        start_date, end_date = self.get_date_range()
        
        # 市場設定からシンボルを取得
        price_index = self.market_config.get("price_index", "S&P500")
        symbol_config = next(
            (idx for idx in self.market_config["indices"] if idx["name"] == price_index),
            None
        )
        symbol = symbol_config["symbol"] if symbol_config else "^GSPC"
        
        result = {
            "market_code": self.market_code,
            "market_name": self.market_config.get("name", "米国"),
            "timeframe_code": self.timeframe_code,
            "timeframe_name": self.timeframe_config.get("name", "短期"),
            "years": years,
            "switchable_years": switchable_years,
            "charts": {},
            "interpretations": {},
            "facts": {}  # Factデータを保存（ヒートマップ・矢印用）
        }
        
        # ① 株価指数チャート
        try:
            price_fetcher = PriceFetcher(self.market_code, symbol)
            price_data = price_fetcher.fetch(start_date, end_date)
            
            if not price_data.empty:
                price_fact = PriceFact(self.market_code)
                price_fact.load_data(price_data)
                
                # Factデータを保存（ヒートマップ・矢印用）
                result["facts"]["price"] = {
                    "is_valid": price_fact.is_valid,
                    "data": price_data,
                    "symbol": symbol
                }
                
                price_chart = PriceChart(self.market_config.get("name", "米国"), price_index)
                chart_fig = price_chart.create_chart(price_data, years, switchable_years)
                result["charts"]["price"] = price_chart.to_html(chart_fig)
                
                price_interpretation = PriceInterpretation(price_fact)
                result["interpretations"]["price"] = price_interpretation.generate_summary()
            else:
                result["charts"]["price"] = "<p>この指標は現在データを取得できません</p>"
                result["interpretations"]["price"] = "株価データは現在取得できません。"
        except Exception as e:
            print(f"株価チャート生成エラー: {e}")
            result["charts"]["price"] = "<p>この指標は現在データを取得できません</p>"
            result["interpretations"]["price"] = "株価データは現在取得できません。"
        
        # ② 政策金利 + 長期金利チャート
        try:
            policy_fetcher = RateFetcher(self.market_code, "policy")
            long_rate_fetcher = RateFetcher(self.market_code, "long_10y")
            
            policy_data = policy_fetcher.fetch(start_date, end_date)
            long_rate_data = long_rate_fetcher.fetch(start_date, end_date)
            
            if not policy_data.empty or not long_rate_data.empty:
                rate_chart = RateChart(self.market_config.get("name", "米国"))
                chart_fig = rate_chart.create_chart(policy_data, long_rate_data, years)
                result["charts"]["rate"] = rate_chart.to_html(chart_fig)
                
                # 解釈（政策金利と長期金利の両方）
                interpretations = []
                if not policy_data.empty:
                    policy_fact = RateFact(self.market_code, "policy")
                    policy_fact.load_data(policy_data)
                    # Factデータを保存（矢印用）
                    result["facts"]["policy_rate"] = {
                        "is_valid": policy_fact.is_valid,
                        "data": policy_data
                    }
                    policy_interpretation = RateInterpretation(policy_fact)
                    interpretations.append(policy_interpretation.generate_summary())
                
                if not long_rate_data.empty:
                    long_rate_fact = RateFact(self.market_code, "long_10y")
                    long_rate_fact.load_data(long_rate_data)
                    # Factデータを保存（矢印用）
                    result["facts"]["long_rate"] = {
                        "is_valid": long_rate_fact.is_valid,
                        "data": long_rate_data
                    }
                    long_rate_interpretation = RateInterpretation(long_rate_fact)
                    interpretations.append(long_rate_interpretation.generate_summary())
                
                result["interpretations"]["rate"] = " ".join(interpretations)
            else:
                result["charts"]["rate"] = "<p>この指標は現在データを取得できません</p>"
                result["interpretations"]["rate"] = "金利データは現在取得できません。"
        except Exception as e:
            print(f"金利チャート生成エラー: {e}")
            result["charts"]["rate"] = "<p>この指標は現在データを取得できません</p>"
            result["interpretations"]["rate"] = "金利データは現在取得できません。"
        
        # ③ CPIチャート
        try:
            cpi_fetcher = CPIFetcher(self.market_code)
            cpi_data = cpi_fetcher.fetch(start_date, end_date)
            
            if not cpi_data.empty:
                cpi_fact = CPIFact(self.market_code)
                cpi_fact.load_data(cpi_data)
                
                # Factデータを保存（矢印用）
                result["facts"]["cpi"] = {
                    "is_valid": cpi_fact.is_valid,
                    "data": cpi_data
                }
                
                cpi_chart = CPIChart(self.market_config.get("name", "米国"))
                chart_fig = cpi_chart.create_chart(cpi_data, years)
                result["charts"]["cpi"] = cpi_chart.to_html(chart_fig)
                
                cpi_interpretation = CPIIntepretation(cpi_fact)
                result["interpretations"]["cpi"] = cpi_interpretation.generate_summary()
            else:
                result["charts"]["cpi"] = "<p>この指標は現在データを取得できません</p>"
                result["interpretations"]["cpi"] = "CPIデータは現在取得できません。"
        except Exception as e:
            print(f"CPIチャート生成エラー: {e}")
            result["charts"]["cpi"] = "<p>この指標は現在データを取得できません</p>"
            result["interpretations"]["cpi"] = "CPIデータは現在取得できません。"
        
        # ④ EPS + PERチャート（20年固定）
        try:
            eps_per_fetcher = EPSPERFetcher(self.market_code, symbol)
            eps_per_data = eps_per_fetcher.fetch()  # 20年固定なので日付指定なし
            
            if not eps_per_data.empty:
                eps_per_fact = EPSPERFact(self.market_code)
                eps_per_fact.load_data(eps_per_data)
                
                eps_per_chart = EPSPERChart(self.market_config.get("name", "米国"))
                chart_fig = eps_per_chart.create_chart(eps_per_data)
                result["charts"]["eps_per"] = eps_per_chart.to_html(chart_fig)
                
                eps_per_interpretation = EPSPERInterpretation(eps_per_fact)
                result["interpretations"]["eps_per"] = eps_per_interpretation.generate_summary()
            else:
                result["charts"]["eps_per"] = "<p>この指標は現在データを取得できません</p>"
                result["interpretations"]["eps_per"] = "EPS/PERデータは現在取得できません。"
        except Exception as e:
            print(f"EPS/PERチャート生成エラー: {e}")
            result["charts"]["eps_per"] = "<p>この指標は現在データを取得できません</p>"
            result["interpretations"]["eps_per"] = "EPS/PERデータは現在取得できません。"
        
        return result

