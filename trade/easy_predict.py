# 导入必要的库
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
import os

# 导入字体管理器
from matplotlib import font_manager

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # 或者使用其他支持中文的字体
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 获取当前脚本所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建数据文件的路径
data_file_path = os.path.join(current_dir, 'data', '000016.SZ.csv')

# 读取数据
data = pd.read_csv(data_file_path)

# 选择收盘价作为预测目标，并将其转换为numpy数组
data = data['Close'].values
data = data.reshape(-1, 1)

# 初始化MinMaxScaler，用于将数据缩放到0-1范围内
scaler = MinMaxScaler(feature_range=(0, 1)) 
scaled_data = scaler.fit_transform(data)

# 将数据集分为训练集（80%）和测试集（20%）
train_size = int(len(scaled_data) * 0.8)
train_data = scaled_data[:train_size]
test_data = scaled_data[train_size-10 :] 

# 定义函数用于创建时间序列数据集
def create_dataset(data, time_step=1):
    X, Y = [], []
    for i in range(len(data)-time_step):
        a = data[i:(i+time_step), 0]  # 输入序列
        X.append(a)
        Y.append(data[i + time_step, 0])  # 目标值
    return np.array(X), np.array(Y)

# 设置时间步长为10，并创建训练集和测试集
time_step = 10
X_train, y_train = create_dataset(train_data, time_step)
X_test, y_test = create_dataset(test_data, time_step)

# 调整输入数据形状以适应LSTM层的输入要求
X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

# 构建LSTM模型
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(time_step, 1)))  # 第一个LSTM层，返回序列
model.add(LSTM(50, return_sequences=False))  # 第二个LSTM层，不返回序列
model.add(Dense(25))  # 全连接层
model.add(Dense(1))  # 输出层

# 编译模型，使用Adam优化器和均方误差损失函数
model.compile(optimizer='adam', loss='mean_squared_error')

# 训练模型
model.fit(X_train, y_train, batch_size=1, epochs=1)

# 使用模型进行预测
train_predict = model.predict(X_train)
test_predict = model.predict(X_test)

# 将预测结果反向转换回原始比例
train_predict = scaler.inverse_transform(train_predict)
test_predict = scaler.inverse_transform(test_predict)

# 将实际数据也反向转换回原始比例
y_train = scaler.inverse_transform([y_train])
y_test = scaler.inverse_transform([y_test])

# 计算并打印每日价格变化、实际价格和预测价格
原始数据 = scaler.inverse_transform(scaled_data)
训练集预测起始索引 = time_step
测试集预测起始索引 = len(train_predict) + time_step

for i in range(1, len(原始数据)):
    实际价格 = 原始数据[i][0]
    前一天价格 = 原始数据[i-1][0]
    价格变化 = 实际价格 - 前一天价格
    百分比变化 = (价格变化 / 前一天价格) * 100
    
    预测价格 = None
    if 训练集预测起始索引 <= i < 训练集预测起始索引 + len(train_predict):
        预测价格 = train_predict[i - 训练集预测起始索引][0]
    elif i >= 测试集预测起始索引 and i - 测试集预测起始索引 < len(test_predict):
        预测价格 = test_predict[i - 测试集预测起始索引][0]
    
    输出信息 = f"第 {i} 天: 实际价格 = {实际价格:.2f}, 价格变化 = {价格变化:.2f}, 百分比变化 = {百分比变化:.2f}%"
    if 预测价格 is not None:
        输出信息 += f", 预测价格 = {预测价格:.2f}"
    
    print(输出信息)
    

# 绘制结果图
# 创建一个新的图形，设置大小为10x6英寸
plt.figure(figsize=(10,6))

# 绘制实际股价
plt.plot(scaler.inverse_transform(scaled_data), label='实际股价')
# scaler.inverse_transform(scaled_data) 将缩放后的数据转换回原始比例
# 这里绘制了整个时间序列的实际股价

# 绘制训练集预测结果
plt.plot(range(time_step, len(train_predict)+time_step), train_predict, label='训练集预测')
# range(time_step, len(train_predict)+time_step) 创建了一个索引范围
# 这个范围从time_step开始，因为前time_step个数据点用于预测第一个值
# len(train_predict)+time_step 是训练集预测的结束位置

# 绘制测试集预测结果
plt.plot(range(len(train_predict)+time_step, len(scaled_data)), test_predict, label='测试集预测')
# 这个范围从训练集预测结束的位置开始，一直到数据集的末尾

# 添加图例
plt.legend()

# 设置图表标题
plt.title('股价预测结果')

# 设置x轴标签
plt.xlabel('时间')

# 设置y轴标签
plt.ylabel('股价')

# 显示图形
plt.show()