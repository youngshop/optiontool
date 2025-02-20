import requests
from typing import List, Dict
from datetime import datetime

class OkxApi:
    def __init__(self):
        self.base_url = "https://www.okx.com"
        
    def get_instruments(self) -> List[Dict]:
        """获取所有期权合约信息"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v5/public/instruments",
                params={"instType": "OPTION"}
            )
            response.raise_for_status()
            return response.json()["data"]
        except Exception as e:
            print(f"获取期权合约列表失败: {e}")
            return []

    def get_expiry_dates(self, underlying="BTC-USD"):
        """获取期权到期日列表"""
        try:
            # 调用获取期权合约信息接口
            url = f"{self.base_url}/api/v5/public/instruments"
            params = {
                "instType": "OPTION",
                "uly": underlying
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["code"] == "0":
                # 提取所有到期日并去重
                expiry_dates = set()
                for instrument in data["data"]:
                    # 将时间戳转换为日期字符串 "YYMMDD"
                    expiry_ts = int(instrument["expTime"])
                    expiry_date = datetime.fromtimestamp(expiry_ts/1000)
                    expiry_str = expiry_date.strftime("%y%m%d")
                    expiry_dates.add(expiry_str)
                
                # 排序并返回
                return sorted(list(expiry_dates))
            else:
                print(f"获取到期日失败: {data}")
                return []
                
        except Exception as e:
            print(f"获取到期日出错: {e}")
            return []
            
    def get_strike_prices(self, underlying="BTC-USD", expiry=None):
        """获取某个到期日的行权价列表"""
        try:
            url = f"{self.base_url}/api/v5/public/instruments"
            params = {
                "instType": "OPTION",
                "uly": underlying
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["code"] == "0":
                # 提取指定到期日的行权价
                strikes = set()
                for instrument in data["data"]:
                    inst_expiry = datetime.fromtimestamp(
                        int(instrument["expTime"])/1000
                    ).strftime("%y%m%d")
                    
                    if inst_expiry == expiry:
                        strike = float(instrument["stk"])
                        strikes.add(strike)
                
                # 排序并返回
                return sorted(list(strikes))
            else:
                print(f"获取行权价失败: {data}")
                return []
                
        except Exception as e:
            print(f"获取行权价出错: {e}")
            return []

    def get_option_price(self, underlying="BTC-USD", expiry=None, strike=None, option_type="C"):
        """获取期权价格"""
        try:
            # 构造期权合约名称
            # 格式: BTC-USD-240228-45000-C
            # strike需要补足为5位数
            strike_str = f"{int(float(strike)):05d}"
            inst_id = f"{underlying}-{expiry}-{strike_str}-{option_type}"
            
            url = f"{self.base_url}/api/v5/market/ticker"
            params = {
                "instId": inst_id
            }
            print(f"请求期权价格，合约ID: {inst_id}")  # 调试信息
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["code"] == "0" and data["data"]:
                ticker = data["data"][0]
                return {
                    "bid_price": float(ticker["bidPx"]) if ticker["bidPx"] else 0,  # 买一价
                    "ask_price": float(ticker["askPx"]) if ticker["askPx"] else 0,  # 卖一价
                    "last_price": float(ticker["last"]) if ticker["last"] else 0    # 最新成交价
                }
            else:
                print(f"获取期权价格失败: {data}")
                return None
                
        except Exception as e:
            print(f"获取期权价格出错: {e}")
            return None