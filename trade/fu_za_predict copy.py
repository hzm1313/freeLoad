# 导入必要的库
import pandas as pd  # 用于数据处理和分析
import numpy as np  # 用于数值计算
import matplotlib.pyplot as plt  # 用于绘图
from sklearn.preprocessing import MinMaxScaler  # 用于数据归一化
from tensorflow.keras.models import Sequential  # 用于创建序列模型
from tensorflow.keras.layers import Dense, LSTM  # 用于构建神经网络层
import os  # 用于处理文件和目录路径

# 导入字体管理器
from matplotlib import font_manager  # 用于管理matplotlib的字体

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # 设置支持中文的字体
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 获取当前脚本所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建数据文件夹的路径
data_folder_path = os.path.join(current_dir, 'data')

# 读取多只股票的数据
股票数据 = {}
for file in os.listdir(data_folder_path):
    if file.endswith('.csv'):
        股票名称 = file.split('.')[0]  # 提取股票名称
        file_path = os.path.join(data_folder_path, file)
        股票数据[股票名称] = pd.read_csv(file_path)  # 读取CSV文件并存储到字典中

# 准备所有股票的收盘价数据
所有股票收盘价 = pd.DataFrame()
for 股票名称, data in 股票数据.items():
    所有股票收盘价[股票名称] = data['Close']  # 提取每只股票的收盘价

# 初始化MinMaxScaler，用于将数据归一化到0-1范围
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(所有股票收盘价)  # 对所有股票的收盘价进行归一化

# 设置时间步长为10，即使用过去10天的数据来预测下一天
time_step = 10

# 使用所有数据进行训练
train_data = scaled_data

# 定义函数用于创建时间序列数据集
def create_dataset(data, time_step=1):
    X, Y = [], []
    for i in range(len(data)-time_step):
        X.append(data[i:(i+time_step)])  # 输入序列
        Y.append(data[i + time_step])  # 目标值
    return np.array(X), np.array(Y)

# 创建训练集
X_train, y_train = create_dataset(train_data, time_step)

# 构建LSTM模型
model = Sequential()
model.add(LSTM(100, return_sequences=True, input_shape=(time_step, len(股票数据))))  # 第一个LSTM层，返回序列
model.add(LSTM(100, return_sequences=False))  # 第二个LSTM层，不返回序列
model.add(Dense(50))  # 全连接层
model.add(Dense(len(股票数据)))  # 输出层，输出每只股票的预测值

# 编译模型
model.compile(optimizer='adam', loss='mean_squared_error')

# 训练模型
model.fit(X_train, y_train, batch_size=32, epochs=10, validation_split=0.1)

# 使用模型进行未来4天的预测
last_sequence = scaled_data[-time_step:]  # 获取最后10天的数据
future_predictions = []

for _ in range(4):
    next_pred = model.predict(last_sequence.reshape(1, time_step, len(股票数据)))  # 预测下一天
    future_predictions.append(next_pred[0])
    last_sequence = np.roll(last_sequence, -1, axis=0)  # 滚动数据
    last_sequence[-1] = next_pred[0]  # 将预测结果添加到序列末尾

# 将预测结果反向转换回原始比例
future_predictions = scaler.inverse_transform(np.array(future_predictions))

# 输出每只股票的预测结果
for i, 股票名称 in enumerate(股票数据.keys()):
    print(f"\n{股票名称} 的历史价格和未来4天预测结果：")
    
    # 输出用于推演的最近10天历史价格
    最近10天价格 = 所有股票收盘价[股票名称].values[-time_step:]
    for k, 价格 in enumerate(最近10天价格):
        print(f"历史第 {k+1} 天: 实际价格 = {价格:.2f}")
    
    # 输出未来4天预测结果
    for j in range(4):
        预测价格 = future_predictions[j][i]
        print(f"未来第 {j+1} 天: 预测价格 = {预测价格:.2f}")