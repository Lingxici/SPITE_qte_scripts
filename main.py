import cv2
import numpy as np
import mss
import time
from pynput.keyboard import Controller, Key

keyboard = Controller()

BAR = {"top": 1060, "left": 120, "width": 2320, "height": 70}
GREEN_LO = np.array([25, 90, 95])
GREEN_HI = np.array([45, 255, 255])
WHITE_LO = np.array([0, 0, 200])
WHITE_HI = np.array([180, 30, 255])

PIXELS_PER_FRAME = 31
cooldown = 0.3
last_trigger_time = 0

# 绿色宽度限制
MIN_GREEN_WIDTH = 50
MAX_GREEN_WIDTH = 500

time.sleep(5)

with mss.MSS() as sct:
    while True:
        current_time = time.time()

        shot = np.array(sct.grab(BAR))
        bgr = cv2.cvtColor(shot, cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        # 识别绿色区间
        green_mask = cv2.inRange(hsv, GREEN_LO, GREEN_HI)
        green_cols = np.where(np.sum(green_mask, axis=0) > 0)[0]
        if len(green_cols) < 5: continue
        g_left = BAR["left"] + green_cols[0]
        g_right = BAR["left"] + green_cols[-1]
        green_width = g_right - g_left

        # 过滤异常绿色宽度
        if green_width < MIN_GREEN_WIDTH or green_width > MAX_GREEN_WIDTH:
            continue

        # 识别白色竖线
        white_mask = cv2.inRange(hsv, WHITE_LO, WHITE_HI)
        white_cols = np.where(np.sum(white_mask, axis=0) > 50)[0]
        if len(white_cols) == 0: continue
        w_x = BAR["left"] + white_cols[0]

        # 计算竖线到绿色边界的距离
        dist_to_green = 0
        if w_x < g_left:
            dist_to_green = g_left - w_x
        elif w_x > g_right:
            dist_to_green = w_x - g_right
        else:
            continue  # 已在绿色内，跳过

        # 计算还需要多少帧到达绿色边界
        frames_needed = dist_to_green / PIXELS_PER_FRAME

        # 根据绿色宽度动态调整延迟帧数
        if green_width >= 200:
            delay_frames = 2.0
        elif green_width >= 100:
            delay_frames = 1.7
        else:
            delay_frames = 1.5

        # 触发条件：还需要的帧数 <= 动态延迟
        should_trigger = False
        if 0 < frames_needed <= delay_frames:
            should_trigger = True

        if should_trigger and current_time - last_trigger_time > cooldown:
            print(f"\n触发！")
            print(f"   绿色宽度: {green_width}px")
            print(f"   竖线: {w_x} | 绿色: [{g_left}, {g_right}]")
            print(f"   距离边界: {dist_to_green}px")
            print(f"   还需{frames_needed:.2f}帧 | 动态延迟: {delay_frames}帧")

            keyboard.press(Key.space)
            time.sleep(0.05)
            keyboard.release(Key.space)

            last_trigger_time = current_time
            print(f"⌨️ 已按空格")

        # 显示实时信息
        status = f"绿宽:{green_width}px | 竖线:{w_x} | 距绿:{dist_to_green}px | 需{frames_needed:.1f}帧 | 延迟:{delay_frames}f"
        print(f"\r{status}", end="", flush=True)

        time.sleep(0.016)
        