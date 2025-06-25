"""
提供串口初始化与通信以及控制小车运动功能的模块

主要功能包括:
- 串口初始化与通信
- 控制小车运动模式
- 控制舵机运动模式
"""

import time
import serial

from Config import my_logger, MoveMode, GrabMode
from modules.Detection import Camera


class MoveControl:
    """
    用于串口通信及小车运动控制的类

    这个类提供了串口初始化，控制小车运动及控制舵机模式等功能

    方法:
        __init__: 进行串口初始化
        __wait_for_action_done: 等待下位机完成动作
        wait_for_start_cmd: 等待下位机发送启动指令
        __send_serial_msg: 向下位机发送各模式指令
        move_X: 控制小车前后运动
        move_Y: 控制小车左右运动
        move_Topleft_Lowerright: 控制小车左上-右下运动
        move_Topright_Lowerleft: 控制小车右上-左下运动
        rotate: 控制小车旋转
        calibration: 控制小车校准
        servo: 控制小车舵机
        bigarm: 控制大臂
        forearm: 控制小臂
        frontpaws: 控制前爪
        hindpaws: 控制后爪
        frontdoor: 控制前门
        backdoor: 控制后门
        cirque: 控制圆环
        clear_buffer: 清空缓存区
    """

    def __init__(self, port: str, baudrate: int) -> None:
        """
        串口初始化

        Args:
            port(str): 设备端口号
            baudrate(int): 波特率

        Returns:
            None
        """
        my_logger.info(f'正在初始化串口')
        try:
            self._serial = serial.Serial(port, baudrate)
        except serial.SerialException as e:
            my_logger.error(e)

        if self._serial.is_open:
            my_logger.info("串口成功初始化")
        else:
            raise RuntimeError("串口未能成功初始化")

        self.buffer_format = [0xFF, 0x00, 0x00, 0xFE]

    def __wait_for_action_done(self) -> None:
        """
        上位机向下位机发送动作指令后，下位机应该在动作执行结束后向上位机反馈动作结束的命令
        此方法用于等待下位机的结束指令[0xFF, 0x01, 0xFE]

        Returns:
            None
        """
        while True:
            head = ord(self._serial.read(1))
            if head == 0xFF:
                data = ord(self._serial.read(1))
                if data == 0x01:
                    self._serial.read(1)
                    self._serial.reset_input_buffer()
                    break

    def wait_for_start_cmd(self) -> None:
        """
        等待下位机的开启指令，指令设置为[0xFF, 0x10, 0xFE]

        Returns:
            None: 函数结束代表受到了指令
        """
        while True:
            head = ord(self._serial.read(1))
            if head == 0xFF:
                data = ord(self._serial.read(1))
                if data == 0x10:
                    self._serial.read(1)
                    self._serial.reset_input_buffer()
                    my_logger.info(f"接收到了下位机的启动消息！")
                    break

    def __send_serial_msg(self, mode: MoveMode, grab_mode: GrabMode = None, distance: float = None,
                          rotation_angle: int = None) -> None:
        """
        发送串口指令给下位机，在被调用时会先对输入的数据进行检查；发送完指令后调用self.__wait_for_action_done()等待下位机反馈

        Args:
            mode (MoveMode): 运动模式，详情见Config.py
            grab_mode(GrabMode): 舵机模式，详情见Config.py
            distance (float): 运动距离，单位为mm
            rotation_angle (int): 旋转角度，单位为度
        Returns:
            None: 函数结束代表发送成功并且收到了下位机的执行结束消息
        """
        buffer = []
        log_msg = f''

        # 对输入数据进行检查
        if mode in [MoveMode.Forward, MoveMode.Backward, MoveMode.Leftward, MoveMode.Rightward, MoveMode.Topleft,
                    MoveMode.Topright, MoveMode.Lowerleft, MoveMode.Lowerright]:
            if distance is None:
                raise ValueError
            if -32.768 <= distance <= 32.767:
                pass
            else:
                my_logger.warning(f"距离设置范围过大，目前支持[-32.768, 32.767] m。截取距离的低十六位")

        elif mode in [MoveMode.Turnleft, MoveMode.Turnright]:
            if rotation_angle is None:
                raise ValueError
            rotation_angle = abs(rotation_angle)

        elif mode in [MoveMode.Calibration, MoveMode.Servo, MoveMode.Highest, MoveMode.Advance]:
            pass

        elif mode in [MoveMode.Bigarm, MoveMode.Forearm, MoveMode.Frontpaws, MoveMode.Hindpaws, MoveMode.Frontdoor,
                      MoveMode.Backdoor, MoveMode.Cirque]:
            if rotation_angle is None:
                raise ValueError
            rotation_angle = abs(rotation_angle)
            if rotation_angle > 180:
                rotation_angle %= 180
                my_logger.warning(f"舵机模式下，输入的角度不在[-180，180]之间，将取值为{rotation_angle}")

        else:
            my_logger.error(f"无法识别的Move模式：{mode}")

        if mode in [MoveMode.Forward, MoveMode.Backward, MoveMode.Leftward, MoveMode.Rightward, MoveMode.Topleft,
                    MoveMode.Topright, MoveMode.Lowerleft, MoveMode.Lowerright]:

            dis_mm = int(distance * 1000)
            high_byte: int = dis_mm // 256
            low_byte = dis_mm % 256

            buffer = [0xFF, mode.value, high_byte, low_byte, 0xFE]

            log_msg = f'动作模式为{mode.name}，使用米作为单位，原始移动距离为{distance}m。'

        elif mode in [MoveMode.Turnleft, MoveMode.Turnright]:
            rotation_angle_ = abs(int(rotation_angle))
            high_byte = rotation_angle // 256
            low_byte = rotation_angle % 256

            buffer = [0xFF, mode.value, high_byte, low_byte, 0xFE]
            log_msg = f'动作模式为旋转，使用度作为单位，原始输入为{rotation_angle_}度'

        elif mode == MoveMode.Calibration:
            buffer = [0xFF, mode.value, 30, 2, 0xFE]
            log_msg = f'动作模式为校准'

        elif mode == MoveMode.Servo:
            my_logger.info(f'执行{grab_mode.name}')
            if grab_mode == GrabMode.Big_Diameter:
                time.sleep(0.04)
                self.frontpaws(angle=70)
                time.sleep(0.1)
                self.frontpaws(angle=10)
            elif grab_mode == GrabMode.Small_Diameter:
                pass
            elif grab_mode == GrabMode.Platform_Low_Start:
                self.bigarm(angle=110)
                self.forearm(angle=58)
                self.hindpaws(angle=0)
                self.frontpaws(angle=0)
                self.cirque(angle=0)
            elif grab_mode == GrabMode.Platform_Low_End:
                self.hindpaws(angle=64)
                self.frontpaws(angle=46)
                self.forearm(angle=40)
                self.bigarm(angle=30)
                time.sleep(0.3)
                self.hindpaws(angle=0)
                self.frontpaws(angle=0)
            elif grab_mode == GrabMode.Platform_Low_End_Circle:
                self.hindpaws(angle=57)
                self.frontpaws(angle=46)
                self.cirque(angle=67)
                self.forearm(angle=20)
                self.forearm(angle=35)
                self.bigarm(angle=44)
                time.sleep(0.3)
                self.hindpaws(angle=0)
                self.frontpaws(angle=0)
                self.frontpaws(angle=60)
            elif grab_mode == GrabMode.Platform_High_Start:
                self.bigarm(angle=105)
                self.forearm(angle=21)
                self.hindpaws(angle=0)
                self.frontpaws(angle=0)
                self.cirque(angle=0)
            elif grab_mode == GrabMode.Platform_High_End:
                self.hindpaws(angle=64)
                self.frontpaws(angle=46)
                self.forearm(angle=40)
                self.bigarm(angle=30)
                time.sleep(0.3)
                self.hindpaws(angle=0)
                self.frontpaws(angle=0)
                self.frontpaws(angle=60)
            elif grab_mode == GrabMode.Platform_High_End_Circle:
                self.hindpaws(angle=57)
                self.frontpaws(angle=46)
                self.cirque(angle=67)
                self.forearm(angle=20)
                self.bigarm(angle=44)
                self.forearm(angle=35)
                time.sleep(0.3)
                self.hindpaws(angle=0)
                self.frontpaws(angle=0)
                self.frontpaws(angle=60)
    
            elif grab_mode == GrabMode.Platform_Medium_Start:
                self.bigarm(angle=110)
                self.forearm(angle=40)
                self.hindpaws(angle=0)
                self.frontpaws(angle=0)
                self.cirque(angle=0)
            elif grab_mode == GrabMode.Platform_Medium_End:
                self.hindpaws(angle=64)
                self.frontpaws(angle=46)
                self.forearm(angle=40)
                self.bigarm(angle=30)
                time.sleep(0.3)
                self.hindpaws(angle=0)
                self.frontpaws(angle=0)
            elif grab_mode == GrabMode.Platform_Medium_End_Circle:
                self.hindpaws(angle=57)
                self.frontpaws(angle=44)
                self.cirque(angle=67)
                self.forearm(angle=20)
                self.forearm(angle=35)
                self.bigarm(angle=44)
                time.sleep(0.3)
                self.hindpaws(angle=0)
                self.frontpaws(angle=0)
                self.frontpaws(angle=60)
            elif grab_mode == GrabMode.Put_Circle:
                self.cirque(angle=67)
                self.forearm(angle=48)
                self.bigarm(angle=46)
                self.hindpaws(angle=57)
                self.frontpaws(angle=46)
                self.forearm(angle=20)
                self.bigarm(angle=90)
                self.forearm(angle=25)
                self.bigarm(angle=100)
                time.sleep(0.4)
                self.hindpaws(angle=0)
                self.frontpaws(angle=0)
                self.cirque(angle=0)

        elif mode in [MoveMode.Bigarm, MoveMode.Forearm, MoveMode.Frontpaws, MoveMode.Hindpaws, MoveMode.Frontdoor,
                      MoveMode.Backdoor, MoveMode.Cirque]:
            rotation_angle_ = abs(int(rotation_angle))

            buffer = [0xFF, mode.value, 0, rotation_angle_, 0xFE]
            log_msg = f'{mode.name}参数为{rotation_angle_}'

        elif mode == MoveMode.Highest:
            my_logger.info(f'升至最高点')
            self.bigarm(angle=90)
            self.forearm(angle=20)
            self.cirque(angle=0)
            self.frontpaws(angle=0)
            self.hindpaws(angle=0)

        elif mode == MoveMode.Advance:
            my_logger.info(f'init')
            self.bigarm(angle=40)
            self.forearm(angle=40)

        else:
            raise ValueError(f'无法识别的模式{mode}')

        if mode not in [MoveMode.Servo, MoveMode.Highest, MoveMode.Advance]:
            send_num = self._serial.write(bytes(buffer))
            my_logger.debug(f"向下位机发送了{send_num}个字节的数据，数据内容为{buffer}。" + log_msg)
            self.__wait_for_action_done()
            my_logger.info(f"接收到串口消息，下位机动作执行完毕")

    def move_X(self, distance: float) -> None:
        """
        控制小车前后方向上的移动

        Args:
            distance: 移动距离，单位为米，范围为[-32, 32]m
        Returns:
            None: 延时程序，函数返回时代表动作完成
        """
        if distance >= 0:
            self.__send_serial_msg(mode=MoveMode.Forward, distance=distance)
            my_logger.info(f"向前{distance}m")
        else:
            distance = abs(distance)
            self.__send_serial_msg(mode=MoveMode.Backward, distance=distance)
            my_logger.info(f"后退{distance}m")

    def move_Y(self, distance: float) -> None:
        """
        控制小车左右方向上的移动

        Args:
            distance: 移动距离，单位为米，范围为[-32, 32]m
        Returns:
            None: 延时程序，函数返回时代表动作完成
        """
        if distance >= 0:
            self.__send_serial_msg(mode=MoveMode.Leftward, distance=distance)
            my_logger.info(f"向左{distance}m")
        else:
            distance = abs(distance)
            self.__send_serial_msg(mode=MoveMode.Rightward, distance=distance)
            my_logger.info(f"向右{distance}m")

    def move_Topleft_Lowerright(self, distance: float) -> None:
        """
        控制小车左上-右下方向上的移动

        Args:
            distance: 移动距离，单位为米，范围为[-32, 32]m
        Returns:
            None: 延时程序，函数返回时代表动作完成
        """
        if distance >= 0:
            self.__send_serial_msg(mode=MoveMode.Topleft, distance=distance)
            my_logger.info(f"向左上{distance}m")
        else:
            distance = abs(distance)
            self.__send_serial_msg(mode=MoveMode.Lowerright, distance=distance)
            my_logger.info(f"向右下{distance}m")

    def move_Topright_Lowerleft(self, distance: float) -> None:
        """
        控制小车右上-左下方向上的移动

        Args:
            distance: 移动距离，单位为米，范围为[-32, 32]m
        Returns:
            None: 延时程序，函数返回时代表动作完成
        """
        if distance >= 0:
            self.__send_serial_msg(mode=MoveMode.Topright, distance=distance)
            my_logger.info(f"向右上{distance}m")
        else:
            distance = abs(distance)
            self.__send_serial_msg(mode=MoveMode.Lowerleft, distance=distance)
            my_logger.info(f"向左下{distance}m")

    def rotate(self, angle: int) -> None:
        """
        控制小车底盘旋转

        Args:
            angle (int): 角度值，单位为度，范围为[-360, 360]，逆时针方向为正
        Returns:
            None: 延时程序，函数返回时代表动作完成
        """
        if angle >= 0:
            self.__send_serial_msg(mode=MoveMode.Turnleft, rotation_angle=angle)
            my_logger.info(f"向左转{angle}m")
        else:
            angle = abs(angle)
            self.__send_serial_msg(mode=MoveMode.Turnright, rotation_angle=angle)
            my_logger.info(f"向右转 {angle}m")

    def calibration(self) -> None:
        """
        小车校准

        Returns:
            None: 延时程序，函数返回时代表动作完成
        """
        self.__send_serial_msg(mode=MoveMode.Calibration)
        my_logger.info(f"进行校准")

    def servo(self, grab_mode: GrabMode) -> None:
        """
        控制舵机

        Args:
            grab_mode(GrabMode): 舵机模式
        Returns:
            None: 延时程序，函数返回时代表动作完成
        """
        self.__send_serial_msg(mode=MoveMode.Servo, grab_mode=grab_mode)
        my_logger.info(f"选取的舵机模式为{grab_mode.name}")

    def bigarm(self, angle: int) -> None:
        """
        控制大臂

        Args:
            angle: 角度，范围[0, 180]
        Returns:
            None: 延时程序，函数返回时代表动作完成
        """
        self.__send_serial_msg(mode=MoveMode.Bigarm, rotation_angle=angle)
        my_logger.info(f"大臂角度: {angle}°")
        time.sleep(0.4)
        pass

    def forearm(self, angle: int) -> None:
        """
        控制小臂

        Args:
            angle: 角度，范围[0, 180]
        Returns:
            None: 延时程序，函数返回时代表动作完成
        """
        self.__send_serial_msg(mode=MoveMode.Forearm, rotation_angle=angle)
        my_logger.info(f"小臂角度: {angle}°")
        time.sleep(0.4)

    def frontpaws(self, angle: int) -> None:
        """
        控制前爪

        Args:
            angle: 角度，范围[0, 180]
        Returns:
            None: 延时程序，函数返回时代表动作完成
        """
        self.__send_serial_msg(mode=MoveMode.Frontpaws, rotation_angle=angle)
        my_logger.info(f"前爪角度: {angle}°")
        time.sleep(0.2)

    def hindpaws(self, angle: int) -> None:
        """
        控制后爪

        Args:
            angle: 角度，范围[0, 180]
        Returns:
            None: 延时程序，函数返回时代表动作完成
        """
        self.__send_serial_msg(mode=MoveMode.Hindpaws, rotation_angle=angle)
        my_logger.info(f"后爪角度: {angle}°")
        time.sleep(0.4)

    def frontdoor(self, angle: int) -> None:
        """
        控制前门

        Args:
            angle: 角度，范围[0, 180]
        Returns:
            None: 延时程序，函数返回时代表动作完成
        """
        self.__send_serial_msg(mode=MoveMode.Frontdoor, rotation_angle=angle)
        my_logger.info(f"前门角度: {angle}°")

    def backdoor(self, angle: int) -> None:
        """
        控制小臂

        Args:
            angle: 角度，范围[0, 180]
        Returns:
            None: 延时程序，函数返回时代表动作完成
        """
        self.__send_serial_msg(mode=MoveMode.Backdoor, rotation_angle=angle)
        my_logger.info(f"后门角度: {angle}°")
        time.sleep(0.4)

    def cirque(self, angle: int) -> None:
        """
        控制圆环

        Args:
            angle: 角度，范围[0, 180]
        Returns:
            None: 延时程序，函数返回时代表动作完成
        """
        self.__send_serial_msg(mode=MoveMode.Cirque, rotation_angle=angle)
        my_logger.info(f"圆环角度: {angle}°")
        time.sleep(0.4)

    def highest(self) -> None:
        self.__send_serial_msg(mode=MoveMode.Highest)
        return None
        
    def advance(self) -> None:
        self.__send_serial_msg(mode=MoveMode.Advance)

    def clear_buffer(self) -> None:
        """
        清空缓存区

        Returns:
            None
        """
        self._serial.reset_input_buffer()
        self._serial.reset_output_buffer()


