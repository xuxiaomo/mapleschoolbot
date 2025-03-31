import random
import time
import keyboard
import cv2
import numpy as np
import pyautogui
from PIL import Image
from typing import Tuple, Optional, List, Dict
import os

class MapleAutoFarm:
    def __init__(self):
        self.moving_right = True
        self.running = True
        self.last_position_update = time.time()  # 添加位置更新时间记录
        
        # 获取当前文件所在目录
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.character_template_path = os.path.join(self.current_dir, 'assets', 'character_template.png')
        self.monster_templates_dir = os.path.join(self.current_dir, 'assets', 'monsters')
        
        # 确保目录存在
        os.makedirs(self.monster_templates_dir, exist_ok=True)
        
        # 加载角色模板
        self.character_template = cv2.imread(self.character_template_path)
        if self.character_template is None:
            raise FileNotFoundError(f"无法加载角色模板图片: {self.character_template_path}")
        
        # 加载所有怪物模板
        self.monster_templates = self.load_monster_templates()
        if not self.monster_templates:
            print("警告：未找到怪物模板，请确保已添加怪物模板图片")
        
        # 初始化位置信息
        self.character_pos = None
        self.monster_positions = {}  # 使用字典存储不同类型怪物的位置
        
        # 图像识别参数
        self.template_threshold = 0.8  # 模板匹配阈值
        self.position_update_interval = 0.5  # 位置更新间隔（秒）

        self.update_positions()

    def load_monster_templates(self) -> Dict[str, np.ndarray]:
        """加载所有怪物模板"""
        templates = {}
        if os.path.exists(self.monster_templates_dir):
            for filename in os.listdir(self.monster_templates_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    template_path = os.path.join(self.monster_templates_dir, filename)
                    template = cv2.imread(template_path)
                    if template is not None:
                        monster_name = os.path.splitext(filename)[0]
                        templates[monster_name] = template
                        print(f"已加载怪物模板: {monster_name}")

        if not templates:
            raise ValueError("未加载怪物模板")
        else:
            return templates

    def capture_game_screen(self) -> np.ndarray:
        """捕获游戏窗口截图"""
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def find_character(self, frame: np.ndarray) -> Optional[Tuple[int, int]]:
        """识别角色位置"""
        result = cv2.matchTemplate(frame, self.character_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= self.template_threshold:
            x = max_loc[0] + self.character_template.shape[1] // 2
            y = max_loc[1] + self.character_template.shape[0] // 2
            return (x, y)
        else:
            if self.character_pos is None:
                from PIL import Image
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                Image.fromarray(frame).save('screenshot.png')
                character = cv2.cvtColor(self.character_template, cv2.COLOR_BGR2RGB)
                Image.fromarray(character).save('character.png')
                raise LookupError("未找到角色位置")
            else:
                return self.character_pos

    def filter_monsters_by_platform(self, character_pos: Tuple[int, int], monster_positions: Dict[str, List[Tuple[int, int]]], y_threshold: int = 120) -> Dict[str, List[Tuple[int, int]]]:
        """过滤掉不在同一平台的怪物
        
        Args:
            character_pos: 角色位置 (x, y)
            monster_positions: 怪物位置字典 {怪物名称: [(x, y), ...]}
            y_threshold: Y坐标允许的误差范围（像素）
            
        Returns:
            过滤后的怪物位置字典
        """
        if not character_pos:
            return {}
            
        char_y = character_pos[1]
        filtered_monsters = {}
        
        for monster_name, positions in monster_positions.items():
            # 只保留Y坐标在允许范围内的怪物
            same_platform_monsters = [
                (x, y) for x, y in positions 
                if abs(y - char_y) <= y_threshold
            ]
            
            if same_platform_monsters:
                filtered_monsters[monster_name] = same_platform_monsters
                
        return filtered_monsters

    def find_monsters(self, frame: np.ndarray) -> Dict[str, List[Tuple[int, int]]]:
        """识别所有类型怪物的位置"""
        all_monsters = {}
        for monster_name, template in self.monster_templates.items():
            result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= self.template_threshold)
            monster_positions = []
            
            for pt in zip(*locations[::-1]):
                x = pt[0] + template.shape[1] // 2
                y = pt[1] + template.shape[0] // 2
                monster_positions.append((x, y))
            
            if monster_positions:
                all_monsters[monster_name] = monster_positions
            else:
                from PIL import Image
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                Image.fromarray(frame).save('screenshot.png')
                monster = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
                Image.fromarray(monster).save(monster_name + '.png')

        print(all_monsters)
                
        # 过滤掉不在同一平台的怪物
        filtered_monsters = self.filter_monsters_by_platform(self.character_pos, all_monsters)
        
        if not filtered_monsters:
            print("警告：未找到与角色在同一平台的怪物")
            filtered_monsters = self.monster_positions
            
        return filtered_monsters

    def update_positions(self):
        """更新角色和怪物位置"""
        frame = self.capture_game_screen()
        
        # 更新角色位置
        self.character_pos = self.find_character(frame)
        if self.character_pos:
            print(f"角色位置: {self.character_pos}")
        
        # 更新所有类型怪物的位置
        self.monster_positions = self.find_monsters(frame)
        for monster_name, positions in self.monster_positions.items():
            print(f"发现 {len(positions)} 只 {monster_name}")

    def has_monsters_ahead(self) -> bool:
        """检查前方是否有任何类型的怪物"""
        char_x = self.character_pos[0]
        
        # 检查所有类型的怪物
        for monster_name, positions in self.monster_positions.items():
            for monster_x, monster_y in positions:
                if self.moving_right:
                    # 向右移动时，检查右侧的怪物
                    if monster_x > char_x:
                        print(f"前方发现 {monster_name}，距离：{monster_x - char_x}像素，坐标：({monster_x}, {monster_y})")
                        return True
                else:
                    # 向左移动时，检查左侧的怪物
                    if monster_x < char_x:
                        print(f"前方发现 {monster_name}，距离：{char_x - monster_x}像素，坐标：({monster_x}, {monster_y})")
                        return True
        
        print("前方没有怪物")
        return False

    def move_character(self):
        """控制角色移动"""
        # 定期更新位置信息
        current_time = time.time()
        if current_time - self.last_position_update >= self.position_update_interval:
            self.update_positions()
            self.last_position_update = current_time

        # 检查前方是否有怪物
        has_monsters = self.has_monsters_ahead()
        
        if not has_monsters:
            if self.moving_right:
                keyboard.release('right')
                keyboard.press('left') 
                print("切换方向：向左移动")
            else:
                keyboard.release('left')
                keyboard.press('right')
                print("切换方向：向右移动")

            # 如果前方没有怪物，改变方向
            self.moving_right = not self.moving_right

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
        print("移动模式：检测前方怪物，无怪物时改变方向")
        print(f"已加载 {len(self.monster_templates)} 种怪物模板")
        
        # 设置计时器
        last_pickup_time = time.time()
        last_skill_time = time.time()

        while self.running:
            current_time = time.time()

            # 移动角色
            self.move_character()

            # 检查是否需要拾取物品
            if current_time - last_pickup_time > random.uniform(0.15, 0.25):
                self.pickup_items()
                last_pickup_time = current_time

            # 检查是否需要使用技能
            if current_time - last_skill_time > random.uniform(0.8, 1):
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
    print("请在10秒内切换到游戏窗口...")
    time.sleep(10)
    
    bot = MapleAutoFarm()
    bot.run() 