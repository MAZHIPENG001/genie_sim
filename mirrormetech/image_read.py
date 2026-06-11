# Copyright (c) 2023-2026, AgiBot Inc. All Rights Reserved.
# Author: Genie Sim Team
# License: Mozilla Public License Version 2.0

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np

class GeniesimImageViewer(Node):
    def __init__(self):
        super().__init__('geniesim_image_viewer')

        self.bridge = CvBridge()

        self.img_width = 640
        self.img_height = 480

        self.blank_image = np.zeros((self.img_height, self.img_width, 3), dtype=np.uint8)
        self.img_camera = self.blank_image.copy()
        self.img_head = self.blank_image.copy()
        self.img_left = self.blank_image.copy()
        self.img_right = self.blank_image.copy()

        qos_profile = 10

        self.sub_camera_rgb = self.create_subscription(
            Image, '/genie_sim/camera_rgb', self.camera_rgb_callback, qos_profile)
        self.sub_head_front_rgb = self.create_subscription(
            Image, '/genie_sim/head_front_camera_rgb', self.head_front_rgb_callback, qos_profile)
        self.sub_left_rgb = self.create_subscription(
            Image, '/genie_sim/left_camera_rgb', self.left_rgb_callback, qos_profile)
        self.sub_right_rgb = self.create_subscription(
            Image, '/genie_sim/right_camera_rgb', self.right_rgb_callback, qos_profile)

        self.timer = self.create_timer(0.033, self.display_timer_callback)

        self.get_logger().info("图像显示节点已启动，正在等待图像数据...")

    def process_image(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            cv_image = cv2.resize(cv_image, (self.img_width, self.img_height))
            return cv_image
        except Exception as e:
            self.get_logger().error(f"图像转换错误: {e}")
            return self.blank_image.copy()

    def camera_rgb_callback(self, msg):
        self.img_camera = self.process_image(msg)
    def head_front_rgb_callback(self, msg):
        self.img_head = self.process_image(msg)
    def left_rgb_callback(self, msg):
        self.img_left = self.process_image(msg)
    def right_rgb_callback(self, msg):
        self.img_right = self.process_image(msg)

    def display_timer_callback(self):
        top_row = cv2.hconcat([self.img_camera, self.img_head])
        bottom_row = cv2.hconcat([self.img_left, self.img_right])
        combined_image = cv2.vconcat([top_row, bottom_row])

        cv2.putText(combined_image, "Camera RGB", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(combined_image, "Head Front RGB", (self.img_width + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(combined_image, "Left Camera RGB", (10, self.img_height + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(combined_image, "Right Camera RGB", (self.img_width + 10, self.img_height + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow('Geniesim Viewer', combined_image)
        cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = GeniesimImageViewer()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("节点被手动终止")
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
