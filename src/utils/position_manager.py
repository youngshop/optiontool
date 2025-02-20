import json
from typing import List, Dict
from src.api.okx_api import OkxApi

class PositionManager:
    @staticmethod
    def save_positions(positions: List[Dict], filename: str):
        """保存期权组合到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(positions, f, indent=4, ensure_ascii=False)
            
    @staticmethod
    def load_positions(filename: str) -> List[Dict]:
        """从文件加载期权组合并更新价格"""
        with open(filename, 'r', encoding='utf-8') as f:
            positions = json.load(f)
            
        # 更新期权价格
        api = OkxApi()
        for pos in positions:
            price_info = api.get_option_price(
                underlying=pos["underlying"],
                expiry=pos["expiry"],
                strike=pos["strike"],
                option_type=pos["type"]
            )
            if price_info:
                pos["price"] = price_info["ask_price"] if pos["side"] == "buy" else price_info["bid_price"]
                
        return positions 