"""
ChartManager - 管理 Matplotlib 图表的创建和更新

职责：
- 初始化4个子图（MPU加速度、ADXL加速度、MPU陀螺仪、重力矢量）
- 高效更新图表数据（支持blit优化）
- 动态调整坐标轴范围
- 更新图表上的统计信息
"""

import time
from typing import Dict, List, Optional, Tuple, Any
from collections import deque

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from . import Config, UIConfig


class ChartManager:
    """
    管理传感器数据可视化图表
    
    提供高效的图表更新，支持blit增量绘制优化
    """
    
    def __init__(self, parent_widget, figsize: Tuple[float, float] = (14, 9)):
        """
        初始化图表管理器
        
        Args:
            parent_widget: 父级 tkinter widget
            figsize: 图表尺寸 (宽, 高)
        """
        self.parent = parent_widget
        self.figsize = figsize
        
        # 图表组件
        self.fig: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None
        
        # 子图引用
        self.ax1: Optional[Axes] = None  # MPU6050加速度
        self.ax2: Optional[Axes] = None  # ADXL355加速度
        self.ax3: Optional[Axes] = None  # MPU6050陀螺仪
        self.ax4: Optional[Axes] = None  # 重力矢量
        
        # 统计文本框
        self.ax1_stats_text = None
        self.ax2_stats_text = None
        self.ax3_stats_text = None
        self.ax4_stats_text = None
        
        # 线条引用
        self.mpu_accel_lines: List = []
        self.adxl_accel_lines: List = []
        self.mpu_gyro_lines: List = []
        self.gravity_line = None
        
        # 性能优化相关
        self._blit_backgrounds: Optional[Dict] = None
        self._blit_artists: List = []
        self._blit_initialized: bool = False
        
        # 频率控制
        self.last_chart_update: float = 0
        self.chart_update_interval: float = Config.CHART_UPDATE_INTERVAL
        self.last_y_limit_update: float = 0
        self.y_limit_update_interval: float = Config.Y_LIMIT_UPDATE_INTERVAL
        
    def setup_plots(self) -> FigureCanvasTkAgg:
        """
        设置matplotlib图表
        
        Returns:
            FigureCanvasTkAgg: matplotlib画布
        """
        # 创建图形和子图
        self.fig, axes = plt.subplots(2, 2, figsize=self.figsize)
        self.ax1 = axes[0, 0]
        self.ax2 = axes[0, 1]
        self.ax3 = axes[1, 0]
        self.ax4 = axes[1, 1]
        
        self.fig.suptitle("Sensor Data Visualization with Statistics", fontsize=14)
        
        # 设置全局字体大小
        plt.rcParams["font.size"] = 10
        plt.rcParams["axes.titlesize"] = 12
        plt.rcParams["axes.labelsize"] = 11
        plt.rcParams["legend.fontsize"] = 10
        
        # 颜色配置
        colors = [UIConfig.CHART_COLOR_X, UIConfig.CHART_COLOR_Y, UIConfig.CHART_COLOR_Z]
        labels = ["X", "Y", "Z"]
        
        # 设置MPU6050加速度计子图
        self._setup_mpu_accel_plot(colors, labels)
        
        # 设置ADXL355加速度计子图
        self._setup_adxl_accel_plot(colors, labels)
        
        # 设置MPU6050陀螺仪子图
        self._setup_mpu_gyro_plot(colors, labels)
        
        # 设置重力矢量模长子图
        self._setup_gravity_plot()
        
        # 设置初始坐标轴范围
        self._set_initial_limits()
        
        plt.tight_layout()
        
        # 创建画布
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas.draw()
        
        return self.canvas
    
    def _setup_mpu_accel_plot(self, colors: List[str], labels: List[str]):
        """设置MPU6050加速度计子图"""
        self.ax1.set_title("MPU6050 Accelerometer (m/s²)", fontweight="bold", fontsize=12)
        self.ax1.set_ylabel("Acceleration", fontsize=11)
        self.ax1.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        self.ax1.set_facecolor("#ffffff")
        
        # 添加统计信息文本框
        self.ax1_stats_text = self.ax1.text(
            0.02, 0.98, "",
            transform=self.ax1.transAxes,
            fontsize=10,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )
        
        # 创建线条
        self.mpu_accel_lines = []
        for i in range(3):
            (line,) = self.ax1.plot(
                [], [], color=colors[i], label=labels[i], linewidth=1.5, alpha=0.8
            )
            self.mpu_accel_lines.append(line)
        self.ax1.legend(loc="upper right", fontsize=10)
    
    def _setup_adxl_accel_plot(self, colors: List[str], labels: List[str]):
        """设置ADXL355加速度计子图"""
        self.ax2.set_title("ADXL355 Accelerometer (m/s²)", fontweight="bold", fontsize=12)
        self.ax2.set_ylabel("Acceleration", fontsize=11)
        self.ax2.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        self.ax2.set_facecolor("#ffffff")
        
        self.ax2_stats_text = self.ax2.text(
            0.02, 0.98, "",
            transform=self.ax2.transAxes,
            fontsize=10,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )
        
        self.adxl_accel_lines = []
        for i in range(3):
            (line,) = self.ax2.plot(
                [], [], color=colors[i], label=labels[i], linewidth=1.5, alpha=0.8
            )
            self.adxl_accel_lines.append(line)
        self.ax2.legend(loc="upper right", fontsize=8)
    
    def _setup_mpu_gyro_plot(self, colors: List[str], labels: List[str]):
        """设置MPU6050陀螺仪子图"""
        self.ax3.set_title("MPU6050 Gyroscope (rad/s)", fontweight="bold", fontsize=12)
        self.ax3.set_ylabel("Angular Velocity", fontsize=11)
        self.ax3.set_xlabel("Time (s)", fontsize=11)
        self.ax3.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        self.ax3.set_facecolor("#ffffff")
        
        self.ax3_stats_text = self.ax3.text(
            0.02, 0.98, "",
            transform=self.ax3.transAxes,
            fontsize=10,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )
        
        self.mpu_gyro_lines = []
        for i in range(3):
            (line,) = self.ax3.plot(
                [], [], color=colors[i], label=labels[i], linewidth=1.5, alpha=0.8
            )
            self.mpu_gyro_lines.append(line)
        self.ax3.legend(loc="upper right", fontsize=8)
    
    def _setup_gravity_plot(self):
        """设置重力矢量模长子图"""
        self.ax4.set_title("Gravity Vector Magnitude (m/s²)", fontweight="bold", fontsize=11)
        self.ax4.set_ylabel("Magnitude", fontsize=10)
        self.ax4.set_xlabel("Sample", fontsize=10)
        self.ax4.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        self.ax4.set_facecolor("#ffffff")
        
        self.ax4_stats_text = self.ax4.text(
            0.02, 0.98, "",
            transform=self.ax4.transAxes,
            fontsize=10,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )
        
        (self.gravity_line,) = self.ax4.plot(
            [], [], color="#ff9900", label="Gravity", linewidth=2.0, alpha=0.8
        )
        self.ax4.legend(loc="upper right", fontsize=8)
    
    def _set_initial_limits(self):
        """设置初始坐标轴范围"""
        # X轴时间范围
        self.ax1.set_xlim(0, 10)
        self.ax2.set_xlim(0, 10)
        self.ax3.set_xlim(0, 10)
        self.ax4.set_xlim(0, 200)
        
        # Y轴范围
        self.ax1.set_ylim(-20, 20)
        self.ax2.set_ylim(-20, 20)
        self.ax3.set_ylim(-10, 10)
        self.ax4.set_ylim(0, 20)
    
    def init_blit(self):
        """初始化blit优化 - 缓存静态背景"""
        if not Config.ENABLE_BLIT_OPTIMIZATION or self._blit_initialized:
            return
        
        try:
            # 获取所有需要刷新的axes
            blit_axes = [ax for ax in [self.ax1, self.ax2, self.ax3, self.ax4] if ax is not None]
            
            # 获取所有需要刷新的artists
            self._blit_artists = []
            self._blit_artists.extend(self.mpu_accel_lines)
            self._blit_artists.extend(self.adxl_accel_lines)
            self._blit_artists.extend(self.mpu_gyro_lines)
            if self.gravity_line:
                self._blit_artists.append(self.gravity_line)
            if self.ax1_stats_text:
                self._blit_artists.append(self.ax1_stats_text)
            if self.ax2_stats_text:
                self._blit_artists.append(self.ax2_stats_text)
            if self.ax3_stats_text:
                self._blit_artists.append(self.ax3_stats_text)
            if self.ax4_stats_text:
                self._blit_artists.append(self.ax4_stats_text)
            
            # 缓存背景
            self._blit_backgrounds = {}
            for ax in blit_axes:
                ax.figure.canvas.draw()
                self._blit_backgrounds[ax] = ax.figure.canvas.copy_from_bbox(ax.bbox)
            
            self._blit_initialized = True
        except Exception:
            # blit初始化失败，回退到普通模式
            self._blit_initialized = False
    
    def update_charts(self, data_dict: Dict[str, Any]) -> bool:
        """
        更新图表 - 性能优化版本（支持blit）
        
        Args:
            data_dict: 包含以下键的数据字典
                - time: 时间数据列表
                - mpu_accel: [x, y, z] 三个列表的列表
                - adxl_accel: [x, y, z] 三个列表的列表
                - mpu_gyro: [x, y, z] 三个列表的列表
                - gravity: 重力矢量模长列表
        
        Returns:
            bool: 是否成功更新
        """
        # 频率控制
        current_time = time.time()
        if current_time - self.last_chart_update < self.chart_update_interval:
            return False
        self.last_chart_update = current_time
        
        # 检查数据
        time_data = data_dict.get('time', [])
        if not time_data or len(time_data) < 2:
            return False
        
        try:
            # 初始化blit（第一次调用时）
            if Config.ENABLE_BLIT_OPTIMIZATION and not self._blit_initialized:
                self.init_blit()
            
            # 获取当前时间
            time_val = time_data[-1] if time_data else 0
            
            # 设置X轴范围
            time_window = Config.CHART_TIME_WINDOW
            x_min = max(0, time_val - time_window)
            x_max = time_val
            
            # 数据降采样
            mpu_accel = data_dict.get('mpu_accel', [[], [], []])
            adxl_accel = data_dict.get('adxl_accel', [[], [], []])
            mpu_gyro = data_dict.get('mpu_gyro', [[], [], []])
            gravity = data_dict.get('gravity', [])
            
            if Config.ENABLE_DATA_DECIMATION and len(time_data) > Config.DISPLAY_DATA_POINTS * 2:
                decimation = Config.CHART_DECIMATION_FACTOR
                time_list = time_data[::decimation]
                mpu_accel_list = [d[::decimation] for d in mpu_accel]
                adxl_accel_list = [d[::decimation] for d in adxl_accel]
                mpu_gyro_list = [d[::decimation] for d in mpu_gyro]
            else:
                time_list = time_data
                mpu_accel_list = mpu_accel
                adxl_accel_list = adxl_accel
                mpu_gyro_list = mpu_gyro
            
            # 更新MPU6050加速度计图表
            for i in range(3):
                if len(mpu_accel_list[i]) == len(time_list) and i < len(self.mpu_accel_lines):
                    self.mpu_accel_lines[i].set_data(time_list, mpu_accel_list[i])
            
            # 更新ADXL355加速度计图表
            for i in range(3):
                if len(adxl_accel_list[i]) == len(time_list) and i < len(self.adxl_accel_lines):
                    self.adxl_accel_lines[i].set_data(time_list, adxl_accel_list[i])
            
            # 更新MPU6050陀螺仪图表
            for i in range(3):
                if len(mpu_gyro_list[i]) == len(time_list) and i < len(self.mpu_gyro_lines):
                    self.mpu_gyro_lines[i].set_data(time_list, mpu_gyro_list[i])
            
            # 更新重力矢量模长图表
            if gravity and len(gravity) == len(time_data):
                display_points = min(len(time_list), Config.DISPLAY_DATA_POINTS)
                start_idx = max(0, len(time_list) - display_points)
                sample_numbers = list(range(display_points))
                
                if Config.ENABLE_DATA_DECIMATION and len(gravity) > Config.DISPLAY_DATA_POINTS * 2:
                    gravity_display = gravity[::Config.CHART_DECIMATION_FACTOR][start_idx:]
                else:
                    gravity_display = gravity[start_idx:]
                
                if len(gravity_display) == len(sample_numbers):
                    self.gravity_line.set_data(sample_numbers, gravity_display)
                    self.ax4.set_xlim(0, display_points)
            
            # 更新X轴范围
            self.ax1.set_xlim(x_min, x_max)
            self.ax2.set_xlim(x_min, x_max)
            self.ax3.set_xlim(x_min, x_max)
            
            # 动态调整Y轴范围（带频率控制）
            if current_time - self.last_y_limit_update >= self.y_limit_update_interval:
                self.adjust_y_limits(data_dict)
                self.last_y_limit_update = current_time
            
            # 使用blit或普通绘制
            if Config.ENABLE_BLIT_OPTIMIZATION and self._blit_initialized:
                self._update_with_blit()
            else:
                self.canvas.draw_idle()
            
            return True
            
        except Exception:
            # 忽略绘图错误
            return False
    
    def _update_with_blit(self):
        """使用blit技术高效更新图表"""
        try:
            # 恢复背景
            for ax, bg in self._blit_backgrounds.items():
                self.canvas.restore_region(bg)
            
            # 重绘变化的artists
            for artist in self._blit_artists:
                if hasattr(artist, 'axes') and artist.axes:
                    artist.axes.draw_artist(artist)
            
            # 更新显示
            self.canvas.blit(self.fig.bbox)
            self.canvas.flush_events()
        except Exception:
            # blit失败，回退到普通绘制
            self.canvas.draw_idle()
    
    def update_statistics_text(self, stats_dict: Dict[str, Any]):
        """
        更新图表中的统计信息文本
        
        Args:
            stats_dict: 包含统计信息的字典
                - mpu_accel_mean: [x, y, z]
                - mpu_accel_std: [x, y, z]
                - adxl_accel_mean: [x, y, z]
                - adxl_accel_std: [x, y, z]
                - mpu_gyro_mean: [x, y, z]
                - mpu_gyro_std: [x, y, z]
                - gravity_mean: float
                - gravity_std: float
        """
        window_size = stats_dict.get('window_size', Config.STATS_WINDOW_SIZE)
        
        # MPU6050加速度计统计文本
        stats_text1 = f"Recent Stats (last {window_size} samples):\n"
        mpu_accel_mean = stats_dict.get('mpu_accel_mean', [0, 0, 0])
        mpu_accel_std = stats_dict.get('mpu_accel_std', [0, 0, 0])
        for i, axis in enumerate(["X", "Y", "Z"]):
            stats_text1 += f"{axis}: μ={mpu_accel_mean[i]:6.3f} σ={mpu_accel_std[i]:6.3f}\n"
        self.ax1_stats_text.set_text(stats_text1)
        
        # ADXL355加速度计统计文本
        stats_text2 = f"Recent Stats (last {window_size} samples):\n"
        adxl_accel_mean = stats_dict.get('adxl_accel_mean', [0, 0, 0])
        adxl_accel_std = stats_dict.get('adxl_accel_std', [0, 0, 0])
        for i, axis in enumerate(["X", "Y", "Z"]):
            stats_text2 += f"{axis}: μ={adxl_accel_mean[i]:6.3f} σ={adxl_accel_std[i]:6.3f}\n"
        self.ax2_stats_text.set_text(stats_text2)
        
        # MPU6050陀螺仪统计文本
        stats_text3 = f"Recent Stats (last {window_size} samples):\n"
        mpu_gyro_mean = stats_dict.get('mpu_gyro_mean', [0, 0, 0])
        mpu_gyro_std = stats_dict.get('mpu_gyro_std', [0, 0, 0])
        for i, axis in enumerate(["X", "Y", "Z"]):
            stats_text3 += f"{axis}: μ={mpu_gyro_mean[i]:6.3f} σ={mpu_gyro_std[i]:6.3f}\n"
        self.ax3_stats_text.set_text(stats_text3)
        
        # 重力矢量统计文本
        stats_text4 = f"Recent Stats (last {window_size} samples):\n"
        gravity_mean = stats_dict.get('gravity_mean', 0)
        gravity_std = stats_dict.get('gravity_std', 0)
        stats_text4 += f"Mean: {gravity_mean:6.3f}\n"
        stats_text4 += f"Std: {gravity_std:6.3f}"
        self.ax4_stats_text.set_text(stats_text4)
    
    def adjust_y_limits(self, data_dict: Dict[str, Any]):
        """
        调整Y轴范围 - 使用numpy向量化计算
        
        Args:
            data_dict: 包含传感器数据的字典
        """
        # MPU6050加速度计
        mpu_accel = data_dict.get('mpu_accel', [[], [], []])
        if mpu_accel[0] and len(mpu_accel[0]) > 0:
            recent_points = min(Config.DISPLAY_DATA_POINTS, len(mpu_accel[0]))
            
            recent_data = []
            for i in range(3):
                if len(mpu_accel[i]) >= recent_points:
                    recent_data.extend(mpu_accel[i][-recent_points:])
            
            if recent_data:
                y_min = float(np.min(recent_data)) - Config.CHART_Y_PADDING
                y_max = float(np.max(recent_data)) + Config.CHART_Y_PADDING
                
                if abs(y_max - y_min) < Config.CHART_MIN_Y_RANGE:
                    y_min = -10
                    y_max = 10
                
                self.ax1.set_ylim(y_min, y_max)
        
        # ADXL355加速度计
        adxl_accel = data_dict.get('adxl_accel', [[], [], []])
        if adxl_accel[0] and len(adxl_accel[0]) > 0:
            recent_points = min(Config.DISPLAY_DATA_POINTS, len(adxl_accel[0]))
            
            recent_data = []
            for i in range(3):
                if len(adxl_accel[i]) >= recent_points:
                    recent_data.extend(adxl_accel[i][-recent_points:])
            
            if recent_data:
                y_min = float(np.min(recent_data)) - Config.CHART_Y_PADDING
                y_max = float(np.max(recent_data)) + Config.CHART_Y_PADDING
                
                if abs(y_max - y_min) < 1:
                    y_min = -10
                    y_max = 10
                
                self.ax2.set_ylim(y_min, y_max)
        
        # MPU6050陀螺仪
        mpu_gyro = data_dict.get('mpu_gyro', [[], [], []])
        if mpu_gyro[0] and len(mpu_gyro[0]) > 0:
            recent_points = min(Config.DISPLAY_DATA_POINTS, len(mpu_gyro[0]))
            
            recent_data = []
            for i in range(3):
                if len(mpu_gyro[i]) >= recent_points:
                    recent_data.extend(mpu_gyro[i][-recent_points:])
            
            if recent_data:
                y_min = float(np.min(recent_data)) - Config.CHART_MIN_Y_RANGE / 2
                y_max = float(np.max(recent_data)) + Config.CHART_MIN_Y_RANGE / 2
                
                if abs(y_max - y_min) < Config.CHART_MIN_Y_RANGE / 2:
                    y_min = -5
                    y_max = 5
                
                self.ax3.set_ylim(y_min, y_max)
        
        # 重力矢量模长
        gravity = data_dict.get('gravity', [])
        if gravity and len(gravity) > 0:
            recent_points = min(Config.DISPLAY_DATA_POINTS, len(gravity))
            recent_data = gravity[-recent_points:]
            
            if recent_data:
                y_min = max(0, float(np.min(recent_data)) - Config.CHART_Y_PADDING)
                y_max = float(np.max(recent_data)) + Config.CHART_Y_PADDING
                
                if abs(y_max - y_min) < 1:
                    y_min = 0
                    y_max = 20
                
                self.ax4.set_ylim(y_min, y_max)
    
    def clear_data(self):
        """清空图表数据"""
        # 清空所有线条数据
        for line in self.mpu_accel_lines:
            line.set_data([], [])
        for line in self.adxl_accel_lines:
            line.set_data([], [])
        for line in self.mpu_gyro_lines:
            line.set_data([], [])
        if self.gravity_line:
            self.gravity_line.set_data([], [])
        
        # 重绘
        if self.canvas:
            self.canvas.draw_idle()
    
    def get_canvas(self) -> Optional[FigureCanvasTkAgg]:
        """获取matplotlib画布"""
        return self.canvas
    
    def close(self):
        """清理资源"""
        if self.fig:
            plt.close(self.fig)
            self.fig = None
        self.canvas = None
