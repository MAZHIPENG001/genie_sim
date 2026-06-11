# Copyright (c) 2023-2026, AgiBot Inc. All Rights Reserved.
# Author: Genie Sim Team
# License: Mozilla Public License Version 2.0

from helper import *
from typing import Tuple
import numpy as np

"""
scene_name: table_with_five_apples
description: Five apples placed on a table
"""

def find_table_top_surface(table_shape: Shape) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculates the world coordinates of the table's top surface and its usable size.
    """
    table_max = compute_shape_max(table_shape)       # [max_x, max_y, max_z]
    table_center = compute_shape_center(table_shape) # [center_x, center_y, center_z]
    table_size = compute_shape_sizes(table_shape)    # [size_x, size_y, size_z]

    # Top surface center: 取桌子的中心 X, Y，以及最大高度 Z
    top_center = np.array([table_center[0], table_center[1], table_max[2]])
    # Usable surface size: 取 X 和 Y 尺寸的 80%
    surface_size = np.array([table_size[0] * 0.8, table_size[1] * 0.8, 0.0])

    return top_center, surface_size

@register()
def place_apples_on_table(table_shape: Shape) -> Shape:
    """
    Places five apples on the table surface without collision.
    """
    workspace, margin = find_table_top_surface(table_shape)

    # 解包中心点和边界
    center_x, center_y, top_z = workspace
    margin_x, margin_y, _ = margin

    # Get a reference apple to compute size for collision avoidance
    ref_apple = library_call("usd", oid="apple", keywords=["apple", "red", "fruit", "reference"])
    apple_size = compute_shape_sizes(ref_apple)
    # 取苹果 X 或 Y 方向的最大直径的一半作为半径
    apple_radius = max(apple_size[0], apple_size[1]) / 2.0

    apples_list = []
    placed_positions = []

    for i in range(5):
        # Find a valid position without collision
        max_attempts = 50
        x, y = center_x, center_y # fallback position

        for _ in range(max_attempts):
            x = np.random.uniform(
                center_x - margin_x / 2.0 + apple_radius,
                center_x + margin_x / 2.0 - apple_radius
            )
            y = np.random.uniform(
                center_y - margin_y / 2.0 + apple_radius,
                center_y + margin_y / 2.0 - apple_radius
            )

            # Check collision with already placed apples
            collision = False
            for px, py in placed_positions:
                if np.sqrt((x - px)**2 + (y - py)**2) < apple_radius * 2.2:
                    collision = True
                    break

            if not collision:
                placed_positions.append((x, y))
                break

        # Calculate POSITION TAG based on y coordinate
        pos_tag = "left" if y > center_y else "right"

        apple = library_call(
            "usd",
            oid="apple",
            keywords=["apple", "red", "fruit", f"apple_{i+1}", pos_tag]
        )

        # Translate apple to the chosen position on the table top
        # 注意这里的 Z 坐标使用的是桌面的 top_z
        apple = transform_shape(apple, translation_matrix([x, y, top_z]))
        apples_list.append(apple)

    return concat_shapes(table_shape, *apples_list)

@register()
def table_with_five_apples() -> Shape:
    """
    Creates the main scene with a table and five apples.
    """
    table_shape = library_call(
        "usd",
        oid="table_001",
        keywords=["table", "wood", "dining_table", "center"]
    )
    return place_apples_on_table(table_shape)

@register()
def root_scene() -> Shape:
    return table_with_five_apples()
