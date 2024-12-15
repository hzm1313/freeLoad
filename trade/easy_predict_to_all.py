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
data_file_path = os.path.join(current_dir, 'data', '000016.SZ_stock_data_3m_1d.csv')

# 读取数据
data = pd.read_csv(data_file_path)

# 选择收盘价作为预测目标，并将其转换为numpy数组
data = data['Close'].values
data = data.reshape(-1, 1)

# 初始化MinMaxScaler，用于将数据缩放到0-1范围内
scaler = MinMaxScaler(feature_range=(0, 1)) 
scaled_data = scaler.fit_transform(data)

# 定义函数用于创建时间序列数据集
def create_dataset(data, time_step=1):
    X, Y = [], []
    for i in range(len(data)-time_step):
        X.append(data[i:(i+time_step), 0])
        Y.append(data[i + time_step, 0])
    return np.array(X), np.array(Y)

# 设置时间步长为10，并创建数据集
time_step = 10
X, y = create_dataset(scaled_data, time_step)

# 调整输入数据形状以适应LSTM层的输入要求
X = X.reshape(X.shape[0], X.shape[1], 1)

# 构建LSTM模型
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(time_step, 1)))
model.add(LSTM(50, return_sequences=False))
model.add(Dense(25))
model.add(Dense(1))

# 编译模型，使用Adam优化器和均方误差损失函数
model.compile(optimizer='adam', loss='mean_squared_error')

# 训练模型
model.fit(X, y, batch_size=1, epochs=1)

# 使用模型进行未来4天的预测
last_sequence = scaled_data[-time_step:]
future_predictions = []

for _ in range(4):
    next_pred = model.predict(last_sequence.reshape(1, time_step, 1))
    future_predictions.append(next_pred[0, 0])
    last_sequence = np.roll(last_sequence, -1)
    last_sequence[-1] = next_pred

# 将预测结果反向转换回原始比例
future_predictions = scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1))

# 输出未来4天的预测结果
print("\n用于预测的最近10天历史价格和未来4天的股价预测结果：")

# 输出用于预测的最近10天历史价格
最近10天价格 = scaler.inverse_transform(last_sequence)
for i, price in enumerate(最近10天价格):
    print(f"历史第 {i+1} 天: 实际价格 = {price[0]:.2f}")

# 输出未来4天的预测结果
for i, price in enumerate(future_predictions):
    print(f"未来第 {i+1} 天: 预测价格 = {price[0]:.2f}")

# # 绘制结果图
# plt.figure(figsize=(10,6))

# # 绘制历史股价
# plt.plot(scaler.inverse_transform(scaled_data), label='历史股价')

# # 绘制未来预测
# future_dates = range(len(scaled_data), len(scaled_data) + 4)
# plt.plot(future_dates, future_predictions, label='未来预测', color='red')

# plt.legend()
# plt.title('股价历史数据和未来预测')
# plt.xlabel('时间')
# plt.ylabel('股价')
# plt.show()