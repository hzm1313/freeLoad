# 检查是否在 Mac 上运行
import platform
from datetime import timedelta
from typing import List

import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.models import Model

from ..config.settings import Settings
from ..models.entities import StockData, PredictionResult
from ..utils.data_processor import DataProcessor
from ..utils.logger import Logger

is_mac = platform.system() == 'Darwin'
is_apple_silicon = is_mac and platform.machine() == 'arm64'

if is_apple_silicon:
    try:
        # 为 Apple Silicon (M1/M2/M3) 设置 Metal 插件
        physical_devices = tf.config.list_physical_devices('GPU')
        if len(physical_devices) > 0:
            tf.config.experimental.set_memory_growth(physical_devices[0], True)
        tf.config.set_visible_devices(physical_devices[0], 'GPU')
    except:
        print("无法设置 GPU 设备。将使用 CPU 进行计算。")
elif is_mac:
    # 对于 Intel Mac 的原有设置
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        tf.config.experimental.set_visible_devices([], 'GPU')
        tf.config.experimental.set_memory_growth(gpus[0], True)
    else:
        print("没有可用的 GPU，使用 CPU 进行计算。")
else:
    print("非 Mac 系统，使用默认设置。")

class LSTMPredictor:
    def __init__(self):
        self.logger = Logger()
        self.data_processor = DataProcessor()
        self.model = self._build_model()

    def _build_model(self) -> Model:
        """构建LSTM模型"""
        inputs = Input(shape=(Settings.LSTM.time_step, 1))
        x = LSTM(Settings.LSTM.lstm_units, return_sequences=True)(inputs)
        x = Dropout(0.2)(x)
        x = LSTM(Settings.LSTM.lstm_units, return_sequences=False)(x)
        x = Dropout(0.2)(x)
        x = Dense(Settings.LSTM.dense_units)(x)
        outputs = Dense(1)(x)

        model = Model(inputs=inputs, outputs=outputs)

        if is_mac:
            # 为 Mac 优化的编译设置
            model.compile(optimizer='adam', loss='mean_squared_error',
                          run_eagerly=True)
        else:
            model.compile(optimizer='adam', loss='mean_squared_error')
        return model
    def train(self, stock_data: StockData) -> None:
        """训练模型"""
        try:
            X, y = self.data_processor.prepare_lstm_data(stock_data)
            # 划分训练集和验证集
            train_size = int(len(X) * (1 - Settings.LSTM.validation_split))
            X_train, X_val = X[:train_size], X[train_size:]
            y_train, y_val = y[:train_size], y[train_size:]
            # 调整数据形状
            X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
            X_val = X_val.reshape(X_val.shape[0], X_val.shape[1], 1)
            # 训练模型
            self.model.fit(
                X_train, y_train,
                batch_size=Settings.LSTM.batch_size,
                epochs=Settings.LSTM.epochs,
                validation_data=(X_val, y_val),
                verbose=1
            )
        except Exception as e:
            self.logger.error(f"Error training LSTM model: {str(e)}")
            raise
    def predict(self, stock_data: StockData, days_ahead: int = 5) -> List[PredictionResult]:
        """预测未来价格"""
        try:
            # 准备最新的时间序列数据
            last_sequence = stock_data.data['Close'].values[-Settings.LSTM.time_step:]
            last_sequence = self.data_processor.scaler.transform(
                last_sequence.reshape(-1, 1)
            )
            predictions = []
            current_sequence = last_sequence.copy()
            for i in range(days_ahead):
                # 预测下一天
                current_sequence_reshaped = current_sequence.reshape(
                    1, Settings.LSTM.time_step, 1
                )
                next_pred = self.model.predict(current_sequence_reshaped)
                # 转换回原始价格
                predicted_price = float(self.data_processor.inverse_transform_prices(
                    next_pred
                )[0, 0])
                # 计算预测日期
                # 计算预测日期：基于最后一个已知日期，向前推进i+1天
                prediction_date = (stock_data.data.index[-1] + timedelta(days=i+1)).date()
                # 计算置信度（简单示例）
                confidence = 0.9 / (i + 1)  # 预测越远置信度越低
                # 生成信号
                signals = self._generate_signals(predicted_price,
                                              stock_data.data['Close'].values[-1])
                predictions.append(PredictionResult(
                    code=stock_data.code,
                    date=prediction_date,
                    predicted_price=predicted_price,
                    confidence=confidence,
                    signals=signals
                ))
                # 更新序列用于下一次预测
                current_sequence = np.roll(current_sequence, -1)
                current_sequence[-1] = next_pred
            return predictions
        except Exception as e:
            self.logger.error(f"Error making predictions: {str(e)}")
            raise

    def _generate_signals(self, predicted_price: float,
                         current_price: float) -> List[str]:
        """生成交易信号"""
        signals = []
        price_change = (predicted_price - current_price) / current_price
        if price_change > 0.03:
            signals.append("强烈买入")
        elif price_change > 0.01:
            signals.append("建议买入")
        elif price_change < -0.03:
            signals.append("强烈卖出")
        elif price_change < -0.01:
            signals.append("建议卖出")
        else:
            signals.append("持观望态度")

        return signals
