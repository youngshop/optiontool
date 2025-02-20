from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, 
    QSpinBox, QPushButton, QLabel
)
from src.api.okx_api import OkxApi

class OptionSelector(QWidget):
    def __init__(self, on_add_position):
        super().__init__()
        self.api = OkxApi()
        self.on_add_position = on_add_position
        
        layout = QHBoxLayout(self)
        
        # 标的选择
        self.underlying = "BTC-USD"
        layout.addWidget(QLabel("标的:"))
        underlying_combo = QComboBox()
        underlying_combo.addItem(self.underlying)
        layout.addWidget(underlying_combo)
        
        # 到期日选择
        layout.addWidget(QLabel("到期日:"))
        self.expiry_combo = QComboBox()
        self.expiry_combo.setMinimumWidth(120)
        self.expiry_combo.currentTextChanged.connect(self.on_expiry_changed)
        layout.addWidget(self.expiry_combo)
        
        # 行权价选择
        layout.addWidget(QLabel("行权价:"))
        self.strike_combo = QComboBox()
        self.strike_combo.setMinimumWidth(100)
        layout.addWidget(self.strike_combo)
        
        # 期权类型选择
        layout.addWidget(QLabel("类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["看涨", "看跌"])
        layout.addWidget(self.type_combo)
        
        # 买卖方向选择
        layout.addWidget(QLabel("方向:"))
        self.side_combo = QComboBox()
        self.side_combo.addItems(["买入", "卖出"])
        layout.addWidget(self.side_combo)
        
        # 数量选择
        layout.addWidget(QLabel("数量:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setValue(1)
        layout.addWidget(self.quantity_spin)
        
        # 添加按钮
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self.add_position)
        layout.addWidget(add_btn)
        
        # 加载到期日列表
        self.load_expiry_dates()
        
    def load_expiry_dates(self):
        """加载到期日列表"""
        dates = self.api.get_expiry_dates()
        self.expiry_combo.addItems(dates)
        
    def on_expiry_changed(self, expiry):
        """当选择的到期日变化时更新行权价列表"""
        if not expiry:
            return
            
        strikes = self.api.get_strike_prices(self.underlying, expiry)
        self.strike_combo.clear()
        self.strike_combo.addItems([str(strike) for strike in strikes])
        
    def add_position(self):
        """添加新的期权头寸"""
        expiry = self.expiry_combo.currentText()
        strike = self.strike_combo.currentText()
        option_type = "C" if self.type_combo.currentText() == "看涨" else "P"
        
        # 获取期权价格
        price_info = self.api.get_option_price(
            underlying=self.underlying,
            expiry=expiry,
            strike=strike,
            option_type=option_type
        )
        
        if price_info:
            # 买入用卖一价，卖出用买一价
            is_buy = self.side_combo.currentText() == "买入"
            price = price_info["ask_price"] if is_buy else price_info["bid_price"]
            
            position = {
                "underlying": self.underlying,
                "expiry": expiry,
                "strike": float(strike),
                "type": option_type,
                "side": "buy" if is_buy else "sell",
                "quantity": self.quantity_spin.value(),
                "price": price  # 保存权利金
            }
            self.on_add_position(position)
        else:
            print("无法获取期权价格，请稍后重试") 