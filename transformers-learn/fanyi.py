import requests
import gzip
from io import BytesIO

# 配置代理服务器
proxies = {
    'http': 'http://11.39.221.0:9091',
    'https': 'http://11.39.221.0:9091',
}

from torch.utils.data import Dataset, random_split
import json

# 设置数据集大小限制
max_dataset_size = 220000
train_set_size = 200000
valid_set_size = 20000

class TRANS(Dataset):
    def __init__(self, data_file):
        # 初始化时加载数据
        self.data = self.load_data(data_file)
    
    def load_data(self, data_file):
        Data = {}
        # 打开并读取数据文件
        with open(data_file, 'rt', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                # 如果达到最大数据集大小，停止读取
                if idx >= max_dataset_size:
                    break
                # 解析每行JSON数据
                sample = json.loads(line.strip())
                Data[idx] = sample
        return Data
    
    def __len__(self):
        # 返回数据集的大小
        return len(self.data)

    def __getitem__(self, idx):
        # 返回指定索引的数据项
        return self.data[idx]

# 加载训练数据集
data = TRANS('data/translation2019zh/translation2019zh_train.json')
# 将数据集分割为训练集和验证集
train_data, valid_data = random_split(data, [train_set_size, valid_set_size])
# 加载测试数据集
test_data = TRANS('data/translation2019zh/translation2019zh_valid.json')

print(f'train set size: {len(train_data)}')
print(f'valid set size: {len(valid_data)}')
print(f'test set size: {len(test_data)}')
print(next(iter(train_data)))

from transformers import AutoTokenizer

model_checkpoint = "Helsinki-NLP/opus-mt-zh-en"
tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
zh_sentence = train_data[0]["chinese"]
en_sentence = train_data[0]["english"]

inputs = tokenizer(zh_sentence)
with tokenizer.as_target_tokenizer():
    targets = tokenizer(en_sentence)