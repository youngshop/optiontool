import numpy as np
from typing import List, Dict

def calculate_payoff(positions: List[Dict], spot_prices: np.ndarray) -> np.ndarray:
    """计算期权组合在不同价格点的盈亏"""
    total_payoff = np.zeros_like(spot_prices, dtype=float)
    
    for position in positions:
        payoff = calculate_single_position_payoff(position, spot_prices)
        total_payoff += payoff
        
    return total_payoff

def calculate_single_position_payoff(position: Dict, spot_prices: np.ndarray) -> np.ndarray:
    """计算单个期权头寸的盈亏"""
    strike = float(position["strike"])
    quantity = float(position["quantity"])
    price = float(position["price"])  # 权利金(BTC)
    
    if position["type"] == "C":  # 看涨期权
        if position["side"] == "buy":  # 买入看涨
            # 亏损固定为权利金
            payoff = np.full_like(spot_prices, -price, dtype=float)
            # 价格超过行权价时，获得额外收益（需要除以100000转换为BTC单位）
            in_the_money = spot_prices > strike
            payoff[in_the_money] += (spot_prices[in_the_money] - strike) / 100000
        else:  # 卖出看涨
            # 收益固定为权利金
            payoff = np.full_like(spot_prices, price, dtype=float)
            # 价格超过行权价时，产生亏损（需要除以100000转换为BTC单位）
            in_the_money = spot_prices > strike
            payoff[in_the_money] -= (spot_prices[in_the_money] - strike) / 100000
    else:  # 看跌期权
        if position["side"] == "buy":  # 买入看跌
            # 亏损固定为权利金
            payoff = np.full_like(spot_prices, -price, dtype=float)
            # 价格低于行权价时，获得额外收益（需要除以100000转换为BTC单位）
            in_the_money = spot_prices < strike
            payoff[in_the_money] += (strike - spot_prices[in_the_money]) / 100000
        else:  # 卖出看跌
            # 收益固定为权利金
            payoff = np.full_like(spot_prices, price, dtype=float)
            # 价格低于行权价时，产生亏损（需要除以100000转换为BTC单位）
            in_the_money = spot_prices < strike
            payoff[in_the_money] -= (strike - spot_prices[in_the_money]) / 100000
    
    return payoff * quantity 