if __name__ == '__main__':

    stm_port = '/dev/ttyUSB0'
    stm_baudrate = 9600

    control = MoveControl(port=stm_port, baudrate=stm_baudrate)

    while True:
        result = False
        choose = input('请选择模式(M[move]/S[servo]/G/[grab]/E[exit]): ')
        if choose == 'M' or choose == 'm':
            while True:
                choose = input('请选择模式(X[x_move]/Y[y_move]/Tl-LR[topleft_lowerright]/TR-LL[topright_lowerleft]/'
                               'R[rotate]/C[calibration]/S[servo]/E[exit]): ')
                if choose == 'X' or choose == 'x':
                    distance = float(input('请输入距离: '))
                    control.move_X(distance=distance)

                elif choose == 'Y' or choose == 'y':
                    distance = float(input('请输入距离: '))
                    control.move_Y(distance=distance)

                elif choose == 'TL' or choose == 'tl' or choose == 'LR' or choose == 'lr':
                    distance = float(input('请输入距离: '))
                    control.move_Topleft_Lowerright(distance=distance)

                elif choose == 'TR' or choose == 'tr' or choose == 'LL' or choose == 'll':
                    distance = float(input('请输入距离: '))
                    control.move_Topright_Lowerleft(distance=distance)

                elif choose == 'R' or choose == 'r':
                    angle = int(input('请输入角度: '))
                    control.rotate(angle=angle)

                elif choose == 'C' or choose == 'c':
                    print('进行校准')

                elif choose == 'S' or choose == 's':
                    print('尚未支持舵机模式')

                elif choose == 'E' or choose == 'e':
                    print('已退出运动选择模式')
                    break

                else:
                    print('请正确选择模式')

        elif choose == 'S' or choose == 's':
            while True:
                choose = input('请选择模式(B[bigarm]/F[forearm]/P[frontpaws]/H[hindpaws]/D[frontdoor]/K[backdoor]/'
                               'C[cirque]/N[conbinations]/E[exit]: ')

                if choose == 'B' or choose == 'b':
                    angle = int(input('请输入角度: '))
                    control.bigarm(angle=angle)

                elif choose == 'F' or choose == 'f':
                    angle = int(input('请输入角度: '))
                    control.forearm(angle=angle)

                elif choose == 'P' or choose == 'p':
                    angle = int(input('请输入角度: '))
                    control.frontpaws(angle=angle)

                elif choose == 'H' or choose == 'h':
                    angle = int(input('请输入角度: '))
                    control.hindpaws(angle=angle)

                elif choose == 'D' or choose == 'd':
                    angle = int(input('请输入角度: '))
                    control.frontdoor(angle=angle)

                elif choose == 'K' or choose == 'k':
                    angle = int(input('请输入角度: '))
                    control.backdoor(angle=angle)

                elif choose == 'C' or choose == 'c':
                    angle = int(input('请输入角度: '))
                    control.cirque(angle=angle)

                elif choose == 'E' or choose == 'e':
                    print('已退出舵机调试模式')
                    break
                elif choose == 'N' or choose == 'n':
                    angle = list(map(int, input('请输入7个参数[bigarm/forearm/frontpaws/hindpaws/frontdoor/backdoor/cirque]\n').split()))
                    control.bigarm(angle=angle[0])
                    control.forearm(angle=angle[1])
                    control.frontpaws(angle=angle[2])
                    control.hindpaws(angle=angle[3])
                    control.frontdoor(angle=angle[4])
                    control.backdoor(angle=angle[5])
                    control.cirque(angle=angle[6])

                else:
                    print('请正确选择模式')

        elif choose == 'G' or choose == 'g':
            camera = Camera()
            camera.open()
            while True:
                control.highest()
                control.frontpaws(angle=0)
                control.hindpaws(angle=0)
                circle = None
                qr_code = None
                choose = input('请选择模式(B[big_diameter]/M[medium]/H[high]/L[low]/R[release]/E[exit]): ')
                if choose == 'B' or choose == 'b':
                    control.servo(grab_mode=GrabMode.Big_Diameter)

                elif choose == 'M' or choose == 'm':
                    control.servo(grab_mode=GrabMode.Platform_Medium_Start)

                    circle = camera.detect_circles()
                    if circle:
                        control.servo(grab_mode=GrabMode.Platform_Medium_End_Circle)

                    else:
                        control.servo(grab_mode=GrabMode.Platform_Medium_End)

                elif choose == 'H' or choose == 'h':
                    control.servo(grab_mode=GrabMode.Platform_High_Start)

                    circle = camera.detect_circles()
                    if circle:
                        control.servo(grab_mode=GrabMode.Platform_High_End_Circle)

                    else:
                        control.servo(grab_mode=GrabMode.Platform_High_End)

                elif choose == 'L' or choose == 'l':
                    control.servo(grab_mode=GrabMode.Platform_Low_Start)

                    circle = camera.detect_circles()
                    if circle:
                        control.servo(grab_mode=GrabMode.Platform_Low_End_Circle)

                    else:
                        control.servo(grab_mode=GrabMode.Platform_Low_End)

                elif choose == 'R' or choose == 'r':
                    control.backdoor(angle=50)
                    time.sleep(2)
                    control.backdoor(angle=0)

                elif choose == 'E' or choose == 'e':
                    print('已退出运动选择模式')
                    break

                else:
                    print('请正确选择模式')

        elif choose == 'E' or choose == 'e':
            print('已退出')
            break

        else:
            print('请正确选择模式')
