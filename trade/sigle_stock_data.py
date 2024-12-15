# import pysnowball as ball

# ball.set_token("xq_a_token=662745a236*****;u=909119****")
# ball.quote_detail('SH600000')

import yfinance as yf
import requests
import os

# 配置代理服务器
proxies = {
    'http': 'http://11.39.221.0:9091',
    'https': 'http://11.39.221.0:9091',
}

# 设置全局代理
session = requests.Session()
session.proxies.update(proxies)


stockArray = ["300750.SZ","600030.SS","600036.SS","601318.SS","000300.SS","513130.SS","000016.SZ"]  # 示例股票代码,请根据你的需求修改
#stockArray = ["588000.SS"]  # 示例股票代码,请根据你的需求修改


for stock in stockArray:
    tickers = [stock]  # 示例股票代码,请根据你的需求修改

    # 使用代理下载数据
    #['600036.SS']: YFInvalidPeriodError("%ticker%: Period '100y' is invalid, must be one of ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']")
    data = yf.download(tickers, start=None, end=None, period='3mo', interval='1d', actions=False, threads=True, session=session)

    # 确保data目录存在
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)

    # 将数据保存到data目录下
    file_path = os.path.join(data_dir, stock + "_stock_data_3m_1d.csv")
    data.to_csv(file_path)

    print(f"数据已保存到: {file_path}")
