# =======================================================================
# 单元格 1: 安装最核心的库
# =======================================================================
print("Installing core libraries: transformers, datasets, accelerate")
!pip install -q -U transformers datasets accelerate
print("Installation complete.")


# =======================================================================
# 单元格 2: 登录 Hugging Face Hub (对于 distilgpt2 非必需，但保留无害)
# =======================================================================
import os
from huggingface_hub import login
from kaggle_secrets import UserSecretsClient

try:
    user_secrets = UserSecretsClient()
    hf_token = user_secrets.get_secret("HUGGINGFACE_TOKEN")
    print("Hugging Face token found. Logging in...")
    login(token=hf_token)
    print("Login successful.")
except Exception as e:
    print("Could not log in to Hugging Face. Please ensure HUGGINGFACE_TOKEN is set correctly.")
    print(f"Error: {e}")


# =======================================================================
# 单元格 3: 配置参数 (使用 distilgpt2 进行最终诊断)
# =======================================================================
class TrainingConfig:
    # --- 使用一个极其稳定和基础的模型作为对照组 ---
    MODEL_ID = "distilgpt2"
    DATA_FILE_PATH = "/kaggle/input/test01/training_data_for_agent.jsonl" # <-- 请务必修改为您的路径
    # --- 修改输出目录以反映新模型 ---
    OUTPUT_DIR = "/kaggle/working/distilgpt2_full_finetuned"

print("Final Diagnostic Run Configuration:")
print(f"  - Model: {TrainingConfig.MODEL_ID}")
print(f"  - Data file: {TrainingConfig.DATA_FILE_PATH}")
print(f"  - Output directory: {TrainingConfig.OUTPUT_DIR}")


# =======================================================================
# 单元格 4: 简化的训练逻辑
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

# 注意：下面的对话模板是为 Gemma 设计的，distilgpt2 会把它当作普通文本处理。
# 这对于我们“测试训练是否能启动”的目标来说没有影响。
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
    device_map=0, # 直接加载到 GPU 0
)
model.resize_token_embeddings(len(tokenizer))
print("Model prepared for training.")

# --- 使用标准的训练参数 ---
training_args = TrainingArguments(
    output_dir=TrainingConfig.OUTPUT_DIR,
    num_train_epochs=1, # 只训练一个周期用于测试
    per_device_train_batch_size=4, # distilgpt2 更小，可以尝试更大的批次
    gradient_accumulation_steps=4,
    learning_rate=5e-5, # 经典的微调学习率
    logging_strategy="steps",
    logging_steps=1, # 每一步都打印日志
    save_strategy="no", # 测试时无需保存
    dataloader_num_workers=0,
    fp16=True,
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
