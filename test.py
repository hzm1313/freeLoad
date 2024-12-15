# 导入必要的库
import json
import os
import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer
import numpy as np
from torch import nn
from transformers import AutoConfig
from transformers import BertPreTrainedModel, BertModel

from torch.utils.data import Dataset


if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("MPS is available. Using GPU.")
else:
    device = torch.device("cpu")
    print("MPS is not available. Using CPU.")
print(f'Using {device} device')

# 设置代理环境变量
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

# 用于存储所有出现的实体类别
categories = set()

class PeopleDaily(Dataset):
    def __init__(self, data_file):
        self.data = self.load_data(data_file)
    
    def load_data(self, data_file):
        Data = {}
        with open(data_file, 'rt', encoding='utf-8') as f:
            for idx, line in enumerate(f.read().split('\n\n')):
                if not line:
                    break
                sentence, labels = '', []
                for i, item in enumerate(line.split('\n')):
                    char, tag = item.split(' ')
                    sentence += char
                    if tag.startswith('B'):
                        # 开始一个新的实体
                        labels.append([i, i, char, tag[2:]]) # 移除 B- 或 I- 前缀
                        categories.add(tag[2:])
                    elif tag.startswith('I'):
                        # 继续前一个实体
                        labels[-1][1] = i
                        labels[-1][2] += char
                Data[idx] = {
                    'sentence': sentence, 
                    'labels': labels
                }
        return Data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]
    
# 加载训练、验证和测试数据
train_data = PeopleDaily('data/china-people-daily-ner-corpus/example.train')
valid_data = PeopleDaily('data/china-people-daily-ner-corpus/example.dev')
test_data = PeopleDaily('data/china-people-daily-ner-corpus/example.test')

# 创建标签到ID的映射
id2label = {0:'O'}
for c in list(sorted(categories)):
    id2label[len(id2label)] = f"B-{c}"
    id2label[len(id2label)] = f"I-{c}"
# 创建ID到标签的映射
label2id = {v: k for k, v in id2label.items()}

# 打印标签映射


# from transformers import AutoTokenizer
# import numpy as np

# checkpoint = "bert-base-chinese"
# tokenizer = AutoTokenizer.from_pretrained(checkpoint)

# sentence = '海钓比赛地点在厦门与金门之间的海域。'
# labels = [[7, 8, '厦门', 'LOC'], [10, 11, '金门', 'LOC']]

# encoding = tokenizer(sentence, truncation=True)
# tokens = encoding.tokens()
# label = np.zeros(len(tokens), dtype=int)
# for char_start, char_end, word, tag in labels:
#     token_start = encoding.char_to_token(char_start)
#     token_end = encoding.char_to_token(char_end)
#     label[token_start] = label2id[f"B-{tag}"]
#     label[token_start+1:token_end+1] = label2id[f"I-{tag}"]

checkpoint = "bert-base-chinese"
tokenizer = AutoTokenizer.from_pretrained(checkpoint)

def collote_fn(batch_samples):
    batch_sentence, batch_tags  = [], []
    for sample in batch_samples:
        batch_sentence.append(sample['sentence'])
        batch_tags.append(sample['labels'])
    batch_inputs = tokenizer(
        batch_sentence, 
        padding=True, 
        truncation=True, 
        return_tensors="pt"
    )
    batch_label = np.zeros(batch_inputs['input_ids'].shape, dtype=int)
    for s_idx, sentence in enumerate(batch_sentence):
        encoding = tokenizer(sentence, truncation=True)
        batch_label[s_idx][0] = -100
        batch_label[s_idx][len(encoding.tokens())-1:] = -100
        for char_start, char_end, _, tag in batch_tags[s_idx]:
            token_start = encoding.char_to_token(char_start)
            token_end = encoding.char_to_token(char_end)
            batch_label[s_idx][token_start] = label2id[f"B-{tag}"]
            batch_label[s_idx][token_start+1:token_end+1] = label2id[f"I-{tag}"]
    return batch_inputs, torch.tensor(batch_label)

train_dataloader = DataLoader(train_data, batch_size=4, shuffle=True, collate_fn=collote_fn)
valid_dataloader = DataLoader(valid_data, batch_size=4, shuffle=False, collate_fn=collote_fn)
test_dataloader = DataLoader(test_data, batch_size=4, shuffle=False, collate_fn=collote_fn)

batch_X, batch_y = next(iter(train_dataloader))
batch_X = {k: v.to(device) for k, v in batch_X.items()}
batch_y = batch_y.to(device)


