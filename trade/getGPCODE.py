import pandas as pd

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

def get_combined_codes(excel1_path, excel2_path):
    # 读取第一个Excel文件
    df1 = pd.read_excel(excel1_path)
    # 读取第二个Excel文件
    df2 = pd.read_excel(excel2_path)
    
    # 获取两个文件中的code列数据
    codes1 = [code + '.SS' for code in df1['CODE'].astype(str).tolist()]
    codes2 = [code + '.SZ' for code in df2['CODE'].astype(str).tolist()]
    
    
    # 合并两个列表并去重
    all_codes = list(set(codes1 + codes2))
    
    # 用逗号拼接
    result = ','.join(all_codes)
    
    return result

if __name__ == '__main__':
    # 替换为实际的Excel文件路径
    excel1_path = '/Users/zm.huang/Desktop/workspace/aiTest/trade/preview/SHZJ_GPLIST.xls'
    excel2_path = '/Users/zm.huang/Desktop/workspace/aiTest/trade/preview/SZZJ_GPLIST.xlsx'
    
    combined_codes = get_combined_codes(excel1_path, excel2_path)
    # 将结果转换为列表
    code_list = combined_codes.split(',')
    
    # 每批次输出的数量
    batch_size = 10
    
    # 分批输出
    for i in range(0, len(code_list)):
        print(f"第{i + 1}个股票代码:")
        print(code_list[i])
        tickers = [code_list[i]]  # 示例股票代码,请根据你的需求修改

        # 使用代理下载数据
        data = yf.download(tickers, start=None, end=None, period='3mo', interval='1d', actions=False, threads=True, session=session)

        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)

        # 将数据保存到data目录下
        file_path = os.path.join(data_dir, code_list[i] + "_stock_data_3m_1d.csv")
        data.to_csv(file_path)

        print(f"数据已保存到: {file_path}")



