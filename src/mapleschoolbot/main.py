from enum import Enum
import time
from time import sleep
import os
import logging

from PIL import ImageGrab
import cv2
import numpy as np
import keyboard


class Direction(Enum):
    LEFT = 1
    RIGHT = 2

class MapleSchoolBot:
    def __init__(self, debug=False):
        self.running = False
        self.current_direction = Direction.RIGHT
        
        # 操作按键设置
        self.left_key = 'left'
        self.right_key = 'right'
        
        # 屏幕截取间隔
        self.flash_interval = 0.25

        # 是否开启调试模式
        self.debug = debug

        # 加载模板
        self.character_template = self.load_character_template('character')
        self.left_boundary_image = self.load_left_boundary_image()
        self.right_boundary_image = self.load_right_boundary_image()
        
        # 更新初始坐标
        self.screenshot = None
        self.screen_no = 0
        self.character_pos = None
        self.left_boundary_pos = None
        self.right_boundary_pos = None
        self.last_screenshot_time = None
        self.update_positions()

    
    def load_character_template(self, character):
        # 加载角色模板
        character_template = cv2.imread(f'./src/mapleschoolbot/resources/{character}.png')
        return character_template

    def load_left_boundary_image(self):
        # 加载左边界图像
        left_boundary_image = cv2.imread('./src/mapleschoolbot/resources/left_boundary.png')
        return left_boundary_image

    def load_right_boundary_image(self):
        # 加载右边界图像
        right_boundary_image = cv2.imread('./src/mapleschoolbot/resources/right_boundary.png')
        return right_boundary_image

    def find_position(self, screenshot, template, confidence_threshold):
        # 进行模板匹配, 在截图中寻找角色
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val > confidence_threshold:
            return True, max_loc, max_val
        return False, None, 0

    def capture_screenshot(self):
        # 截取屏幕
        screenshot = ImageGrab.grab()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        return screenshot

    def update_positions(self):
        self.screenshot = self.capture_screenshot()
        self.screen_no += 1
        self.last_screenshot_time = time.time()

        # 更新
        # 更新角色位置
        found_char, char_pos, _ = self.find_position(self.screenshot, self.character_template, 0.8)
        if found_char:
            self.character_pos = char_pos
        else:
            self.character_pos = None

        # 更新左边界位置
        found_left_boundary, left_boundary_pos, _ = self.find_position(self.screenshot, self.left_boundary_image, 0.8)
        if found_left_boundary:
            self.left_boundary_pos = left_boundary_pos
        else:
            self.left_boundary_pos = None

        # 更新右边界位置
        found_right_boundary, right_boundary_pos, _ = self.find_position(self.screenshot, self.right_boundary_image, 0.8)
        if found_right_boundary:
            self.right_boundary_pos = right_boundary_pos
        else:
            self.right_boundary_pos = None

        if self.debug:
            self.draw_position(self.screenshot, self.character_template, 0.8)
            self.draw_position(self.screenshot, self.left_boundary_image, 0.8)
            self.draw_position(self.screenshot, self.right_boundary_image, 0.8)
            # 保存结果图片
            
            # 确保debug文件夹存在
            if not os.path.exists('./debug'):
                os.makedirs('./debug')
            cv2.imwrite(f'./debug/screenshot_{self.screen_no}.png', self.screenshot)
            cv2.imwrite(f'./debug/character_{self.screen_no}.png', self.character_template)
            cv2.imwrite(f'./debug/left_boundary_{self.screen_no}.png', self.left_boundary_image)
            cv2.imwrite(f'./debug/right_boundary_{self.screen_no}.png', self.right_boundary_image) 

    def change_direction(self):
        # 改变方向
        if self.current_direction == Direction.RIGHT:
            self.current_direction = Direction.LEFT
            keyboard.release(self.right_key)
            keyboard.press(self.left_key)
        else:
            self.current_direction = Direction.RIGHT
            keyboard.release(self.left_key)
            keyboard.press(self.right_key)

    def check_meeting_boundary(self):
        if self.character_pos is not None:
            if self.current_direction == Direction.RIGHT:
                # 向右走时检测右边界，检测中心坐标
                if self.right_boundary_pos is not None and self.character_pos[0] > self.right_boundary_pos[0]:
                    # 角色超过右边界，改变方向
                    self.change_direction()
                    logging.info("角色超过右边界，改变方向")
            else:
                # 向左走时检测左边界
                if self.left_boundary_pos is not None and self.character_pos[0] < self.left_boundary_pos[0]:
                    # 角色超过左边界，改变方向
                    self.change_direction()
                    logging.info("角色超过左边界，改变方向")

    def run(self):
        # 启动程序
        self.running = True
        # 开始向右移动
        self.right_move()
        while self.running:
            # 截取屏幕
            if time.time() - self.last_screenshot_time >= self.flash_interval:
                self.update_positions()
                
            # 执行移动
            self.check_meeting_boundary()
            # 防止CPU占用过高
            time.sleep(0.01)

            # 按F12退出程序
            if keyboard.is_pressed('f12'):
                self.stop()
                break

    def stop(self):
        # 停止程序
        self.running = False
        if self.current_direction == Direction.RIGHT:
            keyboard.release(self.right_key)
        else:
            keyboard.release(self.left_key)

    def right_move(self):
        # 向右移动
        keyboard.release(self.left_key)
        keyboard.press(self.right_key)

    def draw_position(self, screenshot, character_template, confidence_threshold):
        # 进行模板匹配, 在截图中寻找角色，并在截图中绘制矩形框
        result = cv2.matchTemplate(screenshot, character_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val > confidence_threshold:
            # 获取模板的宽度和高度
            template_h, template_w = character_template.shape[:2]
            
            # 在找到的位置绘制矩形框
            top_left = max_loc
            bottom_right = (top_left[0] + template_w, top_left[1] + template_h)
            cv2.rectangle(screenshot, top_left, bottom_right, (0, 255, 0), 2)
            
            # 准备要显示的文本
            text = f"Pos: ({top_left[0]}, {top_left[1]}) Size: {template_w}x{template_h}"
            conf_text = f"Conf: {max_val:.2f}"
            
            # 设置文本参数
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.3
            font_thickness = 1
            text_color = (0, 255, 0)  # 绿色
            
            # 计算文本位置（在矩形框下方）
            text_pos = (top_left[0], bottom_right[1] + 20)
            conf_pos = (top_left[0], bottom_right[1] + 40)
            
            # 绘制文本
            cv2.putText(screenshot, text, text_pos, font, font_scale, text_color, font_thickness)
            cv2.putText(screenshot, conf_text, conf_pos, font, font_scale, text_color, font_thickness)
            


    def draw_positions(self, screenshot, template, confidence_threshold):
        # 进行模板匹配, 在截图中寻找角色，并在截图中绘制矩形框
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= confidence_threshold)

        # 遍历所有匹配结果
        for pt in zip(*loc[::-1]):
            # 获取模板的宽度和高度
            template_h, template_w = template.shape[:2]

            # 在找到的位置绘制矩形框
            top_left = pt
            bottom_right = (top_left[0] + template_w, top_left[1] + template_h)
            cv2.rectangle(screenshot, top_left, bottom_right, (0, 255, 0), 2)

            # 准备要显示的文本
            max_val = result[pt[1]][pt[0]]
            text = f"Pos: ({top_left[0]}, {top_left[1]}) Size: {template_w}x{template_h}"
            conf_text = f"Conf: {max_val:.2f}"

            # 设置文本参数
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.3
            font_thickness = 1
            text_color = (0, 255, 0)  # 绿色

            # 计算文本位置（在矩形框下方）
            text_pos = (top_left[0], bottom_right[1] + 20)
            conf_pos = (top_left[0], bottom_right[1] + 40)

            # 绘制文本
            cv2.putText(screenshot, text, text_pos, font, font_scale, text_color, font_thickness)
            cv2.putText(screenshot, conf_text, conf_pos, font, font_scale, text_color, font_thickness)

        # 保存结果图片
        cv2.imwrite('output.png', screenshot)

        if loc[0].size > 0:
            return True, loc
        else:
            return False, None

if __name__ == "__main__":
    # 开始程序，请在10秒内切换到游戏窗口，按F12退出程序
    print("请在10秒内切换到游戏窗口，按F12退出程序")
    time.sleep(10)

    bot = MapleSchoolBot(debug=True)
    bot.run()