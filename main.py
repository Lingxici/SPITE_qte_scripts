import cv2
import numpy as np
import mss
import time
from pynput.keyboard import Controller, Key

keyboard = Controller()

# 2k 分辨率下，判定槽大概位置
BAR = {"top": 1060, "left": 120, "width": 2320, "height": 70}
# 绿色判定区块
GREEN_LO = np.array([25, 90, 95])
GREEN_HI = np.array([45, 255, 255])
# 白色判定线
WHITE_LO = np.array([0, 0, 200])
WHITE_HI = np.array([180, 30, 255])

# 提前量（像素）- 分辨率不同需自行修改
LEAD_PIXELS = 62  # 提前2帧（31像素/帧 × 2帧）

last_trigger_time = 0
cooldown = 0.5  # 0.5秒冷却

print("于 5s 内切换至游戏内 QTE 游戏界面")
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
        g_center = (g_left + g_right) // 2

        # 识别白色竖线
        white_mask = cv2.inRange(hsv, WHITE_LO, WHITE_HI)
        white_cols = np.where(np.sum(white_mask, axis=0) > 50)[0]
        if len(white_cols) == 0: continue
        w_x = BAR["left"] + white_cols[0]

        # 计算竖线到绿色中心的距离
        distance_to_center = abs(w_x - g_center)

        # 触发条件：竖线距离绿色中心小于阈值
        trigger_distance = LEAD_PIXELS

        if distance_to_center <= trigger_distance:
            if current_time - last_trigger_time > cooldown:
                print(f"\n🎯 触发！竖线: {w_x}, 绿色中心: {g_center}")
                print(f"   距离: {distance_to_center}像素")

                keyboard.press(Key.space)
                time.sleep(0.05)
                keyboard.release(Key.space)

                last_trigger_time = current_time
                print(f"⌨️ 已按空格，冷却{cooldown}秒")

        # 显示实时信息
        status = f"竖线: {w_x} | 绿色: [{g_left}, {g_right}] | 距离: {distance_to_center}"
        print(f"\r{status}", end="", flush=True)

        # 判定后的动画时间
        time.sleep(0.016)
