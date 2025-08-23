# =======================================================================
# Colab 适配版 - 单元格 1: 安装库
# =======================================================================
print("Installing core libraries: transformers, datasets, accelerate")
!pip install -q -U transformers datasets accelerate
print("Installation complete.")


# =======================================================================
# Colab 适配版 - 单元格 2: 登录 Hugging Face Hub
# =======================================================================
import os
from huggingface_hub import login
from google.colab import userdata # <-- 使用 Colab 的密钥管理工具

try:
    # 在 Colab 左侧边栏的“密钥”图标中，添加名为 HUGGINGFACE_TOKEN 的密钥
    hf_token = userdata.get("HUGGINGFACE_TOKEN")
    print("Hugging Face token found in Colab Secrets. Logging in...")
    login(token=hf_token)
    print("Login successful.")
except Exception as e:
    print("Could not log in to Hugging Face. Please ensure HUGGINGFACE_TOKEN is set correctly in Colab Secrets.")
    print(f"Error: {e}")


# =======================================================================
# Colab 适配版 - 单元格 3: 配置参数
# =======================================================================
class TrainingConfig:
    MODEL_ID = "distilgpt2"
    
    # --- 请根据您上传文件的方式，选择并修改下面的路径 ---
    # 方式 A: 如果您是直接上传到会话存储
    # DATA_FILE_PATH = "/content/training_data_for_agent.jsonl"
    
    # 方式 B (推荐): 如果您挂载了 Google Drive
    DATA_FILE_PATH = "/content/drive/MyDrive/Colab_Data/training_data_for_agent.jsonl"
    
    # Colab 的可写目录是 /content/
    OUTPUT_DIR = "/content/distilgpt2_full_finetuned"

print("Training Configuration:")
print(f"  - Model: {TrainingConfig.MODEL_ID}")
print(f"  - Data file: {TrainingConfig.DATA_FILE_PATH}")
print(f"  - Output directory: {TrainingConfig.OUTPUT_DIR}")


# =======================================================================
# Colab 适配版 - 单元格 4: 简化的训练逻辑 (与 Kaggle 版相同)
# =======================================================================
import torch
import json
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
)

# --- 数据加载和处理部分 ---
print(f"Loading dataset from {TrainingConfig.DATA_FILE_PATH}...")
dataset = load_dataset("json", data_files=TrainingConfig.DATA_FILE_PATH, split="train")
print(f"Dataset loaded with {len(dataset)} records.")

tokenizer = AutoTokenizer.from_pretrained(TrainingConfig.MODEL_ID)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

def tokenize_function(examples):
    texts = []
    for prompt, tool_calls in zip(examples['prompt'], examples['tool_calls']):
        completion_obj = {"tool_calls": tool_calls}
        completion_str = json.dumps(completion_obj, ensure_ascii=False)
        text = f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n{completion_str}<end_of_turn>"
        texts.append(text)
    tokenized_output = tokenizer(texts, padding="longest", truncation=True, max_length=512)
    tokenized_output["labels"] = [x[:] for x in tokenized_output["input_ids"]]
    return tokenized_output

print("Tokenizing dataset...")
tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=dataset.column_names)
print("Tokenization complete.")

# --- 极简的模型加载 ---
print("Loading model for full finetuning...")
model = AutoModelForCausalLM.from_pretrained(
    TrainingConfig.MODEL_ID,
    device_map="auto", # 在 Colab 中，auto 会自动选择可用的 GPU
)
model.resize_token_embeddings(len(tokenizer))
print("Model prepared for training.")

# --- 使用标准的训练参数 ---
training_args = TrainingArguments(
    output_dir=TrainingConfig.OUTPUT_DIR,
    num_train_epochs=1,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=5e-5,
    logging_strategy="steps",
    logging_steps=10,
    save_strategy="no",
    dataloader_num_workers=0,
    fp16=True, # Colab 的 GPU 通常都支持 fp16
    report_to="none",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

# --- 开始训练 ---
print("Starting training...")
trainer.train()
print("Training finished successfully! The environment is working.")
