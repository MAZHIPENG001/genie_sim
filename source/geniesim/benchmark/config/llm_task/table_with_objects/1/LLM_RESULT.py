# Copyright (c) 2023-2026, AgiBot Inc. All Rights Reserved.
# Author: Genie Sim Team
# License: Mozilla Public License Version 2.0

from helper import *
import random
import math

"""
scene_name: table_with_two_random_objects
description: A table with two randomly selected distinct objects placed near the center, slightly closer to the operator, with random yaw rotation and no collision.
"""

@register()
def table_with_objects() -> Shape:
    # Load the table
    table_shape = library_call(
        "usd",
        oid="table_000",
        keywords=["table", "workspace", "desktop", "legs", "center"]
    )

    # Get table bounding box info
    table_info = get_object_info(table_shape)
    table_top_z = table_info["max"]
    table_center_x = table_info["center"]
    table_center_y = table_info["center"]

    # Object list provided by user
    object_list = ["apple", "blocks", "cola", "facecleaner", "sprite"]

    # Randomly select two distinct objects
    selected_objects = random.sample(object_list, 2)

    # Placement parameters
    # Slightly closer to the operator (assuming +x is forward/towards the operator)
    offset_x = 0.15
    base_x = table_center_x + offset_x

    # Y offsets to ensure no collision between the two objects
    # According to coordinate system: +y is left, -y is right
    y_offsets = [-0.2, 0.2]
    position_tags = ["right", "left"]

    shapes = [table_shape]

    for i, obj_name in enumerate(selected_objects):
        pos_tag = position_tags[i]

        # Load object with position tag in keywords
        obj_shape = library_call(
            "usd",
            oid=obj_name,
            keywords=[obj_name, "object", "item", pos_tag, f"selected_{i}"]
        )

        # Calculate placement position
        pos_x = base_x
        pos_y = table_center_y + y_offsets[i]
        pos_z = table_top_z

        # Translate object to the table surface
        # usd() returns shape with origin at bottom, so pos_z places it exactly on the table
        # obj_shape = transform_shape(obj_shape, translation_matrix(pos_x, pos_y, pos_z))

        try:
            translation_vec = [
                float(pos_x) if pos_x is not None else 0.0,
                float(pos_y) if pos_y is not None else 0.0,
                float(pos_z) if pos_z is not None else 0.0
            ]
            translation_mat = translation_matrix(translation_vec)
            obj_shape = transform_shape(obj_shape, translation_mat)
        except (TypeError, ValueError) as e:
            print(f"Error creating translation matrix: {e}")
            # 如果仍然失败，使用默认位置
            obj_shape = transform_shape(obj_shape, translation_matrix([0, 0, 0]))

        # Apply random yaw rotation (0 to 360 degrees) around the object's center
        angle = random.uniform(0, 2 * math.pi)
        obj_center = compute_shape_center(obj_shape)
        obj_shape = transform_shape(
            obj_shape,
            rotation_matrix(angle, direction=(0, 0, 1), point=obj_center)
        )

        shapes.append(obj_shape)

    return concat_shapes(*shapes)

@register()
def root_scene() -> Shape:
    return library_call("table_with_objects")
