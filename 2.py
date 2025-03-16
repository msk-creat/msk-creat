import cv2
import numpy as np

# 读取图像
image = cv2.imread('4_cropped.jpg')
if image is None:
    raise FileNotFoundError("图像未找到，请检查路径")

# 转换为HSV颜色空间
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# 定义红色的HSV范围（红色分布在两个区域）
lower_red_1 = np.array([0, 100, 100])    # 红色范围 1 的下限
upper_red_1 = np.array([10, 255, 255])   # 红色范围 1 的上限
lower_red_2 = np.array([170, 100, 100])  # 红色范围 2 的下限
upper_red_2 = np.array([180, 255, 255])  # 红色范围 2 的上限

# 创建红色掩膜（两个范围）
mask1 = cv2.inRange(hsv, lower_red_1, upper_red_1)  # 红色范围 1
mask2 = cv2.inRange(hsv, lower_red_2, upper_red_2)  # 红色范围 2
mask = cv2.bitwise_or(mask1, mask2)  # 合并两个掩膜

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
    print(f"圆圈内的平均颜色 (BGR): {average_color}")

# 显示结果
cv2.imshow('Detected Red Balls', image)
cv2.waitKey(0)
cv2.destroyAllWindows()