"""Feature formulas copied from the desktop prototype without opening a camera."""
import math

LEFT_EYE = {'left': 33, 'right': 133, 'upper1': 160, 'lower1': 144, 'upper2': 158, 'lower2': 153}
RIGHT_EYE = {'left': 362, 'right': 263, 'upper1': 385, 'lower1': 380, 'upper2': 387, 'lower2': 373}
MOUTH_LEFT = 61
MOUTH_RIGHT = 291
MOUTH_UPPER = 13
MOUTH_LOWER = 14

def get_point(landmarks, index, width, height):
    lm = landmarks[index]
    return (int(lm.x * width), int(lm.y * height))

def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def calculate_ear(landmarks, eye, width, height):
    left = get_point(landmarks, eye['left'], width, height)
    right = get_point(landmarks, eye['right'], width, height)
    upper1 = get_point(landmarks, eye['upper1'], width, height)
    lower1 = get_point(landmarks, eye['lower1'], width, height)
    upper2 = get_point(landmarks, eye['upper2'], width, height)
    lower2 = get_point(landmarks, eye['lower2'], width, height)
    horizontal = distance(left, right)
    if horizontal <= 0:
        return 0.0
    vertical1 = distance(upper1, lower1)
    vertical2 = distance(upper2, lower2)
    return (vertical1 + vertical2) / (2.0 * horizontal)

def calculate_mar(landmarks, width, height):
    left = get_point(landmarks, MOUTH_LEFT, width, height)
    right = get_point(landmarks, MOUTH_RIGHT, width, height)
    upper = get_point(landmarks, MOUTH_UPPER, width, height)
    lower = get_point(landmarks, MOUTH_LOWER, width, height)
    horizontal = distance(left, right)
    if horizontal <= 0:
        return 0.0
    vertical = distance(upper, lower)
    return vertical / horizontal
