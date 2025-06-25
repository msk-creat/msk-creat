"""
提供摄像头初始化、开启与释放以及对各种物体及颜色识别功能的模块

主要功能包括:
- 摄像头资源的调度
- 颜色识别
- 物体识别
"""
import math

import cv2
from pyzbar.pyzbar import decode
import numpy as np
from Config import my_logger, color_ranges, ColorSerial


class Camera:
    """
    用于摄像头初始化与图像识别的类

    这个类提供了初始化及释放摄像头，对各种物体与颜色进行识别的功能

    方法:
        __init__: 进行摄像头初始化
        open: 打开摄像头
        release: 释放摄像头资源
        detect_colors: 识别传入图像的颜色
        detect_colors_central: 仅当色块位于中心时才返回颜色
        recognite_qr_info: 识别二维码
    """

    def __init__(self, device: int = 0) -> None:
        """
        初始化摄像头

        Args:
            device(int): 摄像头序号

        Returns:
            None
        """
        self.center_y = None
        self.center_x = None

        self.location_y = None
        self.location_x = None

        self.frame_height = None
        self.frame_width = None

        my_logger.info(f'开始初始化摄像头')
        self.device_id = device
        self.cap = None
        self._debug = False

        my_logger.info(f'初始化摄像头成功！')

    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, value) -> None:
        if isinstance(value, bool):
            self._debug = value
        else:
            raise TypeError

    def open(self) -> None:
        """
        打开摄像头，类在初始化后不会自动打开摄像头，需要手动调用该方法打开摄像头

        Returns:
            None
        """
        if self.cap is None:
            my_logger.info(f"开启摄像头中......")
            self.cap = cv2.VideoCapture(self.device_id)
            if not self.cap.isOpened():
                raise RuntimeError("摄像头打开失败")
            my_logger.info(f"摄像头成功打开")
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.center_x = self.frame_width // 2
        self.center_y = self.frame_height // 2

    def release(self) -> None:
        """
        关闭摄像头，在程序结束时需要调用该方法释放摄像头

        Returns:
            None
        """
        my_logger.info(f'正在关闭摄像头')
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            my_logger.info(f'摄像头已关闭')
        else:
            my_logger.warning('摄像头未打开，不需释放')

    def detect_colors_bigmeter(self, min_area: int = 800, max_attempts: int = 5) -> str:
        detected_colors = None
        """
        识别颜色，调试模式下会显示摄像头画面并实时框选

        Args:
            min_area(int): 最小检测色块面积
            max_attempts(int): 每次执行此方法时识别次数

        Returns:
            color_name(str): 检测到的颜色名
        """
        attempts = 0
        while attempts < max_attempts:
            ret, frame = self.cap.read()  # 从摄像头读取一帧
            frame = frame[:, 160:]
            if not ret:
                my_logger.info('未读取到摄像头画面')
                continue

            detected_colors, frame = self._detect_color_common(frame, min_area)

            if self.debug:
                cv2.imshow("frame", frame)
                k = cv2.waitKey(1) & 0xFF
                if k == 27:
                    cv2.destroyWindow("frame")
                    break
            else:
                attempts += 1

        most_detected_color = max(detected_colors, key=detected_colors.get)
        return most_detected_color if detected_colors[most_detected_color] > 0 else None
        
    def detect_colors_platform(self, min_area: int = 800, max_attempts: int = 5) -> str:
        detected_colors = None
        """
        识别颜色，调试模式下会显示摄像头画面并实时框选

        Args:
            min_area(int): 最小检测色块面积
            max_attempts(int): 每次执行此方法时识别次数

        Returns:
            color_name(str): 检测到的颜色名
        """
        attempts = 0
        while attempts < max_attempts:
            ret, frame = self.cap.read()  # 从摄像头读取一帧
            frame = frame[:, :]
            if not ret:
                my_logger.info('未读取到摄像头画面')
                continue

            detected_colors, frame = self._detect_color_common(frame, min_area)

            if self.debug:
                cv2.imshow("frame", frame)
                k = cv2.waitKey(1) & 0xFF
                if k == 27:
                    cv2.destroyWindow("frame")
                    break
            else:
                attempts += 1

        most_detected_color = max(detected_colors, key=detected_colors.get)
        my_logger.info(f'recognize color: {most_detected_color}')
        return most_detected_color if detected_colors[most_detected_color] > 0 else None

    def _detect_color_common(self, frame, min_area, central_only=False, y_threshold=50):
        detected_colors = {'red': 0, 'blue': 0, 'yellow': 0}
        height, width, _ = frame.shape
        center_x, center_y = width // 2, height // 2  # 计算中心点坐标

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        for color_name, ranges in color_ranges.items():
            masks = [cv2.inRange(hsv, np.array(lower, dtype="uint8"), np.array(upper, dtype="uint8")) for (lower, upper)
                     in ranges]
            mask = cv2.bitwise_or(*masks) if len(masks) > 1 else masks[0]

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            max_area = min_area
            max_contour = None
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > max_area:
                    max_area = area
                    max_contour = contour

            if max_contour is not None and max_area >= min_area:
                x, y, w, h = cv2.boundingRect(max_contour)
                block_center_x, block_center_y = x + w // 2, y + h // 2  # 色块中心点
                # 只有当色块中心点的y坐标在中心点y坐标的阈值范围内时才计数
                if not central_only or (abs(block_center_y - center_y) < y_threshold):
                    detected_colors[color_name] += 1

                    self.location_x = block_center_x
                    self.location_y = block_center_y

                    if self.debug:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(frame, color_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return detected_colors, frame

    '''
    def detect_colors_central(self, min_area: int = 800, max_attempts: int = 5, y_threshold: int = 150) -> str:
        """
        识别颜色，调试模式下会显示摄像头画面并实时框选。
        只有当色块位于摄像头中心y轴上一定范围内时才返回值，否则返回 None。

        Args:
            min_area(int): 最小检测色块面积
            max_attempts(int): 每次执行此方法时识别次数
            y_threshold(int): 中心点y轴的允许偏移量

        Returns:
            color_name(str): 检测到的颜色名 或者 None 如果没有符合条件的色块
        """
        detected_colors = None
        max_attempts = 0
        while max_attempts < max_attempts:
            ret, frame = self.cap.read()  # 从摄像头读取一帧
            frame = frame[:, 80:]
            if not ret:
                my_logger.info('未读取到摄像头画面')
                continue

            detected_colors, frame = self._detect_color_common(frame, min_area, central_only=True,
                                                               y_threshold=y_threshold)

            if self.debug:
                cv2.imshow("frame", frame)
                k = cv2.waitKey(1) & 0xFF
                if k == 27:
                    cv2.destroyWindow("frame")
                    break
            else:
                max_attempts += 1

        most_detected_color = max(detected_colors, key=detected_colors.get)
        return most_detected_color if detected_colors[most_detected_color] > 0 else None
    '''

    def recognite_qr_info(self, data_len: int = -1, max_attempts: int = 10) -> str or None:
        """
        识别二维码

        Args:
            data_len(int): 预期中二维码包含的数据长度，-1作为默认值，表示不对数据长度作出限制
            max_attempts(int): 最大尝试次数
        Returns:
            ColorSerial: 二维码中的颜色信息
        """
        for _ in range(4):
            _, _ = self.cap.read()
        data = ""
        data_flag = False
        attempts = 0
        while attempts < max_attempts:
            _, frame = self.cap.read()
            for barcode in decode(frame):
                data_ = barcode.data.decode('utf-8')
                (x, y, w, h) = barcode.rect
                # 计算二维码中心点
                qr_center_x = x + w // 2
                qr_center_y = y + h // 2
                if self.debug:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
                    cv2.putText(
                        frame, data_, (x, y), cv2.FONT_HERSHEY_PLAIN, 1.0, (0, 0, 255)
                    )
                # 没有数据长度限制或数据长度符合预期
                if data_len == -1 or len(data_) == data_len:
                    data = data_
                    data_flag = True
                    # 更新二维码中心点位置
                    self.location_x = qr_center_x
                    self.location_y = qr_center_y
                    break

            if self.debug:
                cv2.imshow("frame", frame)
                k = cv2.waitKey(1) & 0xFF
                if k == 27:  # ESC键退出
                    cv2.destroyWindow("frame")
                    break
            if not self.debug:
                if data_flag:
                    break
                else:
                    attempts += 1
            
        my_logger.info(f'二维码内容: {data}')

        # 根据二维码内容返回相应的颜色
        if data == 'B':
            return 'blue'
        elif data == 'R':
            return 'red'
        else:
            return None

    def detect_circles(self, max_attempts: int = 1) -> bool:
        attempts = 0
        # 计算帧中心点
        frame_center = (self.frame_width / 2, self.frame_height / 2)

        for _ in range(3):
            _, _ = self.cap.read()

        while attempts < max_attempts:
            ret, frame = self.cap.read()
            frame = frame[:, 130:]
            if not ret:
                my_logger.error('无法读取视频流')
                return False

            # 转换为灰度图
            # img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # 中值滤波去噪
            dst_img = cv2.medianBlur(frame, 5)
            cimg = cv2.cvtColor(dst_img, cv2.COLOR_BGR2GRAY)
            # cimg = dst_img

            # 圆检测
            circles = cv2.HoughCircles(cimg, cv2.HOUGH_GRADIENT, 1, 100,
                                       param1=60, param2=60, minRadius=100, maxRadius=200)

            closest_circle = None
            min_distance = float('inf')

            if circles is not None:
                circles = np.uint16(np.around(circles))
                for i in circles[0, :]:
                    center = (i[0], i[1])
                    radius = i[2]

                    # 检查圆是否在中心区域内
                    if (frame_center[0] - self.frame_width * 0.25 < center[0] < frame_center[0] + self.frame_width * 0.25 and
                            frame_center[1] - self.frame_height * 0.25 < center[1] < frame_center[1] + self.frame_height * 0.25):

                        # 计算圆心到图像中心的距离
                        distance_to_center = np.sqrt(
                            (center[0] - frame_center[0]) ** 2 + (center[1] - frame_center[1]) ** 2)

                        # 如果当前圆比之前记录的更近，则更新最近的圆
                        if distance_to_center < min_distance:
                            min_distance = distance_to_center
                            closest_circle = (center, radius)

            if closest_circle is not None:
                center, radius = closest_circle
                self.location_x, self.location_y = center
                # 绘制圆心
                cv2.circle(frame, center, 1, (0, 100, 100), 3)
                # 绘制圆轮廓
                cv2.circle(frame, center, radius, (255, 0, 0), 3)
                # 添加文本"circle"
                cv2.putText(frame, "circle", (center[0] - 40, center[1] + 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            if self.debug:
                cv2.imshow("frame", frame)
                k = cv2.waitKey(1) & 0xFF
                if k == 27:  # 按ESC键退出
                    cv2.destroyWindow("frame")
                    break
            else:
                attempts += 1

            # 检查是否检测到圆
            if closest_circle is not None and not self.debug:
                my_logger.info(f'检测到圆环')
                return True

        my_logger.info(f'未检测到圆环')
        return False
        
    def detect_circles_platform_low(self, max_attempts: int = 1) -> bool:
        attempts = 0
        # 计算帧中心点
        frame_center = (self.frame_width / 2, self.frame_height / 2)

        for _ in range(4):
            _, _ = self.cap.read()

        while attempts < max_attempts:
            ret, frame = self.cap.read()
            frame = frame[:, 130:]
            if not ret:
                my_logger.error('无法读取视频流')
                return False

            # 转换为灰度图
            # img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # 中值滤波去噪
            dst_img = cv2.medianBlur(frame, 5)
            cimg = cv2.cvtColor(dst_img, cv2.COLOR_BGR2GRAY)
            # cimg = dst_img

            # 圆检测
            circles = cv2.HoughCircles(cimg, cv2.HOUGH_GRADIENT, 1, 100,
                                       param1=50, param2=50, minRadius=50, maxRadius=200)

            closest_circle = None
            min_distance = float('inf')

            if circles is not None:
                circles = np.uint16(np.around(circles))
                for i in circles[0, :]:
                    center = (i[0], i[1])
                    radius = i[2]

                    # 检查圆是否在中心区域内
                    if (frame_center[0] - self.frame_width * 0.25 < center[0] < frame_center[0] + self.frame_width * 0.25 and
                            frame_center[1] - self.frame_height * 0.25 < center[1] < frame_center[1] + self.frame_height * 0.25):

                        # 计算圆心到图像中心的距离
                        distance_to_center = np.sqrt(
                            (center[0] - frame_center[0]) ** 2 + (center[1] - frame_center[1]) ** 2)

                        # 如果当前圆比之前记录的更近，则更新最近的圆
                        if distance_to_center < min_distance:
                            min_distance = distance_to_center
                            closest_circle = (center, radius)

            if closest_circle is not None:
                center, radius = closest_circle
                self.location_x, self.location_y = center
                # 绘制圆心
                cv2.circle(frame, center, 1, (0, 100, 100), 3)
                # 绘制圆轮廓
                cv2.circle(frame, center, radius, (255, 0, 0), 3)
                # 添加文本"circle"
                cv2.putText(frame, "circle", (center[0] - 40, center[1] + 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            if self.debug:
                cv2.imshow("frame", frame)
                k = cv2.waitKey(1) & 0xFF
                if k == 27:  # 按ESC键退出
                    cv2.destroyWindow("frame")
                    break
            else:
                attempts += 1

            # 检查是否检测到圆
            if closest_circle is not None and not self.debug:
                my_logger.info(f'检测到圆环')
                return True

        my_logger.info(f'未检测到圆环')
        return False
        
    def detect_circles_from_high(self):
        # 从摄像头读取一帧
        ret, img = self.cap.read()

        if not ret:
            print("无法从摄像头读取图像，请检查摄像头是否连接")
            return False

        # 将图像转换为灰度图
        gray_img = cv2.cvtColor(img)

        # 二值化处理
        ret, binary_image = cv2.threshold(gray_img, 127, 255, cv2.THRESH_BINARY)

        # 定义腐蚀和膨胀的核
        kernel = np.ones((3, 3), np.uint8)

        # 腐蚀和膨胀操作
        eroded_image = cv2.erode(binary_image, kernel, iterations=2)
        dilated_image = cv2.dilate(eroded_image, kernel, iterations=8)

        # Canny边缘检测
        edges = cv2.Canny(dilated_image, 50, 150, apertureSize=3)

        # 霍夫变换检测圆
        circles = cv2.HoughCircles(edges, cv2.HOUGH_GRADIENT, dp=1, minDist=30,
                                   param1=50, param2=30, minRadius=100, maxRadius=200)

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")

            closest_circle = None
            min_distance = float('inf')

            for (x, y, r) in circles:
                distance_to_center = np.sqrt((x - img.shape[1] / 2) ** 2 + (y - img.shape[0] / 2) ** 2)

                if distance_to_center < min_distance:
                    min_distance = distance_to_center
                    closest_circle = (x, y, r)

            if closest_circle is not None:
                x, y, r = closest_circle
                self.location_x, self.location_y = x, y

                # 在原始图像上绘制圆周和圆心
                cv2.circle(img, (x, y), r, (0, 255, 0), 2)
                cv2.circle(img, (x, y), 2, (0, 0, 255), 3)

                if self.debug:
                    cv2.imshow('Detected Circles', img)
                    cv2.waitKey(0)

                return True
            else:
                print("没有找到合适的圆")
        else:
            print("没有检测到圆")

        return False

    def recognize_lines_to_correct_location(self, max_attempts: int = 5) -> float or None:
        attempts = 0

        for _ in range(4):
            _, _ = self.cap.read()

        while attempts < max_attempts:
            ret, frame = self.cap.read()
            frame = frame[:, 250:450]
            
            (h, w, c) = frame.shape
            self.lines_central_x = w // 2
            self.lines_central_y = h // 2

            ret, binary_image = cv2.threshold(frame, 210, 255, cv2.THRESH_BINARY)

            # 定义一个5x5的核
            kernel = np.ones((5, 5), np.uint8)

            # 对图像进行腐蚀操作
            eroded_image = cv2.erode(binary_image, kernel, iterations=2)
            dilated_image = cv2.dilate(eroded_image, kernel, iterations=2)

            # 边缘检测
            edges = cv2.Canny(dilated_image, 50, 150, apertureSize=3)

            # 使用Hough变换检测直线
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 150)

            horizontal_angle_threshold = 2
            all_points = []

            if lines is not None:
                for line in lines:
                    rho, theta = line[0]
                    a = np.cos(theta)
                    b = np.sin(theta)
                    x0 = a * rho
                    y0 = b * rho
                    x1 = int(x0 + 1000 * (-b))
                    y1 = int(y0 + 1000 * (a))
                    x2 = int(x0 - 1000 * (-b))
                    y2 = int(y0 - 1000 * (a))

                    dx = x2 - x1
                    dy = y2 - y1
                    if dx != 0:
                        angle = math.degrees(math.atan(dy / dx))
                    else:
                        angle = 90.0

                    if horizontal_angle_threshold < abs(angle) < (180 - horizontal_angle_threshold):
                        all_points.append((x1, y1))
                        all_points.append((x2, y2))

            # 如果有足够的点来进行拟合
            if len(all_points) > 1:
                points = np.array(all_points)
                vx, vy, x0, y0 = cv2.fitLine(points, cv2.DIST_L2, 0, 0.01, 0.01)

                if vy != 0:
                    fitted_line_angle = math.degrees(math.atan(vx / vy))
                else:
                    fitted_line_angle = 90.0

                # 获取两个端点
                lefty = int((-x0 * vy / vx) + y0)
                righty = int(((frame.shape[1] - x0) * vy / vx) + y0)

                bottom_y = frame.shape[0] - 1
                bottom_x = int((bottom_y - y0) * vx / vy + x0)

                #lefty = max(0, min(lefty, frame.shape[0] - 1))
                #righty = max(0, min(righty, frame.shape[0] - 1))
                bottom_x = max(0, min(bottom_x, frame.shape[1] - 1))

                if self.debug:
                    cv2.line(frame, (frame.shape[1] - 1, righty), (0, lefty), (0, 0, 255), 2)
                    cv2.imshow('test', frame)
                    cv2.waitKey(0)
                elif fitted_line_angle and bottom_x:
                    return bottom_x, fitted_line_angle
                else:
                    attempts += 1

        return bottom_x, fitted_line_angle


if __name__ == '__main__':
    camera = Camera(device=0)
    camera.debug = True
    camera.open()

    while True:
        result = False

        choose = input('请选择识别模式(C[color]/T[central]/Q[qrcode]/R[circle]/A[angle]/L[location]/D[debug]/E[exit]: ')
        if choose == 'C' or choose == 'c':
            result = camera.detect_colors_bigmeter()

        elif choose == 'T' or choose == 't':
            result = camera.detect_colors_bigmeter()

        elif choose == 'Q' or choose == 'q':
            result = camera.recognite_qr_info()
            print(result)
            continue

        elif choose == 'R' or choose == 'r':
            result = camera.detect_circles()
            print(result)
            continue

        elif choose == 'A' or choose == 'a':
            horizontal_angle, vertical_angle = camera.calculate_angle_by_cross()
            print(horizontal_angle, vertical_angle)
            continue

        elif choose == 'L' or choose == 'l':
            x, angle = camera.recognize_lines_to_correct_location()
            print(x, angle)
            continue

        elif choose == 'D' or choose == 'd':
            if camera.debug:
                camera.debug = False
                my_logger.info(f"已关闭debug模式")
                continue
            else:
                camera.debug = True
                my_logger.info(f"已开启debug模式")
                continue

        elif choose == 'E' or choose == 'e':
            break

        else:
            print('请正确选择模式')
            continue

        if result:
            print(f'识别到的颜色为: {result}')

        else:
            print(f'未识别成功')

    camera.release()
