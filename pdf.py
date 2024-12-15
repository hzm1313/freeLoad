from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# https://transformers.run/c2/2021-12-08-transformers-note-1/#%E9%9B%B6%E8%AE%AD%E7%BB%83%E6%A0%B7%E6%9C%AC%E5%88%86%E7%B1%BB

# 检查MPS（Metal Performance Shaders）是否可用
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("MPS is available. Using GPU.")
else:
    device = torch.device("cpu")
    print("MPS is not available. Using CPU.")

checkpoint = "distilbert-base-uncased-finetuned-sst-2-english"
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
model = AutoModelForSequenceClassification.from_pretrained(checkpoint)

sequence = "I've been waiting for a HuggingFace course my whole life."

tokenized_inputs = tokenizer(sequence, return_tensors="pt")
print("Inputs Keys:\n", tokenized_inputs.keys())
print("\nInput IDs:\n", tokenized_inputs["input_ids"])

output = model(**tokenized_inputs)
print("\nLogits:\n", output.logits)