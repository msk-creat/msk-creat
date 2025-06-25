"""
主流程函数
"""

from modules.Config import my_logger, GrabMode
from modules.Detection import Camera
from modules.MoveControl import MoveControl
import time


class MainControl:
    """
    用于主流程控制的类

    这个类提供了各设备接口实例化与主流程控制功能

    方法:
        __init__: 进行各接口实例化
        whether_continue: 暂停进程
        start: 主流程
    """

    def __init__(self, port: str, baudrate: int = 9600, camera_index: int = 0) -> None:
        """
        设备初始化

        Args:
            port(str): 设备端口号
            baudrate(int): 波特率
            camera_index(int): 摄像头序号

        Returns:
            None
        """
        self.port = port
        self.baudrate = baudrate
        self.camera_index = camera_index

        self.camera = Camera(self.camera_index)
        self.movecontrol = MoveControl(port=port, baudrate=baudrate)

        self.skip = False

    def whether_continue(self) -> None:
        """
        暂停程序

        Returns:
            None
        """
        while True:
            data = input('是否继续运行程序[y/s/n]:')
            if data == 'y' or data == 'Y':
                return
            elif data == 's' or data == 'S':
                self.skip = True
                return

            elif data == 'n' or data == 'N':
                self.camera.release()
                exit(0)
            else:
                print(f'请正确选择模式')
                continue

    def init_to_start(self) -> None:
        self.camera.open()
        self.camera.debug = False
        self.movecontrol.advance()
        self.movecontrol.hindpaws(angle=0)
        self.movecontrol.frontpaws(angle=0)

    def go_to_big_diameter(self) -> None:
        self.whether_continue()
        if self.skip:
            self.skip = False
            return None
        self.movecontrol.move_Y(distance=-0.42)
        self.movecontrol.move_X(distance=1.9)
        self.movecontrol.move_X(distance=1.9)

    def turn_to_big_diameter(self) -> None:
        self.whether_continue()
        if self.skip:
            self.skip = False
            return None
        self.movecontrol.highest()
        self.movecontrol.rotate(angle=-720)
        self.adjust_angle_by_cross()
        self.adjust_location_by_cross()
        self.movecontrol.forearm(angle=45)
        self.movecontrol.frontpaws(angle=25)

    def grab_ball_from_big_diameter(self) -> None:
        self.whether_continue()
        if self.skip:
            self.skip = False
            return None

        start_time = time.time()

        first_skip = self.camera.detect_colors_bigmeter()
        while True:
            predict_result = self.camera.detect_colors_bigmeter()
            if first_skip != predict_result:
                if first_skip == 'red':
                        self.movecontrol.frontdoor(angle=66)
                        self.movecontrol.servo(grab_mode=GrabMode.Big_Diameter)
                elif first_skip == 'yellow':
                        self.movecontrol.frontdoor(angle=0)
                        self.movecontrol.servo(grab_mode=GrabMode.Big_Diameter)
                break

        while (time.time() - start_time) < 20:  # 添加时间限制条件
            predict_result = self.camera.detect_colors_bigmeter()

            if predict_result == 'red':
                self.movecontrol.frontdoor(angle=66)
                self.movecontrol.servo(grab_mode=GrabMode.Big_Diameter)
            elif predict_result == 'yellow':
                self.movecontrol.frontdoor(angle=0)
                self.movecontrol.servo(grab_mode=GrabMode.Big_Diameter)

    def turn_away_from_big_diameter(self) -> None:
        self.whether_continue()
        if self.skip:
            self.skip = False
            return None
        self.movecontrol.highest()
        self.movecontrol.rotate(angle=720)

    def go_to_platform(self):
        self.whether_continue()
        if self.skip:
            self.skip = False
            return None
        self.movecontrol.rotate(angle=720)
        self.movecontrol.advance()

        self.movecontrol.move_X(distance=1)
        self.movecontrol.rotate(angle=720)
        self.movecontrol.move_X(distance=2.2)
        self.movecontrol.rotate(angle=-720)
        self.movecontrol.highest()
        self.adjust_angle_by_cross()
        self.adjust_location_by_cross_platform()

    def grab_from_platform_medium(self) -> None:
        self.whether_continue()
        if self.skip:
            self.skip = False
            return None

        qr_code = self.camera.recognite_qr_info()
        self.adjust_location()

        self.movecontrol.servo(grab_mode=GrabMode.Platform_Medium_Start)

        if qr_code == 'red':
            self.movecontrol.servo(grab_mode=GrabMode.Platform_Medium_End)
        else:
            color = self.camera.detect_colors_platform()
            if color is not None:
                for _ in range(2):
                    self.camera.detect_colors_platform()
                    self.adjust_location()
            if color == 'red':
                circle = self.camera.detect_circles()
                if circle:
                    self.movecontrol.servo(grab_mode=GrabMode.Platform_Medium_End_Circle)
                else:
                    self.movecontrol.servo(grab_mode=GrabMode.Platform_Medium_End)

        self.movecontrol.highest()
        self.movecontrol.move_Y(distance=-0.1)

    def grab_from_platform_high(self) -> None:
        self.whether_continue()
        if self.skip:
            self.skip = False
            return None
        
        qr_code = self.camera.recognite_qr_info()
        self.adjust_location()

        self.movecontrol.servo(grab_mode=GrabMode.Platform_High_Start)

        if qr_code == 'red':
            self.movecontrol.servo(grab_mode=GrabMode.Platform_High_End)
        else:
            color = self.camera.detect_colors_platform()
            if color is not None:
                for _ in range(3):
                    self.camera.detect_colors_platform()
                    self.adjust_location()
            if color == 'red':
                circle = self.camera.detect_circles()
                if circle:
                    self.movecontrol.servo(grab_mode=GrabMode.Platform_High_End_Circle)
                else:
                    self.movecontrol.servo(grab_mode=GrabMode.Platform_High_End)

        self.movecontrol.highest()
        self.movecontrol.move_Y(distance=-0.08)

    def grab_from_platform_low(self) -> None:
        self.whether_continue()
        if self.skip:
            self.skip = False
            return None
            
        self.movecontrol.bigarm(angle=90)
        self.movecontrol.forearm(angle=50)

        qr_code = self.camera.recognite_qr_info()
        self.adjust_location()

        self.movecontrol.servo(grab_mode=GrabMode.Platform_Low_Start)

        if qr_code == 'red':
            self.movecontrol.servo(grab_mode=GrabMode.Platform_Low_End)
        else:
            color = self.camera.detect_colors_platform()
            if color is not None:
                for _ in range(3):
                    self.camera.detect_colors_platform()
                    self.adjust_location()
            if color == 'red':
                circle = self.camera.detect_circles_platform_low()
                if circle:
                    self.movecontrol.servo(grab_mode=GrabMode.Platform_Low_End_Circle)
                else:
                    self.movecontrol.servo(grab_mode=GrabMode.Platform_Low_End)

        self.movecontrol.highest()
        self.movecontrol.move_Y(distance=-0.05)

    def go_to_ware_house(self) -> None:
        self.whether_continue()
        if self.skip:
            self.skip = False
            return None
        self.movecontrol.move_X(distance=-0.2)
        self.adjust_angle_by_cross()
        self.movecontrol.rotate(angle=-1440)
        self.movecontrol.move_X(distance=1.3)
        self.adjust_angle_by_cross()

        self.movecontrol.move_Y(distance=-0.1)

        for _ in range(3):
            self.camera.detect_circles()
            self.adjust_location()

        self.movecontrol.servo(grab_mode=GrabMode.Put_Circle)

        self.movecontrol.move_Y(distance=-0.86)
        self.movecontrol.rotate(angle=-1440)
        self.movecontrol.move_X(distance=-0.1)

    def put_down_items(self) -> None:
        self.whether_continue()
        if self.skip:
            self.skip = False
            return None
        self.movecontrol.backdoor(angle=20)
        time.sleep(2)
        self.movecontrol.backdoor(angle=0)

    def go_home(self) -> None:

        self.movecontrol.advance()
        self.movecontrol.move_Y(distance=1)
        self.movecontrol.move_X(distance=0.4)
        self.movecontrol.highest()

        for _ in range(3):
            self.camera.detect_colors_bigmeter()
            self.adjust_location()

        self.movecontrol.advance()
        self.movecontrol.move_X(distance=0.3)

    def adjust_location(self) -> None:
        x_value = (self.camera.location_x - self.camera.center_x) * 0.000185
        y_value = (self.camera.center_y - self.camera.location_y) * 0.000185

        my_logger.info(f'x:{x_value} y:{y_value}')

        x_value = (x_value * 100) / 100
        y_value = (y_value * 100) / 100

        my_logger.info(f'x:{x_value} y:{y_value}')

        self.movecontrol.move_X(distance=x_value)
        self.movecontrol.move_Y(distance=y_value)

    def adjust_angle_by_cross(self) -> None:
        _, angle = self.camera.calculate_angle_by_cross()
        angle = int((90 - angle) * 8)
        self.movecontrol.rotate(angle=angle)

    def adjust_location_by_cross(self) -> None:
        distance = self.camera.calculate_location_by_cross()
        distance = (distance - 85) * 0.001 + 0.17

        distance = (distance * 100) / 100

        self.movecontrol.move_X(distance=distance)

    def adjust_location_by_cross_platform(self) -> None:
        distance = self.camera.calculate_location_by_cross_platform()
        distance = (distance - 205) * 0.001 + 0.14

        distance = (distance * 100) / 100

        self.movecontrol.move_X(distance=distance)

    def start(self) -> None:

        my_logger.info(f'进行初始化')
        self.init_to_start()
        my_logger.info(f'初始化完成， 等待下位机发送开始指令')
        # self.movecontrol.wait_for_start_cmd()
        my_logger.info(f'接收到开始指令，开始执行任务')

        my_logger.info(f'-------------------前往大圆盘-------------------')

        self.go_to_big_diameter()
        my_logger.info(f'抵达大圆盘')

        my_logger.info(f'转向大圆盘')
        self.turn_to_big_diameter()

        my_logger.info(f'准备抓取小球')
        self.grab_ball_from_big_diameter()

        my_logger.info(f'转离大圆盘')
        self.turn_away_from_big_diameter()

        my_logger.info(f'-------------------大圆盘任务结束-------------------')

        my_logger.info(f'-------------------前往颁奖台-------------------')

        self.go_to_platform()
        my_logger.info(f'颁奖台-低，第一个物体')
        self.grab_from_platform_low()
        my_logger.info(f'颁奖台-低，第一个物体')
        self.grab_from_platform_low()

        my_logger.info(f'颁奖台-高，第一个物体')
        self.grab_from_platform_high()
        my_logger.info(f'颁奖台-高，第二个物体')
        self.grab_from_platform_high()
        my_logger.info(f'颁奖台-高，第三个物体')
        self.grab_from_platform_high()
        my_logger.info(f'颁奖台-高，第四个物体')
        self.grab_from_platform_high()

        my_logger.info(f'颁奖台-中，第一个物体')
        self.grab_from_platform_medium()
        my_logger.info(f'颁奖台-中，第二个物体')
        self.grab_from_platform_medium()

        my_logger.info(f'-------------------颁奖台任务结束 -------------------')

        my_logger.info(f'-------------------前往仓储区-------------------')
        self.go_to_ware_house()
        my_logger.info(f'-------------------抵达仓储区-------------------')

        my_logger.info(f'-------------------准备投放物料-------------------')
        self.put_down_items()
        my_logger.info(f'-------------------物理投放结束-------------------')


if __name__ == '__main__':
    stm_port = '/dev/ttyUSB0'
    stm_baudrate = 9600
    cam_index = 0

    control = MainControl(port=stm_port, baudrate=stm_baudrate, camera_index=cam_index)

    control.start()
