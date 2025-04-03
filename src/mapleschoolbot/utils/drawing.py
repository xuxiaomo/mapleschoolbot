import cv2
import numpy as np

def draw_position(screenshot, template, confidence_threshold):
    """在截图中绘制单个匹配位置的矩形框和信息"""
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val > confidence_threshold:
        # 获取模板的宽度和高度
        template_h, template_w = template.shape[:2]
        
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

def draw_positions(screenshot, template, confidence_threshold):
    """在截图中绘制所有匹配位置的矩形框和信息"""
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

    if loc[0].size > 0:
        return True, loc
    else:
        return False, None