# Copyright (c) 2023-2026, AgiBot Inc. All Rights Reserved.
# Author: Genie Sim Team
# License: Mozilla Public License Version 2.0

# import sys
# import rclpy
# from rclpy.serialization import deserialize_message
# from rosidl_runtime_py.utilities import get_message
# import rosbag2_py
# import cv2
# import numpy as np
# import os

# def read_and_display_all(bag_path):
#     # 1. 配置 Reader
#     reader = rosbag2_py.SequentialReader()
#     storage_options = rosbag2_py.StorageOptions(uri=bag_path, storage_id='mcap')
#     converter_options = rosbag2_py.ConverterOptions('', '')
#     reader.open(storage_options, converter_options)

#     # 获取 topic 信息，构建反序列化字典
#     topic_types = reader.get_all_topics_and_types()
#     type_map = {topic.name: get_message(topic.type) for topic in topic_types}

#     print(f"==========================================")
#     print(f" 开始读取 Bag: {bag_path}")
#     print(f" 包含的 Topics: {list(type_map.keys())}")
#     print(f" 按 OpenCV 窗口中的 'q' 键退出。")
#     print(f"==========================================\n")

#     frame_count = 0

#     # 2. 遍历 Bag 中的所有消息
#     while reader.has_next():
#         (topic, data, t) = reader.read_next()
#         msg_type = type_map[topic]
#         msg = deserialize_message(data, msg_type)

#         # ---------------------------------------------------------
#         # 处理并显示图像数据
#         # ---------------------------------------------------------
#         if topic in ['/genie_sim/head_front_camera_rgb', '/genie_sim/left_camera_rgb', '/genie_sim/right_camera_rgb']:
#             channels = len(msg.data) // (msg.height * msg.width)
#             # 还原 numpy 数组
#             img_np = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width, channels))
#             # RGB 转 BGR 以适应 OpenCV 默认色彩空间
#             if channels == 4:
#                 # 4通道通常为 RGBA，转为 OpenCV 的 BGR
#                 img_cv2 = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
#             elif channels == 3:
#                 # 3通道通常为 RGB，转为 BGR
#                 img_cv2 = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
#             else:
#                 # 其他情况（如单通道灰度），直接赋值
#                 img_cv2 = img_np

#             # 提取部位名称作为窗口名 (head, left_hand, right_hand)
#             window_name = topic.split('/')[-1]
#             cv2.imshow(f"Camera: {window_name}", img_cv2)

#             # 使用 OpenCV 处理键盘事件 (30ms 延迟控制播放速度)
#             key = cv2.waitKey(1)
#             if key == ord('q'):
#                 print("\n[用户中断] 已退出播放。")
#                 break

#         # ---------------------------------------------------------
#         # 处理并打印关节数据
#         # ---------------------------------------------------------
#         elif topic == '/joint_states':
#             frame_count += 1
#             timestamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
#             print(f"\n--- 帧 {frame_count} | 时间戳: {timestamp_sec:.3f} ---")
#             for name, pos in zip(msg.name, msg.position):
#                 print(f"  {name}: {pos:+.4f} rad")
#     cv2.destroyAllWindows()

# if __name__ == '__main__':
#     current_dir = os.path.dirname(os.path.abspath(__file__))

#     while True:
#         user_input = input("请输入要查看的数据编号，输入 'q' 结束退出: ").strip()
#         if user_input.lower() == 'q':
#             print("退出程序。")
#             break
#         if user_input.isdigit():
#             folder_name = f"{int(user_input):03d}"
#             target_bag_path = f"../dataset/{folder_name}"
#             path = os.path.join(current_dir, target_bag_path)
#             if not os.path.exists(path):
#                 print(f"提示: 找不到路径 {path}，请检查该数据是否存在。")
#                 continue
#             try:
#                 print(f"正在读取: {path} ...")
#                 read_and_display_all(path)
#             except Exception as e:
#                 print(f"读取出错: {e}")
#         else:
#             print("无效的输入，请输入数字编号或 'q'。")



import sys
import rclpy
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
import rosbag2_py
import cv2
import numpy as np
import os

