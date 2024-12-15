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
# 获取当前脚本所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建数据文件夹的路径
data_folder_path = os.path.join(current_dir, 'data')

# 读取多只股票的数据
股票数据 = {}
for file in os.listdir(data_folder_path):
    if file.endswith('.csv'):
        股票名称 = file.split('.')[0]
        file_path = os.path.join(data_folder_path, file)
        股票数据[股票名称] = pd.read_csv(file_path)

# 准备所有股票的收盘价数据
所有股票收盘价 = pd.DataFrame()
for 股票名称, data in 股票数据.items():
    所有股票收盘价[股票名称] = data['Close']

# 初始化MinMaxScaler
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(所有股票收盘价)

# 设置时间步长为10
time_step = 10

# 将数据集分为训练集（80%）和测试集（20%）
train_size = int(len(scaled_data) * 0.8)
train_data = scaled_data[:train_size]
test_data = scaled_data[train_size - time_step:]

# 定义函数用于创建时间序列数据集
def create_dataset(data, time_step=1):
    X, Y = [], []
    for i in range(len(data)-time_step):
        X.append(data[i:(i+time_step)])
        Y.append(data[i + time_step])
    return np.array(X), np.array(Y)

# 设置时间步长为10，并创建训练集和测试集
X_train, y_train = create_dataset(train_data, time_step)
X_test, y_test = create_dataset(test_data, time_step)

# 构建LSTM模型
model = Sequential()
model.add(LSTM(100, return_sequences=True, input_shape=(time_step, len(股票数据))))
model.add(LSTM(100, return_sequences=False))
model.add(Dense(50))
model.add(Dense(len(股票数据)))

# 编译模型
model.compile(optimizer='adam', loss='mean_squared_error')

# 训练模型
model.fit(X_train, y_train, batch_size=32, epochs=10, validation_split=0.1)

# 使用模型进行预测
train_predict = model.predict(X_train)
test_predict = model.predict(X_test)

# 将预测结果反向转换回原始比例
train_predict = scaler.inverse_transform(train_predict)
test_predict = scaler.inverse_transform(test_predict)
y_train = scaler.inverse_transform(y_train)
y_test = scaler.inverse_transform(y_test)

# 绘制结果图
plt.figure(figsize=(15,10))
for i, 股票名称 in enumerate(股票数据.keys()):
    plt.subplot(len(股票数据), 1, i+1)
    plt.plot(所有股票收盘价[股票名称].values, label='实际股价')
    plt.plot(range(time_step, len(train_predict)+time_step), train_predict[:, i], label='训练集预测')
    plt.plot(range(len(train_predict)+time_step, len(scaled_data)), test_predict[:, i], label='测试集预测')
    plt.title(f'{股票名称} 股价预测结果')
    plt.legend()

plt.tight_layout()
plt.show()

# 输出每只股票的预测结果
for i, 股票名称 in enumerate(股票数据.keys()):
    print(f"\n{股票名称} 的预测结果：")
    for j in range(len(test_predict)):
        实际价格 = y_test[j][i]
        预测价格 = test_predict[j][i]
        误差 = 实际价格 - 预测价格
        误差百分比 = (误差 / 实际价格) * 100
        print(f"第 {j+1} 天: 实际价格 = {实际价格:.2f}, 预测价格 = {预测价格:.2f}, 误差 = {误差:.2f}, 误差百分比 = {误差百分比:.2f}%")