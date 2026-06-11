# Copyright (c) 2023-2026, AgiBot Inc. All Rights Reserved.
# Author: Genie Sim Team
# License: Mozilla Public License Version 2.0

import rclpy
from rclpy.node import Node
import time

class NodeInspector(Node):
    def __init__(self):
        super().__init__('python_node_inspector')

    def inspect_and_save_nodes(self, filename="node_information.txt"):
        # 获取当前网络中的所有节点
        node_names_and_namespaces = self.get_node_names_and_namespaces()

        if not node_names_and_namespaces:
            print("未发现任何节点！(除了本脚本)")
            return

        print(f"共发现 {len(node_names_and_namespaces)} 个节点，正在写入文件 '{filename}'...")

        # 打开文件准备写入（使用 utf-8 编码防止乱码）
        with open(filename, 'w', encoding='utf-8') as f:
            # 写入文件头信息
            f.write("====================================================\n")
            f.write("               ROS 2 节点信息报告\n")
            f.write(f" 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n")
            f.write("====================================================\n\n")

            for node_name, namespace in node_names_and_namespaces:
                # 过滤掉本脚本自身的临时节点
                if node_name == 'python_node_inspector':
                    continue

                self._write_node_info_to_file(f, node_name, namespace)

        print(f"【成功】所有节点信息已成功保存至当前目录下的: {filename}")

    def _write_node_info_to_file(self, file, node_name, namespace):
        # 拼接完整的节点路径
        full_node_path = f"{namespace}{node_name}" if namespace == '/' else f"{namespace}/{node_name}"
        file.write(f"========== 节点: {full_node_path} ==========\n")

        # 1. 获取并写入发布者
        pubs = self.get_publisher_names_and_types_by_node(node_name, namespace)
        file.write("[发布者 Publishers]:\n")
        self._write_items(file, pubs)

        # 2. 获取并写入订阅者
        subs = self.get_subscriber_names_and_types_by_node(node_name, namespace)
        file.write("\n[订阅者 Subscribers]:\n")
        self._write_items(file, subs)

        # 3. 获取并写入服务端
        srvs = self.get_service_names_and_types_by_node(node_name, namespace)
        file.write("\n[服务端 Services]:\n")
        self._write_items(file, srvs)

        # 4. 获取并写入客户端
        clients = self.get_client_names_and_types_by_node(node_name, namespace)
        file.write("\n[客户端 Clients]:\n")
        self._write_items(file, clients)

        file.write("====================================================\n\n")

    def _write_items(self, file, items):
        if not items:
            file.write("  (无)\n")
            return
        for name, types in items:
            file.write(f"  - 名称: {name}\n    类型: {types}\n")

def main(args=None):
    rclpy.init(args=args)
    inspector = NodeInspector()

    print("正在扫描 ROS 2 网络拓扑，请稍候...")
    time.sleep(1.0) # 等待网络拓扑发现

    # 执行检查并保存
    inspector.inspect_and_save_nodes("node_information.txt")

    # 清理退出
    inspector.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