def read_and_display_all(bag_path):
    # 1. 配置 Reader
    reader = rosbag2_py.SequentialReader()
    storage_options = rosbag2_py.StorageOptions(uri=bag_path, storage_id='mcap')
    converter_options = rosbag2_py.ConverterOptions('', '')
    reader.open(storage_options, converter_options)

    # 获取 topic 信息，构建反序列化字典
    topic_types = reader.get_all_topics_and_types()
    type_map = {topic.name: get_message(topic.type) for topic in topic_types}

    print(f"==========================================")
    print(f" 开始读取 Bag: {bag_path}")
    print(f" 包含的 Topics: {list(type_map.keys())}")
    print(f" 按 OpenCV 窗口中的 'q' 键退出。")
    print(f"==========================================\n")

    frame_count = 0

    # 用于缓存每个视角的最新一帧图像
    latest_images = {
        '/genie_sim/left_camera_rgb': None,
        '/genie_sim/head_front_camera_rgb': None,
        '/genie_sim/right_camera_rgb': None
    }

    # 设定的目标分辨率 (宽 x 高)
    target_size = (640, 480)

    # 2. 遍历 Bag 中的所有消息
    while reader.has_next():
        (topic, data, t) = reader.read_next()
        msg_type = type_map[topic]
        msg = deserialize_message(data, msg_type)

        # ---------------------------------------------------------
        # 处理并显示图像数据
        # ---------------------------------------------------------
        if topic in latest_images.keys():
            channels = len(msg.data) // (msg.height * msg.width)

            # 还原 numpy 数组
            img_np = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width, channels))

            # RGB 转 BGR 以适应 OpenCV 默认色彩空间
            if channels == 4:
                img_cv2 = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
            elif channels == 3:
                img_cv2 = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            else:
                img_cv2 = img_np

            # 1. 缩放图像至 640x480
            img_resized = cv2.resize(img_cv2, target_size)

            # 2. 更新对应 topic 的图像缓存
            latest_images[topic] = img_resized

            # 3. 检查是否三个视角的数据都至少收到了一帧
            if all(img is not None for img in latest_images.values()):
                # 水平拼接图像 (顺序设定为: 左边 -> 头部 -> 右边)
                combined_img = np.hstack((
                    latest_images['/genie_sim/left_camera_rgb'],
                    latest_images['/genie_sim/head_front_camera_rgb'],
                    latest_images['/genie_sim/right_camera_rgb']
                ))

                # 在单个窗口中显示拼接后的画面 (总分辨率为 1920x480)
                cv2.imshow("Genie Sim Cameras (Left | Head | Right)", combined_img)

                # 使用 OpenCV 处理键盘事件
                key = cv2.waitKey(1)
                if key == ord('q'):
                    print("\n[用户中断] 已退出播放。")
                    break

        # ---------------------------------------------------------
        # 处理并打印关节数据
        # ---------------------------------------------------------
        elif topic == '/joint_states':
            frame_count += 1
            timestamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            print(f"\n--- 帧 {frame_count} | 时间戳: {timestamp_sec:.3f} ---")
            for name, pos in zip(msg.name, msg.position):
                print(f"  {name}: {pos:+.4f} rad")
                # idx01_body_joint1: -0.8356 rad
                # idx02_body_joint2: +1.2186 rad
                # idx03_body_joint3: +0.0996 rad
                # idx04_body_joint4: -0.0001 rad
                # idx05_body_joint5: +0.0001 rad

                # idx11_head_joint1: -0.0001 rad
                # idx12_head_joint2: +0.0000 rad
                # idx13_head_joint3: +0.1147 rad

                # idx21_arm_l_joint1: +2.6641 rad
                # idx22_arm_l_joint2: +0.2454 rad
                # idx23_arm_l_joint3: -2.6989 rad
                # idx24_arm_l_joint4: -1.5807 rad
                # idx25_arm_l_joint5: +0.4181 rad
                # idx26_arm_l_joint6: -0.2229 rad
                # idx27_arm_l_joint7: +0.0635 rad
                # idx39_gripper_l_inner_joint0: +0.3182 rad
                # idx31_gripper_l_inner_joint1: -0.6500 rad
                # idx32_gripper_l_inner_joint3: -0.0412 rad
                # idx33_gripper_l_inner_joint4: +0.0281 rad
                # idx49_gripper_l_outer_joint0: -0.3630 rad
                # idx41_gripper_l_outer_joint1: +0.6500 rad
                # idx42_gripper_l_outer_joint3: +0.0207 rad
                # idx43_gripper_l_outer_joint4: +0.0261 rad

                # idx61_arm_r_joint1: -0.7166 rad
                # idx62_arm_r_joint2: -0.3866 rad
                # idx63_arm_r_joint3: +0.8862 rad
                # idx64_arm_r_joint4: -1.6394 rad
                # idx65_arm_r_joint5: -0.5469 rad
                # idx66_arm_r_joint6: +0.0502 rad
                # idx67_arm_r_joint7: -0.2761 rad
                # idx79_gripper_r_inner_joint0: +0.3180 rad
                # idx71_gripper_r_inner_joint1: -0.6500 rad
                # idx72_gripper_r_inner_joint3: -0.0413 rad
                # idx73_gripper_r_inner_joint4: +0.0283 rad
                # idx89_gripper_r_outer_joint0: -0.3183 rad
                # idx81_gripper_r_outer_joint1: +0.6500 rad
                # idx82_gripper_r_outer_joint3: +0.0412 rad
                # idx83_gripper_r_outer_joint4: -0.0280 rad

                # idx111_chassis_lwheel_front_joint1: -0.0005 rad
                # idx112_chassis_lwheel_front_joint2: -0.4830 rad
                # idx121_chassis_lwheel_rear_joint1: -0.0026 rad
                # idx122_chassis_lwheel_rear_joint2: -0.5278 rad
                # idx131_chassis_rwheel_front_joint1: +0.0269 rad
                # idx132_chassis_rwheel_front_joint2: -0.2437 rad
                # idx141_chassis_rwheel_rear_joint1: -0.0020 rad
                # idx142_chassis_rwheel_rear_joint2: -0.5031 rad
    cv2.destroyAllWindows()

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))

    while True:
        user_input = input("请输入要查看的数据编号，输入 'q' 结束退出: ").strip()
        if user_input.lower() == 'q':
            print("退出程序。")
            break
        if user_input.isdigit():
            folder_name = f"{int(user_input):03d}"
            target_bag_path = f"../dataset/{folder_name}"
            path = os.path.join(current_dir, target_bag_path)
            if not os.path.exists(path):
                print(f"提示: 找不到路径 {path}，请检查该数据是否存在。")
                continue
            try:
                print(f"正在读取: {path} ...")
                read_and_display_all(path)
            except Exception as e:
                print(f"读取出错: {e}")
        else:
            print("无效的输入，请输入数字编号或 'q'。")
