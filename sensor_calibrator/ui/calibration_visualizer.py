"""
Calibration Visualizer Module

2D传感器方位可视化组件 - 轻量级实现
使用 tkinter Canvas 替代 matplotlib，确保 10 FPS 性能不受影响
"""

import tkinter as tk
from typing import Optional


class CalibrationVisualizer2D:
    """
    2D传感器方位可视化
    
    显示传感器在不同位置的朝向示意图，帮助用户正确放置传感器。
    使用 Canvas 绘制，性能开销极小。
    """
    
    # 6个校准位置定义
    POSITIONS = [
        {
            'name': '+X', 
            'down_axis': 'X+', 
            'view': 'side', 
            'gravity_dir': 'right',
            'description': '右侧面朝下 (X+)',
            'tip': '右侧朝下'
        },
        {
            'name': '-X', 
            'down_axis': 'X-', 
            'view': 'side', 
            'gravity_dir': 'left',
            'description': '左侧面朝下 (X-)',
            'tip': '左侧朝下'
        },
        {
            'name': '+Y',
            'down_axis': 'Y+',
            'view': 'front',
            'gravity_dir': 'down',
            'description': '底面朝下 (Y+)',
            'tip': '底面朝下'
        },
        {
            'name': '-Y',
            'down_axis': 'Y-',
            'view': 'front',
            'gravity_dir': 'up',
            'description': '顶面朝下 (Y-)',
            'tip': '顶面朝下'
        },
        {
            'name': '+Z',
            'down_axis': 'Z+',
            'view': 'front',
            'gravity_dir': 'down',
            'description': '前面朝下 (Z+)',
            'tip': '前面朝下'
        },
        {
            'name': '-Z',
            'down_axis': 'Z-',
            'view': 'front',
            'gravity_dir': 'up',
            'description': '后面朝下 (Z-)',
            'tip': '后面朝下'
        },
    ]
    
    # 颜色配置
    COLORS = {
        'X': '#ff4444',        # X轴 - 红色
        'Y': '#44ff44',        # Y轴 - 绿色
        'Z': '#4444ff',        # Z轴 - 蓝色
        'sensor': '#888888',   # 传感器主体 - 灰色
        'sensor_edge': '#333333',  # 传感器边框
        'gravity': '#ff9900',  # 重力 - 橙色
        'text': '#333333',     # 文字
        'text_highlight': '#000000',  # 高亮文字
        'bg': '#f0f0f0',       # 背景
    }
    
    def __init__(self, canvas: tk.Canvas):
        """
        初始化2D可视化器
        
        Args:
            canvas: tkinter Canvas 控件
        """
        self.canvas = canvas
        self.current_idx = 0
        self.width = 200
        self.height = 200
        
        # 缓存静态元素ID，避免重复创建
        self._static_elements = []
        self._dynamic_elements = []
        
    def set_position(self, position_idx: int):
        """
        设置当前显示的位置
        
        Args:
            position_idx: 位置索引 (0-5)
        """
        if not 0 <= position_idx <= 5:
            return
            
        self.current_idx = position_idx
        self._draw()
        
    def _draw(self):
        """绘制2D示意图"""
        # 清除所有元素
        self.canvas.delete("all")
        
        pos = self.POSITIONS[self.current_idx]
        
        # 根据视图类型绘制
        if pos['view'] == 'top':
            self._draw_top_view(pos)
        elif pos['view'] == 'side':
            self._draw_side_view(pos)
        else:  # front
            self._draw_front_view(pos)
            
    def _draw_top_view(self, pos):
        """俯视图 - 从上方看（Z轴相关）"""
        cx, cy = 90, 90  # 中心点
        
        # 绘制传感器矩形（顶面）
        rect_size = 60
        x1, y1 = cx - rect_size, cy - rect_size
        x2, y2 = cx + rect_size, cy + rect_size
        
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=self.COLORS['sensor'],
            outline=self.COLORS['sensor_edge'],
            width=2
        )
        
        # X轴（水平方向）
        self.canvas.create_line(
            x1, cy, x2, cy,
            fill=self.COLORS['X'],
            width=3
        )
        self.canvas.create_text(
            cx + rect_size + 15, cy,
            text="X",
            fill=self.COLORS['X'],
            font=('Segoe UI', 10, 'bold')
        )
        
        # Y轴（垂直方向）
        self.canvas.create_line(
            cx, y1, cx, y2,
            fill=self.COLORS['Y'],
            width=3
        )
        self.canvas.create_text(
            cx, y1 - 15,
            text="Y",
            fill=self.COLORS['Y'],
            font=('Segoe UI', 10, 'bold')
        )
        
        # Z轴（用圆圈表示，因为是俯视）
        self.canvas.create_oval(
            cx - 8, cy - 8, cx + 8, cy + 8,
            fill=self.COLORS['Z'],
            outline='white',
            width=2
        )
        self.canvas.create_text(
            cx, cy + rect_size + 20,
            text="Z",
            fill=self.COLORS['Z'],
            font=('Segoe UI', 10, 'bold')
        )
        
        # 重力指示 - 简化显示
        if pos['down_axis'] == 'Z+':
            # Z+ 朝下
            self.canvas.create_text(
                cx, 20,
                text="● Z+ (顶面朝下)",
                fill=self.COLORS['gravity'],
                font=('Segoe UI', 8, 'bold')
            )
        else:
            # Z- 朝下
            self.canvas.create_text(
                cx, 20,
                text="◎ Z- (底面朝下)",
                fill=self.COLORS['gravity'],
                font=('Segoe UI', 8, 'bold')
            )
            
    def _draw_side_view(self, pos):
        """侧视图 - 从侧面看（X轴相关）"""
        cx, cy = 90, 90
        
        # 绘制传感器矩形（侧面）
        rect_width = 60
        rect_height = 80
        x1 = cx - rect_width
        y1 = cy - rect_height // 2
        x2 = cx + rect_width
        y2 = cy + rect_height // 2
        
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=self.COLORS['sensor'],
            outline=self.COLORS['sensor_edge'],
            width=2
        )
        
        # X轴（水平方向 - 从侧面看是横线）
        self.canvas.create_line(
            x1 - 20, cy, x2 + 20, cy,
            fill=self.COLORS['X'],
            width=4
        )
        self.canvas.create_text(
            x1 - 30, cy,
            text="X",
            fill=self.COLORS['X'],
            font=('Segoe UI', 10, 'bold')
        )
        
        # Y轴（垂直方向 - 从侧面看是纵线）
        self.canvas.create_line(
            cx, y1 - 10, cx, y2 + 10,
            fill=self.COLORS['Y'],
            width=2,
            dash=(4, 2)  # 虚线表示在内部
        )
        self.canvas.create_text(
            cx - 15, y1 - 15,
            text="Y",
            fill=self.COLORS['Y'],
            font=('Segoe UI', 10)
        )
        
        # Z轴（垂直于屏幕 - 用圆点表示）
        self.canvas.create_oval(
            cx - 6, cy - 6, cx + 6, cy + 6,
            fill=self.COLORS['Z'],
            outline='white',
            width=1
        )
        self.canvas.create_text(
            cx + 20, cy - 15,
            text="Z",
            fill=self.COLORS['Z'],
            font=('Segoe UI', 10)
        )
        
        # 重力箭头
        if pos['down_axis'] == 'X+':
            # X+ 朝下：箭头向右
            self._draw_arrow(cx, y1 - 25, 0, -20, self.COLORS['gravity'], "重力 →")
        else:
            # X- 朝下：箭头向左
            self._draw_arrow(cx, y1 - 25, 0, -20, self.COLORS['gravity'], "← 重力", flip=True)
            
    def _draw_front_view(self, pos):
        """正视图 - 从前面看（Y轴相关）"""
        cx, cy = 90, 90
        
        # 绘制传感器矩形（前面）
        rect_size = 70
        x1 = cx - rect_size
        y1 = cy - rect_size
        x2 = cx + rect_size
        y2 = cy + rect_size
        
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=self.COLORS['sensor'],
            outline=self.COLORS['sensor_edge'],
            width=2
        )
        
        # Y轴（垂直方向 - 从前面看是纵线）
        self.canvas.create_line(
            cx, y1 - 20, cx, y2 + 20,
            fill=self.COLORS['Y'],
            width=4
        )
        self.canvas.create_text(
            cx + 15, y1 - 25,
            text="Y",
            fill=self.COLORS['Y'],
            font=('Segoe UI', 10, 'bold')
        )
        
        # X轴（水平方向 - 从前面看是横线）
        self.canvas.create_line(
            x1 - 10, cy, x2 + 10, cy,
            fill=self.COLORS['X'],
            width=2,
            dash=(4, 2)  # 虚线表示在内部
        )
        self.canvas.create_text(
            x1 - 20, cy - 10,
            text="X",
            fill=self.COLORS['X'],
            font=('Segoe UI', 10)
        )
        
        # Z轴（垂直于屏幕）
        self.canvas.create_oval(
            cx - 6, cy - 6, cx + 6, cy + 6,
            fill=self.COLORS['Z'],
            outline='white',
            width=1
        )
        self.canvas.create_text(
            cx + 20, cy + 20,
            text="Z",
            fill=self.COLORS['Z'],
            font=('Segoe UI', 10)
        )
        
        # 重力箭头 - 支持Y轴和Z轴朝下
        if pos['down_axis'] in ('Y+', 'Z+'):
            # Y+ 或 Z+ 朝下：箭头向下
            axis_label = "Y+" if pos['down_axis'] == 'Y+' else "Z+"
            self._draw_arrow(cx + rect_size + 30, cy, 20, 0, self.COLORS['gravity'], f"↓ {axis_label}")
        else:
            # Y- 或 Z- 朝下：箭头向上
            axis_label = "Y-" if pos['down_axis'] == 'Y-' else "Z-"
            self._draw_arrow(cx + rect_size + 30, cy, -20, 0, self.COLORS['gravity'], f"{axis_label} ↑", flip=True)
            
    def _draw_arrow(self, x, y, dx, dy, color, text, flip=False):
        """
        绘制箭头
        
        Args:
            x, y: 起点坐标
            dx, dy: 箭头方向向量
            color: 颜色
            text: 文字标签
            flip: 是否翻转文字位置
        """
        if flip:
            # 水平翻转
            dx = -dx
            x -= 40
            
        # 绘制箭头线
        self.canvas.create_line(
            x, y, x + dx, y + dy,
            fill=color,
            width=3,
            arrow=tk.LAST
        )
        
        # 绘制文字
        text_x = x + dx // 2
        text_y = y + dy // 2 - 15
        self.canvas.create_text(
            text_x, text_y,
            text=text,
            fill=color,
            font=('Segoe UI', 9, 'bold')
        )
        
    def get_current_description(self) -> str:
        """获取当前位置的描述文字"""
        return self.POSITIONS[self.current_idx]['description']
        
    def get_current_tip(self) -> str:
        """获取当前位置的操作提示"""
        return self.POSITIONS[self.current_idx]['tip']
        
    def highlight_axis(self, axis: str):
        """
        高亮指定轴线（用于采集时的视觉反馈）
        
        Args:
            axis: 'X', 'Y', 或 'Z'
        """
        # 创建闪烁效果 - 用较粗的线条重绘对应轴线
        cx, cy = 100, 100
        
        if axis == 'X':
            self.canvas.create_line(
                20, cy, 180, cy,
                fill=self.COLORS['X'],
                width=6,
                stipple='gray50'  # 半透明闪烁效果
            )
        elif axis == 'Y':
            self.canvas.create_line(
                cx, 20, cx, 180,
                fill=self.COLORS['Y'],
                width=6,
                stipple='gray50'
            )
        elif axis == 'Z':
            self.canvas.create_oval(
                cx - 12, cy - 12, cx + 12, cy + 12,
                fill='',
                outline=self.COLORS['Z'],
                width=4
            )


