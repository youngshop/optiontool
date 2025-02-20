from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox, QSpinBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

from src.ui.option_selector import OptionSelector
from src.utils.payoff_calculator import calculate_payoff
from src.utils.position_manager import PositionManager
from src.utils.greeks_calculator import calculate_greeks  # 待实现

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("期权组合分析工具")
        self.setMinimumSize(1000, 800)
        
        # 存储期权头寸
        self.positions = []
        
        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 添加期权选择器
        self.option_selector = OptionSelector(self.add_position)
        layout.addWidget(self.option_selector)
        
        # 添加头寸列表
        self.position_table = QTableWidget()
        self.setup_position_table()
        layout.addWidget(self.position_table)
        
        # 添加删除按钮
        delete_btn = QPushButton("删除选中")
        delete_btn.clicked.connect(self.delete_selected_positions)
        layout.addWidget(delete_btn)
        
        # 添加图表
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)
        
        # 添加按钮布局
        button_layout = QHBoxLayout()
        
        # 添加保存/加载按钮
        save_btn = QPushButton("保存组合")
        save_btn.clicked.connect(self.save_positions)
        load_btn = QPushButton("加载组合")
        load_btn.clicked.connect(self.load_positions)
        
        # 添加希腊字母显示
        self.greeks_table = QTableWidget()
        self.setup_greeks_table()
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(load_btn)
        layout.addLayout(button_layout)
        layout.addWidget(self.greeks_table)
        
    def setup_position_table(self):
        """设置头寸表格"""
        self.position_table.setColumnCount(7)  # 增加一列显示权利金
        self.position_table.setHorizontalHeaderLabels([
            "标的", "到期日", "行权价", "类型", "方向", "数量", "权利金"
        ])
        self.position_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    def add_position(self, position):
        """添加新的期权头寸"""
        self.positions.append(position)
        self.update_position_table()
        self.update_chart()
        self.update_greeks()
        
    def update_position_table(self):
        """更新头寸表格"""
        self.position_table.setRowCount(len(self.positions))
        
        for i, pos in enumerate(self.positions):
            # 设置颜色
            color = QColor("#4CAF50") if (
                (pos["type"] == "C" and pos["side"] == "buy") or
                (pos["type"] == "P" and pos["side"] == "sell")
            ) else QColor("#F44336")
            
            # 不可编辑的列
            for col in range(3):
                item = QTableWidgetItem(str([
                    pos["underlying"],
                    pos["expiry"],
                    pos["strike"]
                ][col]))
                item.setForeground(QBrush(color))
                self.position_table.setItem(i, col, item)
            
            # 类型选择（可编辑）
            type_combo = QComboBox()
            type_combo.addItems(["看涨", "看跌"])
            type_combo.setCurrentText("看涨" if pos["type"] == "C" else "看跌")
            type_combo.currentTextChanged.connect(
                lambda text, row=i: self.on_type_changed(row, text)
            )
            type_combo.setStyleSheet(f"color: {color.name()}")
            self.position_table.setCellWidget(i, 3, type_combo)
            
            # 方向选择（可编辑）
            side_combo = QComboBox()
            side_combo.addItems(["买入", "卖出"])
            side_combo.setCurrentText("买入" if pos["side"] == "buy" else "卖出")
            side_combo.currentTextChanged.connect(
                lambda text, row=i: self.on_side_changed(row, text)
            )
            side_combo.setStyleSheet(f"color: {color.name()}")
            self.position_table.setCellWidget(i, 4, side_combo)
            
            # 数量输入（可编辑）
            quantity_spin = QSpinBox()
            quantity_spin.setMinimum(1)
            quantity_spin.setValue(pos["quantity"])
            quantity_spin.valueChanged.connect(
                lambda value, row=i: self.on_quantity_changed(row, value)
            )
            quantity_spin.setStyleSheet(f"color: {color.name()}")
            self.position_table.setCellWidget(i, 5, quantity_spin)
            
            # 添加权利金列
            price_item = QTableWidgetItem(f"{pos['price']:.4f}")
            price_item.setForeground(QBrush(color))
            self.position_table.setItem(i, 6, price_item)
    
    def on_type_changed(self, row, text):
        """当期权类型改变时更新数据"""
        self.positions[row]["type"] = "C" if text == "看涨" else "P"
        self.update_chart()
        self.update_greeks()
    
    def on_side_changed(self, row, text):
        """当买卖方向改变时更新数据"""
        self.positions[row]["side"] = "buy" if text == "买入" else "sell"
        self.update_chart()
        self.update_greeks()
    
    def on_quantity_changed(self, row, value):
        """当数量改变时更新数据"""
        self.positions[row]["quantity"] = value
        self.update_chart()
        self.update_greeks()
    
    def update_chart(self):
        """更新盈亏图表"""
        if not self.positions:
            return
            
        # 生成价格点
        strikes = [float(pos["strike"]) for pos in self.positions]
        min_strike = min(strikes)
        max_strike = max(strikes)
        center_price = (min_strike + max_strike) / 2
        price_range = max_strike - min_strike
        
        # 当只有一个期权时，price_range会是0，导致生成的价格点都是相同的
        # 修改为使用行权价的一定比例作为范围
        if price_range == 0:
            price_range = min_strike * 0.2  # 使用行权价的20%作为范围
        
        spot_prices = np.linspace(
            center_price - price_range,  # 居中显示
            center_price + price_range,
            200
        )
        
        # 计算盈亏
        payoff = calculate_payoff(self.positions, spot_prices)
        
        # 绘制图表
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 绘制盈亏曲线
        ax.plot(spot_prices, payoff, linewidth=2)
        ax.grid(True)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 标记关键点
        for strike in strikes:
            payoff_at_strike = calculate_payoff(self.positions, np.array([strike]))[0]
            ax.plot(strike, payoff_at_strike, 'ro')  # 红点标记
            ax.annotate(f'K={strike}', 
                       xy=(strike, payoff_at_strike),
                       xytext=(10, 10),
                       textcoords='offset points')
        
        # 标记盈亏平衡点
        def find_zero(x):
            return calculate_payoff(self.positions, np.array([x]))[0]
        
        try:
            breakeven_points = []
            for x0 in strikes:
                # 在行权价附近寻找盈亏平衡点
                x_range = np.linspace(x0 * 0.8, x0 * 1.2, 1000)
                y_values = calculate_payoff(self.positions, x_range)
                
                # 找出y值符号改变的位置
                sign_changes = np.where(np.diff(np.signbit(y_values)))[0]
                
                for idx in sign_changes:
                    # 使用线性插值找到更精确的零点
                    x1, x2 = x_range[idx], x_range[idx + 1]
                    y1, y2 = y_values[idx], y_values[idx + 1]
                    root = x1 - y1 * (x2 - x1) / (y2 - y1)
                    
                    # 检查是否是有效的盈亏平衡点
                    if min(spot_prices) <= root <= max(spot_prices):
                        breakeven_points.append(root)
            
            # 移除重复的盈亏平衡点
            breakeven_points = sorted(set([round(x, 2) for x in breakeven_points]))
            
            for point in breakeven_points:
                ax.plot(point, 0, 'go')  # 绿点标记
                ax.annotate(f'BE={point:.0f}', 
                           xy=(point, 0),
                           xytext=(10, -20),
                           textcoords='offset points')
        except Exception as e:
            print(f"计算盈亏平衡点出错: {e}")
        
        ax.set_xlabel("标的价格")
        ax.set_ylabel("盈亏(BTC)")
        
        # 绘制零轴，使用深蓝色
        ax.axhline(y=0, color='navy', linestyle='-', alpha=0.5, linewidth=1.5)
        
        # 设置更精确的y轴刻度，限制最多16条
        max_abs_payoff = max(abs(payoff))
        y_min = -max_abs_payoff * 1.1
        y_max = max_abs_payoff * 1.1
        
        # 计算合适的刻度间隔，使得刻度数不超过16
        y_range = y_max - y_min
        min_ticks = 8
        max_ticks = 16
        
        for n in range(min_ticks, max_ticks + 1):
            step = y_range / n
            # 将步长规整到合适的值
            magnitude = 10 ** np.floor(np.log10(step))
            for mult in [1, 2, 2.5, 5, 10]:
                if mult * magnitude > step:
                    step = mult * magnitude
                    break
            if y_range / step <= max_ticks:
                break
        
        y_ticks = np.arange(
            np.floor(y_min/step) * step,
            np.ceil(y_max/step) * step + step/2,
            step
        )
        
        ax.set_yticks(y_ticks)
        ax.yaxis.set_major_formatter(plt.FormatStrFormatter('%.4f'))
        
        self.canvas.draw()
    
    def delete_selected_positions(self):
        """删除选中的期权头寸"""
        selected_rows = set(item.row() for item in self.position_table.selectedItems())
        if not selected_rows:
            return
            
        # 从后向前删除，避免索引变化
        for row in sorted(selected_rows, reverse=True):
            del self.positions[row]
            
        self.update_position_table()
        self.update_chart()
        self.update_greeks()
    
    def setup_greeks_table(self):
        """设置希腊字母表格"""
        self.greeks_table.setColumnCount(5)
        self.greeks_table.setHorizontalHeaderLabels([
            "Delta", "Gamma", "Theta(每天)", "Vega(1%)", "Rho(1%)"
        ])
        self.greeks_table.setRowCount(1)
        
    def update_greeks(self):
        """更新希腊字母"""
        if not self.positions:
            return
            
        greeks = calculate_greeks(self.positions)
        for i, (name, value) in enumerate(greeks.items()):
            self.greeks_table.setItem(0, i, QTableWidgetItem(f"{value:.4f}"))
            
    def save_positions(self):
        """保存当前期权组合"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存期权组合", "", "JSON文件 (*.json)"
        )
        if filename:
            PositionManager.save_positions(self.positions, filename)
            
    def load_positions(self):
        """加载期权组合"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "加载期权组合", "", "JSON文件 (*.json)"
        )
        if filename:
            self.positions = PositionManager.load_positions(filename)
            self.update_position_table()
            self.update_chart()
            self.update_greeks() 