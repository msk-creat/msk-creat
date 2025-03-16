import cv2
import numpy as np

# 定义常见颜色的 BGR 范围
COLOR_RANGES = {
    "红色": ([0, 0, 100], [50, 50, 255]),  # 红色范围
    "绿色": ([0, 100, 0], [50, 255, 50]),  # 绿色范围
    "蓝色": ([100, 0, 0], [255, 50, 50]),  # 蓝色范围
    "黄色": ([0, 100, 100], [60, 255, 255]),  # 黄色范围
    "橙色": ([0, 50, 100], [50, 150, 255]),  # 橙色范围
    "紫色": ([50, 0, 50], [150, 50, 150]),  # 紫色范围
    "白色": ([200, 200, 200], [255, 255, 255]),  # 白色范围
    "黑色": ([0, 0, 0], [50, 50, 50]),  # 黑色范围
}

def get_color_name(bgr_color):
    """
    根据 BGR 颜色值返回颜色名称
    """
    b, g, r = bgr_color
    for color_name, (lower, upper) in COLOR_RANGES.items():
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        if lower[0] <= b <= upper[0] and lower[1] <= g <= upper[1] and lower[2] <= r <= upper[2]:
            return color_name
    return "未知颜色"

# 读取图像
image = cv2.imread('0_cropped.jpg')
if image is None:
    raise FileNotFoundError("图像未找到，请检查路径")

# 转换为HSV颜色空间
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# 定义黄色的HSV范围（H: 20-30, S: 100-255, V: 100-255）
lower_yellow = np.array([20, 100, 100])
upper_yellow = np.array([30, 255, 255])

# 创建掩膜
mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

# 形态学处理：开运算（去噪）和闭运算（填充空洞）
kernel = np.ones((5,5), np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

# 查找轮廓
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 筛选圆形轮廓
min_area = 100  # 最小面积阈值
for cnt in contours:
    area = cv2.contourArea(cnt)
    if area < min_area:
        continue
    
    # 计算圆形度：4π*面积/周长²，越接近1越圆
    perimeter = cv2.arcLength(cnt, True)
    if perimeter == 0:
        continue
    circularity = 4 * np.pi * area / (perimeter ** 2)
    if circularity < 0.7:
        continue
    
    # 绘制最小外接圆
    (x, y), radius = cv2.minEnclosingCircle(cnt)
    center = (int(x), int(y))
    radius = int(radius)
    cv2.circle(image, center, radius, (0, 255, 0), 2)
    
    # 创建圆圈掩膜
    circle_mask = np.zeros_like(mask)
    cv2.circle(circle_mask, center, radius, 255, -1)  # 在掩膜上绘制白色圆圈
    
    # 提取圆圈内的区域
    circle_region = cv2.bitwise_and(image, image, mask=circle_mask)
    
    # 计算圆圈内的平均颜色
    average_color = cv2.mean(circle_region, mask=circle_mask)[:3]  # 只取 BGR 通道
    average_color = np.array(average_color, dtype=int)
    
    # 获取颜色名称
    color_name = get_color_name(average_color)
    print(f"圆圈内的平均颜色 (BGR): {average_color}, 颜色名称: {color_name}")

# 显示结果
cv2.imshow('Detected Balls', image)
cv2.waitKey(0)
cv2.destroyAllWindows()