import matplotlib.pyplot as plt

# 数据
x = [1, 2, 3, 4, 5]
y = [2, 3, 5, 7, 11]

# 创建折线图
plt.plot(x, y)

# 添加标题和标签
plt.title('simple plot')
plt.xlabel('X axis')
plt.ylabel('Y axis')

# 显示图表
plt.show()