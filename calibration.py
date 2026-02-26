from typing import Iterable, List, Sequence, Tuple

import numpy as np


def compute_six_position_calibration(
    axis_samples: Sequence[Sequence[float]], gravity: float
) -> Tuple[List[float], List[float]]:
    """
    根据 6 个静止姿态的数据计算某一加速度计的 scale / offset。

    axis_samples: 长度为 6 的序列，每个元素为长度为 3 的 (x, y, z) 向量，对应：
        0: +X axis down
        1: -X axis down
        2: +Y axis down
        3: -Y axis down
        4: +Z axis down
        5: -Z axis down

    返回:
        (scales, offsets)，其中 scales/offsets 均为长度为 3 的列表。
    """
    if len(axis_samples) != 6:
        raise ValueError("compute_six_position_calibration requires exactly 6 positions")

    arr = np.asarray(axis_samples, dtype=float)
    if arr.shape != (6, 3):
        raise ValueError("axis_samples must have shape (6, 3)")

    scales: List[float] = []
    offsets: List[float] = []

    for axis in range(3):
        pos_idx = axis * 2
        neg_idx = axis * 2 + 1

        pos_val = float(arr[pos_idx, axis])
        neg_val = float(arr[neg_idx, axis])

        offset = (pos_val + neg_val) / 2.0
        delta = pos_val - neg_val

        if abs(delta) > 1e-6:
            raw_scale = delta / (2.0 * gravity)
        else:
            raw_scale = 1.0

        scale_factor = 1.0 / raw_scale if abs(raw_scale) > 1e-6 else 1.0

        offsets.append(offset)
        scales.append(scale_factor)

    return scales, offsets


def compute_gyro_offset(samples: Iterable[Sequence[float]]) -> List[float]:
    """
    根据多组静止状态下的陀螺仪读数计算三轴零偏。

    samples: 可迭代对象，每个元素为长度为 3 的 (x, y, z) 向量。
    """
    arr = np.asarray(list(samples), dtype=float)
    if arr.size == 0:
        return [0.0, 0.0, 0.0]
    mean = arr.mean(axis=0)
    return [float(mean[0]), float(mean[1]), float(mean[2])]