class CalibrationPositionIndicator:
    """
    6位置状态指示器
    
    显示6个校准位置的完成状态，带颜色和动画效果。
    """
    
    POSITIONS = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]
    
    # 状态颜色
    STATUS_COLORS = {
        'pending': '#cccccc',      # 未开始 - 灰色
        'collecting': '#ffcc00',   # 采集中 - 黄色
        'completed': '#44aa44',    # 已完成 - 绿色
        'error': '#ff4444',        # 错误 - 红色
    }
    
    def __init__(self, parent: tk.Widget, theme=None):
        """
        初始化位置指示器
        
        Args:
            parent: 父容器
            theme: 主题配置（可选）
        """
        self.parent = parent
        self.theme = theme
        self.labels = []
        self.status = ['pending'] * 6
        
        self._create_widgets()
        
    def _create_widgets(self):
        """创建UI组件"""
        # 主框架
        self.frame = tk.Frame(self.parent, bg=self._get_bg_color())
        
        # 创建6个位置标签
        for i, pos in enumerate(self.POSITIONS):
            pos_frame = tk.Frame(self.frame, bg=self._get_bg_color())
            pos_frame.pack(side="left", expand=True, padx=5)
            
            # 位置名称
            tk.Label(
                pos_frame,
                text=f"{i+1}. {pos}",
                bg=self._get_bg_color(),
                fg='#666666',
                font=('Segoe UI', 9)
            ).pack()
            
            # 状态指示（使用圆形符号）
            lbl = tk.Label(
                pos_frame,
                text="○",
                bg=self._get_bg_color(),
                fg=self.STATUS_COLORS['pending'],
                font=('Segoe UI', 16)
            )
            lbl.pack()
            self.labels.append(lbl)
            
    def _get_bg_color(self):
        """获取背景色"""
        if self.theme:
            return getattr(self.theme, 'BG_CARD', '#ffffff')
        return '#ffffff'
        
    def set_position_status(self, position_idx: int, status: str):
        """
        设置指定位置的状态
        
        Args:
            position_idx: 位置索引 (0-5)
            status: 'pending', 'collecting', 'completed', 'error'
        """
        if not 0 <= position_idx <= 5:
            return
            
        self.status[position_idx] = status
        color = self.STATUS_COLORS.get(status, self.STATUS_COLORS['pending'])
        
        # 根据状态设置符号
        symbols = {
            'pending': '○',
            'collecting': '◐',
            'completed': '●',
            'error': '✗',
        }
        symbol = symbols.get(status, '○')
        
        self.labels[position_idx].config(
            text=symbol,
            fg=color
        )
        
    def set_current_position(self, position_idx: int):
        """
        设置当前正在采集的位置（高亮显示）
        
        Args:
            position_idx: 位置索引 (0-5)
        """
        for i, lbl in enumerate(self.labels):
            if i == position_idx and self.status[i] == 'pending':
                lbl.config(font=('Segoe UI', 18, 'bold'))
            else:
                lbl.config(font=('Segoe UI', 16))
                
    def reset_all(self):
        """重置所有状态为待处理"""
        for i in range(6):
            self.set_position_status(i, 'pending')
            
    def get_frame(self):
        """获取框架引用（用于布局）"""
        return self.frame
