from time import sleep
from typing import Tuple
from math import cos, sin, pi, tau, atan2, sqrt, pow
import cv2
import numpy as np

LOG = False


def find_1d_ranges(img, axis, limit=None, min_size=5):
    range_start = None
    found = 0
    for position in range(img.shape[axis] - 1, -1, -1):
        slice = img[:, position] if axis == 1 else img[position, :]
        slice_sum = sum(slice > 0)
        if range_start:
            if slice_sum == 0:
                if range_start - position >= min_size:
                    found += 1
                    yield position, range_start

                if limit and found >= limit:
                    return

                range_start = None
        else:  # Not in a range
            if slice_sum:
                range_start = position


def find_registration_pels(img):
    for start, end in find_1d_ranges(img, 1, 2):
        y_start, y_end = tuple(find_1d_ranges(img[:, start:end], 0, 1))[0]
        yield round(start + (end - start) / 2), round(y_start + (y_end - y_start) / 2)


def find_center(reg0deg: Tuple[float, float], reg60deg: Tuple[float, float]):
    root3 = sqrt(3)
    x1, y1 = reg60deg
    x2, y2 = reg0deg
    # https://www.quora.com/Given-two-vertices-of-an-equilateral-triangle-what’s-the-formula-to-find-the-third-vertex/answer/Greg-Gruzalski
    return (x1 + x2 + root3 * (y1 - y2)) / 2, (y1 + y2 + root3 * (x2 - x1)) / 2


def frame_values():
    cap = cv2.VideoCapture('cpx.mov')
    ret, frame = cap.read()
    while ret:
        gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        scale = 0.3
        img = cv2.resize(gray_img, (0, 0), fx=scale, fy=scale)
        bright = cv2.inRange(img, 250, 255)
        reg_pels = tuple(find_registration_pels(bright))
        if len(reg_pels) == 2:
            reg0deg, reg60deg = reg_pels
            center = find_center(reg0deg, reg60deg)
            dx = reg0deg[0] - center[0]
            dy = reg0deg[1] - center[1]
            radius = sqrt(pow(dx, 2) + pow(dy, 2))
            global_rotation = atan2(dy, dx)
            twelfth = tau / 12
            def angle(power): return twelfth * (power + 4) + global_rotation
            bits = ((round(center[0] + cos(angle(power)) * radius),
                       round(center[1] + sin(angle(power)) * radius)) for power in range(5))
            parts = (int(pow(2, 4-i)) * (1 if bright[b[1], b[0]] > 0 else 0) for i, b in enumerate(bits))
            yield sum(parts)
        ret, frame = cap.read()
    cap.release()
    cv2.destroyAllWindows()
    return


def likely_values():
    batch = []
    for v in frame_values():
        if LOG and v > 0:
            print(v, '', end='')
        if v:
            batch.append(v)
        else:
            if batch:
                largest = max(batch)
                if LOG: print(largest)
                yield largest
                batch = []


a_offset = ord('a')
for v in likely_values():
    c = ' ' if v == 27 else chr(v + a_offset - 1)
    end = '\n' if LOG else ''
    print(c, end=end)