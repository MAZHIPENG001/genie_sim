# Copyright (c) 2023-2026, AgiBot Inc. All Rights Reserved.
# Author: Genie Sim Team
# License: Mozilla Public License Version 2.0

import os
import sys
import time
import signal
import subprocess
import threading
import math
import numpy as np

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, JointState

# 模拟数据生成节点
class MockRobotGenerator(Node):
    def __init__(self):
        super().__init__('mock_robot_generator')
        self.pub_head = self.create_publisher(Image, "/genie_sim/head_front_camera_rgb", 10)
        self.pub_left = self.create_publisher(Image, "/genie_sim/left_camera_rgb", 10)
        self.pub_right = self.create_publisher(Image, "/genie_sim/right_camera_rgb", 10)
        self.pub_joints = self.create_publisher(JointState, '/joint_states', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)  # 10Hz

    def generate_random_image(self):
        msg = Image()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.height = 224
        msg.width = 224
        msg.encoding = 'rgb8'
        msg.step = 224 * 3
        img_data = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        msg.data = img_data.tobytes()
        return msg

    def timer_callback(self):
        self.pub_head.publish(self.generate_random_image())
        self.pub_left.publish(self.generate_random_image())
        self.pub_right.publish(self.generate_random_image())

        joint_msg = JointState()
        joint_msg.header.stamp = self.get_clock().now().to_msg()
        joint_msg.name = [f'joint_{i + 1}' for i in range(7)]
        joint_msg.position = np.random.uniform(-math.pi, math.pi, 7).tolist()
        self.pub_joints.publish(joint_msg)

# Rosbag 录制管理类
class RosbagRecorder:
    def __init__(self, folder_name="dataset"):
        current_dir = os.path.dirname(os.path.abspath(__file__))

        self.base_path = os.path.abspath(os.path.join(current_dir, "..", folder_name))

        self.process = None
        print(f"数据存放根目录设为: {self.base_path}")

    def _get_next_folder_path(self):
        """内部函数：自动计算下一个次序命名的文件夹路径"""
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

        # 扫描已有文件夹
        existing_dirs = [d for d in os.listdir(self.base_path) if os.path.isdir(os.path.join(self.base_path, d))]
        seq_nums = []
        for d in existing_dirs:
            try:
                seq_nums.append(int(d))
            except ValueError:
                pass

        next_seq = max(seq_nums) + 1 if seq_nums else 1
        return os.path.join(self.base_path, f"{next_seq:03d}")

    def start_recording(self):
        """手动调用：开始录制"""
        if self.process is not None:
            print("[警告] 录制已在运行中，请勿重复启动。")
            return

        bag_path = self._get_next_folder_path()
        topics = [
            "/genie_sim/head_front_camera_rgb",
            "/genie_sim/left_camera_rgb",
            "/genie_sim/right_camera_rgb",
            "/joint_states",
            "/joint_states_ee"
        ]

        # 拼接 ros2 bag 命令行指令
        cmd = ["ros2", "bag", "record"] + topics + ["-o", bag_path]

        print(f"\n>>> [开始录制] 数据将保存至: {bag_path}")

        # 使用 preexec_fn=os.setsid 创建新进程组，方便后面完整关闭其子进程
        # stdout/stderr 设置为 DEVNULL 可以让终端保持干净，不被 rosbag 的日志刷屏
        self.process = subprocess.Popen(
            cmd,
            preexec_fn=os.setsid,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def stop_recording(self):
        """手动调用：停止录制"""
        if self.process is None:
            print("[警告] 当前没有正在运行的录制任务。")
            return

        print(">>> [停止录制] 正在安全关闭 Rosbag 进程...")
        try:
            # 向整个进程组发送 SIGINT (等同于 Ctrl+C)，触发 rosbag 安全退出机制
            os.killpg(os.getpgid(self.process.pid), signal.SIGINT)
            self.process.wait(timeout=5)  # 等待文件写入完成
        except subprocess.TimeoutExpired:
            print("[错误] Rosbag 未能及时停止，强制结束。")
            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
        finally:
            self.process = None
            print(">>> 录制已停止，数据已成功保存。")

# 演示如何手动调用
def ros2_spin_thread(node):
    """后台线程：负责运行 ROS 2 节点提供数据"""
    try:
        rclpy.spin(node)
    except Exception:
        pass


if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from keyboard import KeystrokeCounter, KeyCode, Key
    # 初始化 ROS 2
    rclpy.init()
    mock_node = MockRobotGenerator()

    # 启动后台线程运行 ROS 2 节点（持续产生随机图像和关节数据）
    spin_thread = threading.Thread(target=ros2_spin_thread, args=(mock_node,), daemon=True)
    spin_thread.start()
    print("后台模拟机器人数据节点已启动（10Hz）...")

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