class BertForNER(BertPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        self.bert = BertModel(config, add_pooling_layer=False)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.classifier = nn.Linear(768, len(id2label))
        self.post_init()

    def forward(self, x):
        bert_output = self.bert(**x)
        sequence_output = bert_output.last_hidden_state
        sequence_output = self.dropout(sequence_output)
        logits = self.classifier(sequence_output)
        return logits

config = AutoConfig.from_pretrained(checkpoint)
model = BertForNER.from_pretrained(checkpoint, config=config).to(device)
outputs = model(batch_X)

if __name__ == "__main__":
    mode = "predict"  # 可以设置为 "train" 或 "predict"
    if mode == "train":
        from tqdm.auto import tqdm

        def train_loop(dataloader, model, loss_fn, optimizer, lr_scheduler, epoch, total_loss):
            progress_bar = tqdm(range(len(dataloader)))
            progress_bar.set_description(f'loss: {0:>7f}')
            finish_batch_num = (epoch-1) * len(dataloader)
            
            model.train()
            for batch, (X, y) in enumerate(dataloader, start=1):
                X, y = X.to(device), y.to(device)
                pred = model(X)
                loss = loss_fn(pred.permute(0, 2, 1), y)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                lr_scheduler.step()

                total_loss += loss.item()
                progress_bar.set_description(f'loss: {total_loss/(finish_batch_num + batch):>7f}')
                progress_bar.update(1)
            return total_loss


        from seqeval.metrics import classification_report
        from seqeval.scheme import IOB2

        y_true = [['O', 'O', 'O', 'B-LOC', 'I-LOC', 'I-LOC', 'B-LOC', 'O'], ['B-PER', 'I-PER', 'O']]
        y_pred = [['O', 'O', 'B-LOC', 'I-LOC', 'I-LOC', 'I-LOC', 'B-LOC', 'O'], ['B-PER', 'I-PER', 'O']]

        print(classification_report(y_true, y_pred, mode='strict', scheme=IOB2))

        from seqeval.metrics import classification_report
        from seqeval.scheme import IOB2

        def test_loop(dataloader, model):
            true_labels, true_predictions = [], []

            model.eval()
            with torch.no_grad():
                for X, y in tqdm(dataloader):
                    X, y = X.to(device), y.to(device)
                    pred = model(X)
                    predictions = pred.argmax(dim=-1).cpu().numpy().tolist()
                    labels = y.cpu().numpy().tolist()
                    true_labels += [[id2label[int(l)] for l in label if l != -100] for label in labels]
                    true_predictions += [
                        [id2label[int(p)] for (p, l) in zip(prediction, label) if l != -100]
                        for prediction, label in zip(predictions, labels)
                    ]
            print(classification_report(true_labels, true_predictions, mode='strict', scheme=IOB2))
            return classification_report(
            true_labels, 
            true_predictions, 
            mode='strict', 
            scheme=IOB2, 
            output_dict=True
            )


        from transformers import AdamW, get_scheduler

        learning_rate = 1e-5
        epoch_num = 3

        loss_fn = nn.CrossEntropyLoss()
        optimizer = AdamW(model.parameters(), lr=learning_rate)
        lr_scheduler = get_scheduler(
            "linear",
            optimizer=optimizer,
            num_warmup_steps=0,
            num_training_steps=epoch_num*len(train_dataloader),
        )

        total_loss = 0.
        for t in range(epoch_num):
            print(f"Epoch {t+1}/{epoch_num}\n-------------------------------")
            total_loss = train_loop(train_dataloader, model, loss_fn, optimizer, lr_scheduler, t+1, total_loss)
            test_loop(valid_dataloader, model)
        print("Done!")

        total_loss = 0.
        best_f1 = 0.
        for t in range(epoch_num):
            print(f"Epoch {t+1}/{epoch_num}\n-------------------------------")
            total_loss = train_loop(train_dataloader, model, loss_fn, optimizer, lr_scheduler, t+1, total_loss)
            metrics = test_loop(valid_dataloader, model)
            valid_macro_f1, valid_micro_f1 = metrics['macro avg']['f1-score'], metrics['micro avg']['f1-score']
            valid_f1 = metrics['weighted avg']['f1-score']
            if valid_f1 > best_f1:
                best_f1 = valid_f1
                print('saving new weights...\n')
                torch.save(
                    model.state_dict(), 
                    f'epoch_{t+1}_valid_macrof1_{(100*valid_macro_f1):0.3f}_microf1_{(100*valid_micro_f1):0.3f}_weights.bin'
                )   
        print("Done!")
    else:
        sentence = '日本外务省3月18日发布消息称，日本首相岸田文雄将于19至21日访问印度和柬埔寨。'
        model.eval()
        results = []
        with torch.no_grad():
            inputs = tokenizer(sentence, truncation=True, return_tensors="pt", return_offsets_mapping=True)
            offsets = inputs.pop('offset_mapping').squeeze(0)
            inputs = inputs.to(device)
            pred = model(inputs)
            probabilities = torch.nn.functional.softmax(pred, dim=-1)[0].cpu().numpy().tolist()
            predictions = pred.argmax(dim=-1)[0].cpu().numpy().tolist()

            pred_label = []
            idx = 0
            while idx < len(predictions):
                pred = predictions[idx]
                label = id2label[pred]
                if label != "O":
                    label = label[2:] # Remove the B- or I-
                    start, end = offsets[idx]
                    all_scores = [probabilities[idx][pred]]
                    # Grab all the tokens labeled with I-label
                    while (
                        idx + 1 < len(predictions) and
                        id2label[predictions[idx + 1]] == f"I-{label}"
                    ):
                        all_scores.append(probabilities[idx + 1][predictions[idx + 1]])
                        _, end = offsets[idx + 1]
                        idx += 1

                    score = np.mean(all_scores).item()
                    start, end = start.item(), end.item()
                    word = sentence[start:end]
                    pred_label.append(
                        {
                            "entity_group": label,
                            "score": score,
                            "word": word,
                            "start": start,
                            "end": end,
                        }
                    )
                idx += 1
            print(pred_label)
