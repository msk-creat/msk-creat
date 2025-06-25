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
        self.movecontrol.rotate(angle=720)
        self.movecontrol.move_X(distance=0.6)
        self.movecontrol.rotate(angle=-740)
        self.movecontrol.move_X(distance=1.9)
        self.movecontrol.move_X(distance=1.85)

    def turn_to_big_diameter(self) -> None:
        self.movecontrol.highest()
        self.movecontrol.rotate(angle=720)
        self.adjust_angle_by_lines()
        self.adjust_location_by_lines()
        self.movecontrol.move_X(distance=0.16)
        self.movecontrol.forearm(angle=45)
        self.movecontrol.frontpaws(angle=10)

    def grab_ball_from_big_diameter(self) -> None:
        start_time = time.time()
        first_skip = None

        while (time.time() - start_time) < 10:
            predict_result = self.camera.detect_colors_bigmeter()
            if predict_result not in ['red', 'yellow']:
                continue
            elif first_skip is None:
                first_skip = predict_result

            elif first_skip != predict_result:
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

    def turn_away_from_big_diameter_to_warehouse(self) -> None:
        self.movecontrol.highest()
        self.movecontrol.move_X(distance=-0.15)

        self.adjust_angle_by_lines()

        self.movecontrol.rotate(angle=720)
        self.movecontrol.advance()
        self.movecontrol.move_X(distance=1.6)
        self.movecontrol.rotate(angle=-720)
        # self.movecontrol.move_X(distance=0.2)
        self.movecontrol.highest()
        self.adjust_angle_by_lines()
        self.adjust_location_by_lines()
        self.movecontrol.advance()
        self.movecontrol.rotate(angle=-1440)
        self.movecontrol.move_X(distance=-0.2)

    def go_back_to_diameter(self) -> None:
        self.movecontrol.move_X(distance=0.1)
        self.movecontrol.rotate(angle=700)
        self.movecontrol.advance()
        self.movecontrol.move_X(distance=1.6)

    def turn_away_from_big_diameter(self) -> None:

        self.movecontrol.highest()
        self.movecontrol.move_X(distance=-0.1)
        # self.adjust_angle_by_lines(reverse=True)
        self.movecontrol.frontdoor(angle=66)
        self.movecontrol.rotate(angle=720)

    def go_to_platform(self):

        self.movecontrol.rotate(angle=-715)
        self.movecontrol.advance()

        self.movecontrol.move_X(distance=0.6)
        self.movecontrol.rotate(angle=-720)

        self.movecontrol.move_X(distance=0.2)
        self.movecontrol.rotate(angle=725)
        self.movecontrol.move_X(distance=0.7)

        self.movecontrol.rotate(angle=-700)
        # self.movecontrol.move_X(distance=0.9)
        self.movecontrol.move_X(distance=0.94)
        self.movecontrol.rotate(angle=720)
        self.movecontrol.highest()
        self.movecontrol.move_X(distance=0.1)

        self.adjust_angle_by_lines()
        self.adjust_location_by_lines()

        self.movecontrol.move_X(distance=0.1)

    def grab_from_platform_low(self) -> None:
        qr_code = self.camera.recognite_qr_info()
        if qr_code is None:
            self.movecontrol.bigarm(angle=110)
            self.movecontrol.forearm(angle=35)
            qr_code = self.camera.recognite_qr_info()
            if qr_code is not None:
                self.adjust_location()
            circle_previous = self.camera.detect_circles()
            self.movecontrol.servo(grab_mode=GrabMode.Platform_Low_Start)

        if qr_code is not None:
            if qr_code == 'red':
                self.movecontrol.servo(grab_mode=GrabMode.Platform_Low_End)
        else:
            color = self.camera.detect_colors_platform()
            if color is not None:
                for _ in range(2):
                    self.camera.detect_colors_platform()
                    self.adjust_location()
            if color == 'red':
                circle = self.camera.detect_circles_platform_low()
                if circle or circle_previous:
                    pass
                    # self.movecontrol.servo(grab_mode=GrabMode.Platform_Low_End_Circle)
                else:
                    self.movecontrol.servo(grab_mode=GrabMode.Platform_Low_End)

        self.movecontrol.servo(grab_mode=GrabMode.Platform_Low_Start)

    def grab_from_platform_high(self) -> None:
        qr_code = self.camera.recognite_qr_info()
        if qr_code is None:
            self.movecontrol.bigarm(angle=100)
            self.movecontrol.forearm(angle=15)
            qr_code = self.camera.recognite_qr_info()
            if qr_code is not None:
                self.adjust_location()
            circle_previous = self.camera.detect_circles()
            self.movecontrol.servo(grab_mode=GrabMode.Platform_High_Start)

        if qr_code is not None:
            if qr_code == 'red':
                self.movecontrol.servo(grab_mode=GrabMode.Platform_High_End)
        else:
            color = self.camera.detect_colors_platform()
            if color is not None:
                for _ in range(2):
                    self.camera.detect_colors_platform()
                    self.adjust_location()
            if color == 'red':
                circle = self.camera.detect_circles()
                if circle or circle_previous:
                    pass
                    # self.movecontrol.servo(grab_mode=GrabMode.Platform_High_End_Circle)
                else:
                    self.movecontrol.servo(grab_mode=GrabMode.Platform_High_End)

        self.movecontrol.servo(grab_mode=GrabMode.Platform_High_Start)

    def grab_from_platform_medium(self) -> None:
        qr_code = self.camera.recognite_qr_info()
        if qr_code is None:
            self.movecontrol.bigarm(angle=110)
            self.movecontrol.forearm(angle=25)
            qr_code = self.camera.recognite_qr_info()
            if qr_code is not None:
                self.adjust_location()
            circle_previous = self.camera.detect_circles()
            self.movecontrol.servo(grab_mode=GrabMode.Platform_Medium_Start)

        if qr_code is not None:
            self.adjust_location()
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
                if circle or circle_previous:
                    pass
                    # self.movecontrol.servo(grab_mode=GrabMode.Platform_Medium_End_Circle)
                else:
                    self.movecontrol.servo(grab_mode=GrabMode.Platform_Medium_End)

        self.movecontrol.servo(grab_mode=GrabMode.Platform_Medium_Start)

    def go_to_ware_house(self) -> None:

        self.movecontrol.move_X(distance=-0.15)
        self.adjust_angle_by_lines()
        self.movecontrol.advance()
        self.movecontrol.move_Y(distance=-0.09)
        self.movecontrol.rotate(angle=-1440)
        self.movecontrol.move_X(distance=1.25)
        self.movecontrol.move_Y(distance=-0.3)
        self.movecontrol.highest()
        self.adjust_angle_by_lines()
        # self.movecontrol.move_Y(distance=-0.06)
        # self.adjust_angle_by_lines()
        # self.movecontrol.move_X(distance=0.04)

        # self.movecontrol.bigarm(angle=90)
        # self.movecontrol.forearm(angle=20)
        # self.movecontrol.servo(grab_mode=GrabMode.Put_Circle)
        # self.movecontrol.forearm(angle=20)
        self.movecontrol.advance()
        # self.movecontrol.move_X(distance=-0.1)

        self.movecontrol.rotate(angle=-720)
        self.movecontrol.move_X(distance=0.34)
        self.movecontrol.rotate(angle=-720)
        self.movecontrol.move_X(distance=-0.2)

    def put_down_items(self) -> None:

        self.movecontrol.backdoor(angle=30)
        self.movecontrol.frontdoor(angle=33)
        time.sleep(0.3)
        self.movecontrol.frontdoor(angle=0)
        time.sleep(0.3)
        self.movecontrol.frontdoor(angle=33)
        time.sleep(0.3)
        self.movecontrol.frontdoor(angle=66)
        time.sleep(2)
        self.movecontrol.backdoor(angle=0)

    def go_home(self) -> None:

        self.movecontrol.advance()
        self.movecontrol.move_X(distance=0.1)
        self.movecontrol.rotate(angle=-720)
        self.movecontrol.move_X(distance=2)
        self.movecontrol.rotate(angle=720)
        self.movecontrol.advance()
        self.movecontrol.move_X(distance=0.8)

    def adjust_location(self) -> None:
        x_value = (self.camera.location_x - self.camera.center_x) * 0.000185
        y_value = (self.camera.center_y - self.camera.location_y) * 0.000185

        my_logger.info(f'x:{x_value} y:{y_value}')

        x_value = (x_value * 100) / 100
        y_value = (y_value * 100) / 100

        my_logger.info(f'x:{x_value} y:{y_value}')

        self.movecontrol.move_X(distance=x_value)
        self.movecontrol.move_Y(distance=y_value)

    def adjust_angle_by_lines(self, x_move_1=None, x_move_2=None, reverse=False) -> None:
        if x_move_1 is not None:
            self.movecontrol.move_X(distance=x_move_1)
        _, angle = self.camera.recognize_lines_to_correct_location()
        angle = int(angle * 8)
        if reverse:
            angle = -angle
        self.movecontrol.rotate(angle=angle)
        if x_move_2 is not None:
            self.movecontrol.move_X(distance=x_move_2)

    def adjust_location_by_lines(self) -> None:
        distance, _ = self.camera.recognize_lines_to_correct_location()

        distance = (distance - self.camera.lines_central_x) * 0.001
        distance = (distance * 100) / 100

        self.movecontrol.move_X(distance=distance)

    def start(self) -> None:

        my_logger.info(f'进行初始化')
        self.init_to_start()
        my_logger.info(f'初始化完成， 等待下位机发送开始指令')
        self.movecontrol.wait_for_start_cmd()
        my_logger.info(f'接收到开始指令，开始执行任务')
        time.sleep(0.6)

        my_logger.info(f'-------------------前往大圆盘-------------------')

        self.go_to_big_diameter()
        my_logger.info(f'抵达大圆盘')

        my_logger.info(f'转向大圆盘')
        self.turn_to_big_diameter()

        my_logger.info(f'准备抓取小球')
        self.grab_ball_from_big_diameter()

        my_logger.info(f'转离大圆盘')
        self.turn_away_from_big_diameter_to_warehouse()
        self.put_down_items()
        self.go_back_to_diameter()

        my_logger.info(f'-------------------大圆盘任务结束-------------------')

        my_logger.info(f'-------------------前往颁奖台-------------------')

        self.go_to_platform()

        self.movecontrol.servo(grab_mode=GrabMode.Platform_Low_Start)

        my_logger.info(f'颁奖台-低，第一个物体')
        self.grab_from_platform_low()
        self.movecontrol.move_Y(distance=-0.1)
        self.movecontrol.move_X(distance=-0.03)

        my_logger.info(f'颁奖台-低，第二个物体')
        self.grab_from_platform_low()
        self.movecontrol.highest()

        self.adjust_angle_by_lines(x_move_1=-0.15, x_move_2=0.1)

        self.movecontrol.move_Y(distance=-0.16)

        self.movecontrol.servo(grab_mode=GrabMode.Platform_High_Start)
        my_logger.info(f'颁奖台-高，第一个物体')
        self.grab_from_platform_high()
        self.movecontrol.move_Y(distance=-0.09)
        self.movecontrol.move_X(distance=-0.02)
        my_logger.info(f'颁奖台-高，第二个物体')
        self.grab_from_platform_high()
        self.movecontrol.highest()

        self.adjust_angle_by_lines(x_move_1=-0.15, x_move_2=0.1)

        self.movecontrol.move_Y(distance=-0.09)

        self.movecontrol.servo(grab_mode=GrabMode.Platform_High_Start)
        my_logger.info(f'颁奖台-高，第三个物体')
        self.grab_from_platform_high()
        self.movecontrol.move_Y(distance=-0.09)
        my_logger.info(f'颁奖台-高，第四个物体')
        self.grab_from_platform_high()
        self.movecontrol.highest()

        self.adjust_angle_by_lines(x_move_1=-0.15, x_move_2=0.1)

        self.movecontrol.move_Y(distance=-0.11)

        self.movecontrol.servo(grab_mode=GrabMode.Platform_Medium_Start)
        my_logger.info(f'颁奖台-中，第一个物体')
        self.grab_from_platform_medium()
        self.movecontrol.move_Y(distance=-0.09)
        my_logger.info(f'颁奖台-中，第二个物体')
        self.grab_from_platform_medium()
        self.movecontrol.move_Y(distance=-0.09)
        self.movecontrol.highest()

        my_logger.info(f'-------------------颁奖台任务结束 -------------------')

        my_logger.info(f'-------------------前往仓储区-------------------')
        self.go_to_ware_house()
        my_logger.info(f'-------------------抵达仓储区-------------------')

        my_logger.info(f'-------------------准备投放物料-------------------')
        self.put_down_items()
        my_logger.info(f'-------------------物理投放结束-------------------')
        self.go_home()

    def run(self):
        self.camera.open()
        self.camera.debug = False
        self.movecontrol.highest()
        self.adjust_angle_by_lines()
        self.adjust_location_by_lines()


if __name__ == '__main__':
    stm_port = '/dev/ttyUSB0'
    stm_baudrate = 9600
    cam_index = 0

    control = MainControl(port=stm_port, baudrate=stm_baudrate, camera_index=cam_index)

    control.start()
    # control.run()
