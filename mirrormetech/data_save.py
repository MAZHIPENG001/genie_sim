# Copyright (c) 2023-2026, AgiBot Inc. All Rights Reserved.
# Author: Genie Sim Team
# License: Mozilla Public License Version 2.0

import sys
import os
import rclpy
from device.rosbag_data_save import RosbagRecorder
from device.keyboard import KeystrokeCounter, KeyCode, Key

if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # 初始化 ROS 2
    rclpy.init()

    # 实例化录制器
    recorder = RosbagRecorder()
    stop = False

    with KeystrokeCounter() as key_counter:
        while not stop:
            # 按键判断
            press_events = key_counter.get_press_events()
            # Q: 退出程序
            # C: 开始录制
            # S: 保存当前数据
            # num: order
            # Backspace: 删除最近录制的episode
            for key_stroke in press_events:
                if key_stroke == KeyCode(char='q'):
                    stop = True
                elif key_stroke == KeyCode(char='c'):
                    recorder.start_recording()
                elif key_stroke == KeyCode(char='s'):
                    recorder.stop_recording()
