import random
import time
import keyboard
import win32gui
import win32con
import cv2
import numpy as np
import pyautogui
from typing import Tuple, Optional
import os

class MapleAutoFarm:
    def __init__(self):
        self.moving_right = True
        self.running = True
        self.right_move_time = 15  # 向右移动时间（秒）
        self.left_move_time = 15   # 向左移动时间（秒）
        self.last_direction_change = time.time()
        self.last_jump_time = time.time()
        
        # 获取当前文件所在目录
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_path = os.path.join(self.current_dir, 'assets', 'character_template.png')
        
        # 加载角色模板
        self.character_template = cv2.imread(self.template_path)
        if self.character_template is None:
            raise FileNotFoundError(f"无法加载角色模板图片: {self.template_path}")
        
        # 初始化平台边界
        self.platform_left = None
        self.platform_right = None
        self.character_pos = None
        
        # 图像识别参数
        self.template_threshold = 0.8  # 模板匹配阈值
        self.platform_color_lower = np.array([0, 0, 0])  # 平台颜色范围下限
        self.platform_color_upper = np.array([180, 30, 30])  # 平台颜色范围上限

    def capture_game_screen(self) -> np.ndarray:
        """捕获游戏窗口截图"""
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def find_character(self, frame: np.ndarray) -> Optional[Tuple[int, int]]:
        """识别角色位置"""
        result = cv2.matchTemplate(frame, self.character_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= self.template_threshold:
            # 返回角色中心点坐标
            x = max_loc[0] + self.character_template.shape[1] // 2
            y = max_loc[1] + self.character_template.shape[0] // 2
            return (x, y)
        return None

    def find_platform_boundaries(self, frame: np.ndarray) -> Tuple[Optional[int], Optional[int]]:
        """识别平台左右边界"""
        # 转换为HSV颜色空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 创建平台颜色掩码
        mask = cv2.inRange(hsv, self.platform_color_lower, self.platform_color_upper)
        
        # 获取角色位置附近的水平线
        if self.character_pos:
            y = self.character_pos[1] + 50  # 在角色下方50像素处检测平台
            line = mask[y:y+1, :]
            
            # 找到非零点的左右边界
            non_zero = np.nonzero(line)[1]
            if len(non_zero) > 0:
                left = non_zero[0]
                right = non_zero[-1]
                return left, right
        
        return None, None

    def update_positions(self):
        """更新角色位置和平台边界"""
        frame = self.capture_game_screen()
        
        # 更新角色位置
        self.character_pos = self.find_character(frame)
        if self.character_pos:
            print(f"角色位置: {self.character_pos}")
        
        # 更新平台边界
        left, right = self.find_platform_boundaries(frame)
        if left is not None and right is not None:
            self.platform_left = left
            self.platform_right = right
            print(f"平台边界: 左={left}, 右={right}")

    def move_character(self):
        """控制角色移动"""
        # 定期更新位置信息
        if random.random() < 0.1:  # 10%的概率更新位置
            self.update_positions()
        
        current_time = time.time()
        time_since_last_change = current_time - self.last_direction_change

        # 如果已经识别到平台边界，使用边界来控制移动
        if self.platform_left is not None and self.platform_right is not None and self.character_pos is not None:
            if self.moving_right:
                if self.character_pos[0] >= self.platform_right:
                    self.moving_right = False
                    keyboard.release('right')
                    keyboard.press('left')
                    self.last_direction_change = current_time
                    print("切换方向：向左移动")
                else:
                    keyboard.release('left')
                    keyboard.press('right')
            else:
                if self.character_pos[0] <= self.platform_left:
                    self.moving_right = True
                    keyboard.release('left')
                    keyboard.press('right')
                    self.last_direction_change = current_time
                    print("切换方向：向右移动")
                else:
                    keyboard.release('right')
                    keyboard.press('left')
        else:
            # 如果还没有识别到边界，使用时间控制移动
            if self.moving_right:
                if time_since_last_change >= self.right_move_time:
                    self.moving_right = False
                    keyboard.release('right')
                    keyboard.press('left')
                    self.last_direction_change = current_time
                    print("切换方向：向左移动")
                else:
                    keyboard.release('left')
                    keyboard.press('right')
            else:
                if time_since_last_change >= self.left_move_time:
                    self.moving_right = True
                    keyboard.release('left')
                    keyboard.press('right')
                    self.last_direction_change = current_time
                    print("切换方向：向右移动")
                else:
                    keyboard.release('right')
                    keyboard.press('left')

    def pickup_items(self):
        """拾取物品"""
        keyboard.press('z')
        time.sleep(0.05)
        keyboard.release('z')

    def use_skill(self):
        """使用技能"""
        keyboard.press('e')
        time.sleep(0.05)
        keyboard.release('e')

    def run(self):
        print("脚本启动中... 按 'F12' 停止脚本")
        print(f"移动模式：向右 {self.right_move_time}秒，向左 {self.left_move_time}秒")
        
        # 设置计时器
        last_pickup_time = time.time()
        last_skill_time = time.time()

        while self.running:
            current_time = time.time()

            # 移动角色
            self.move_character()

            # 检查是否需要拾取物品
            if current_time - last_pickup_time > random.uniform(0.25, 0.35):
                self.pickup_items()
                last_pickup_time = current_time

            # 检查是否需要使用技能
            if current_time - last_skill_time > random.uniform(0.4, 0.6):
                self.use_skill()
                last_skill_time = current_time

            # 检查停止热键
            if keyboard.is_pressed('F12'):
                self.running = False
                keyboard.release('left')
                keyboard.release('right')
                print("脚本已停止")

            time.sleep(0.01)  # 防止CPU占用过高

if __name__ == "__main__":
    # 等待3秒后启动，留时间切换到游戏窗口
    print("请在3秒内切换到游戏窗口...")
    time.sleep(3)
    
    bot = MapleAutoFarm()
    bot.run() 