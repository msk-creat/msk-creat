import cv2
import numpy as np

# 定义颜色范围（HSV颜色空间）
def get_color_ranges():
    return {
        'white': ([0, 0, 200], [180, 50, 255]),
        'red': ([0, 100, 100], [10, 255, 255]),
        'red2': ([160, 100, 100], [180, 255, 255]),  # 处理红色的不连续性
        'blue': ([100, 100, 100], [130, 255, 255]),
        'yellow': ([20, 100, 100], [40, 255, 255]),
        'green': ([40, 100, 100], [80, 255, 255]),
        'black': ([0, 0, 0], [180, 255, 50])
    }

# 检测图像中小球的颜色
def detect_ball_color(image):
    # 将图像转换为HSV颜色空间
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 获取颜色范围
    color_ranges = get_color_ranges()

    # 初始化颜色计数器
    color_counts = {color: 0 for color in color_ranges}

    # 遍历每个颜色范围
    for color, (lower, upper) in color_ranges.items():
        # 将 lower 和 upper 转换为 NumPy 数组
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)

        if color == 'red':
            # 处理红色的两个范围
            mask1 = cv2.inRange(hsv, np.array(color_ranges['red'][0], dtype=np.uint8), np.array(color_ranges['red'][1], dtype=np.uint8))
            mask2 = cv2.inRange(hsv, np.array(color_ranges['red2'][0], dtype=np.uint8), np.array(color_ranges['red2'][1], dtype=np.uint8))
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            mask = cv2.inRange(hsv, lower, upper)

        # 统计该颜色的像素数量
        color_counts[color] = np.sum(mask > 0)

    # 找到像素数量最多的颜色
    detected_color = max(color_counts, key=color_counts.get)
    return detected_color

# 读取图像
image_path = input("请输入图像路径: ")  # 用户输入图像路径
image = cv2.imread(image_path)

if image is None:
    print("错误：无法加载图像，请检查路径。")
else:
    # 调整图像大小以便更好地显示
    image = cv2.resize(image, (640, 480))

    # 检测小球颜色
    ball_color = detect_ball_color(image)
    print(f"检测到小球的颜色是: {ball_color}")

    # 显示图像
    cv2.imshow("Ball Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()