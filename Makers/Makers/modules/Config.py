"""
提供封装信息与配置文件

该模块定义了控制小车运动模式、颜色信息以及其他相关配置类
"""

import enum
import sys
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO")
#logger.add("/home/flmg/Desktop/Makers/log/interface_log.log", level="DEBUG")
logger.add("Makers/log/interface_log.log", level="DEBUG")
my_logger = logger


class MoveMode(enum.IntEnum):
    """
    该类用于封装小车运动及控制模式
    枚举成员:
        Forward: 前进
        Backward: 后退
        Leftward: 向左走
        Rightward: 向右走
        Topleft: 向左上走
        Topright: 向右上走
        Lowerleft: 向左下走
        Lowerright: 向右下走
        Turnleft: 左转
        Turnright: 右转
        Calibration: 校准
        Servo: 舵机

        Bigarm: 大臂
        Forearm: 小臂
        Frontpaws: 前爪
        Hindpaws: 后爪
        Frontdoor: 前门
        Backdoor: 后门
        Cirque: 圆环

        Highest: 调高
    """
    Forward = 1
    Backward = 2
    Leftward = 3
    Rightward = 4
    Topleft = 5
    Topright = 6
    Lowerleft = 7
    Lowerright = 8
    Turnleft = 9
    Turnright = 10
    Calibration = 11
    Servo = 12

    Bigarm = 13
    Forearm = 14
    Frontpaws = 15
    Hindpaws = 16
    Frontdoor = 17
    Backdoor = 18
    Cirque = 19

    Highest = 20
    Advance = 21


class GrabMode(enum.IntEnum):
    """
    该类用于封装舵机运动及控制模式
    """

    Big_Diameter = 1
    Small_Diameter = 2

    Platform_High_Start = 3
    Platform_High_End = 4
    Platform_High_End_Circle = 5

    Platform_Medium_Start = 6
    Platform_Medium_End = 7
    Platform_Medium_End_Circle = 8

    Platform_Low_Start = 9
    Platform_Low_End = 10
    Platform_Low_End_Circle = 11

    Put_Circle = 12


class ColorSerial(enum.IntEnum):
    """
    该类用于封装颜色信息

    枚举成员:
        red: 红色
        blue: 蓝色
        yellow: 黄色
    """
    red = 1
    blue = 2
    yellow = 3


# 映射ColorSerial枚举到实际的颜色名称
SerialColor = {
    ColorSerial.red: 'red',
    ColorSerial.blue: 'blue',
    ColorSerial.yellow: 'yellow',
}


color_ranges = {
    'red': [([0, 100, 100], [10, 255, 255]), ([160, 100, 100], [179, 255, 255])],
    'blue': [([95, 100, 100], [120, 255, 255])],
    'yellow': [([20, 100, 100], [30, 255, 255])],
}


if __name__ == '__main__':
    # 测试日志输出
    my_logger.info('logger_test')
    my_logger.error('error_test')
