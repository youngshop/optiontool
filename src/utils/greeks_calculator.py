import numpy as np
from typing import List, Dict
from scipy.stats import norm
from datetime import datetime

def calculate_time_to_expiry(expiry_str: str) -> float:
    """计算到期时间（年化）"""
    expiry_date = datetime.strptime(expiry_str, "%y%m%d")
    now = datetime.now()
    days_to_expiry = (expiry_date - now).days + (expiry_date - now).seconds / 86400
    return max(days_to_expiry / 365, 0.00001)  # 避免除以0

def calculate_greeks(positions: List[Dict]) -> Dict[str, float]:
    """计算期权组合的希腊字母（BS模式）"""
    total_greeks = {
        "Delta": 0.0,
        "Gamma": 0.0,
        "Theta": 0.0,
        "Vega": 0.0,
        "Rho": 0.0
    }
    
    # 市场参数
    spot_price = float(positions[0]["strike"])  # 当前价格，需要从市场获取
    risk_free_rate = 0.035  # 年化无风险利率
    volatility = 0.65  # 年化波动率
    
    for pos in positions:
        strike = float(pos["strike"])
        expiry = calculate_time_to_expiry(pos["expiry"])
        quantity = float(pos["quantity"])
        is_call = pos["type"] == "C"
        is_long = pos["side"] == "buy"
        sign = 1 if is_long else -1
        
        # BS模型参数
        sqrt_t = np.sqrt(expiry)
        d1 = (np.log(spot_price/strike) + (risk_free_rate + volatility**2/2)*expiry) / (volatility*sqrt_t)
        d2 = d1 - volatility*sqrt_t
        
        # Delta
        if is_call:
            delta = norm.cdf(d1)
        else:
            delta = norm.cdf(d1) - 1
        total_greeks["Delta"] += sign * delta * quantity
        
        # Gamma (相同公式对看涨和看跌期权)
        gamma = norm.pdf(d1) / (spot_price * volatility * sqrt_t)
        total_greeks["Gamma"] += sign * gamma * quantity
        
        # Vega (相同公式对看涨和看跌期权)
        vega = spot_price * sqrt_t * norm.pdf(d1) / 100  # 除以100转换为1%波动率变化
        total_greeks["Vega"] += sign * vega * quantity
        
        # Theta (每天的时间价值损失)
        theta_t = -spot_price * norm.pdf(d1) * volatility / (2 * sqrt_t)
        if is_call:
            theta = theta_t - risk_free_rate * strike * np.exp(-risk_free_rate*expiry) * norm.cdf(d2)
        else:
            theta = theta_t + risk_free_rate * strike * np.exp(-risk_free_rate*expiry) * norm.cdf(-d2)
        total_greeks["Theta"] += sign * theta * quantity / 365  # 转换为每天的theta
        
        # Rho (利率变化1%对期权价格的影响)
        if is_call:
            rho = strike * expiry * np.exp(-risk_free_rate*expiry) * norm.cdf(d2) / 100
        else:
            rho = -strike * expiry * np.exp(-risk_free_rate*expiry) * norm.cdf(-d2) / 100
        total_greeks["Rho"] += sign * rho * quantity
    
    return total_greeks 