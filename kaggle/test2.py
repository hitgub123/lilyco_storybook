# =======================================================================
# 单元格 1: 安装最核心的库
# =======================================================================
print("Installing core libraries: transformers, datasets, accelerate")
!pip install -q -U transformers datasets accelerate
print("Installation complete.")


# =======================================================================
# 单元格 2: 登录 Hugging Face Hub
# =======================================================================
import os
from huggingface_hub import login
from kaggle_secrets import UserSecretsClient
from IPython.display import Javascript

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
# 单元格 3: 配置参数
# =======================================================================
class TrainingConfig:
    MODEL_ID = "google/gemma-3-270m-it"
    DATA_FILE_PATH = "/kaggle/input/test01/training_data_for_agent.jsonl" # <-- 请务必修改为您的路径
    OUTPUT_DIR = "/kaggle/working/gemma3_full_finetuned" # 输出一个完整微调的模型

print("Training Configuration:")
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

# --- 数据加载和处理部分 (与之前相同) ---
print(f"Loading dataset from {TrainingConfig.DATA_FILE_PATH}...")
try:
    dataset = load_dataset("json", data_files=TrainingConfig.DATA_FILE_PATH, split="train")
except Exception as e:
    print(f"load_dataset Error: {e}")
print(f"Dataset loaded with {len(dataset)} records.")
try:
    tokenizer = AutoTokenizer.from_pretrained(TrainingConfig.MODEL_ID)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
except Exception as e:
    print(f"from_pretrained Error: {e}")
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
try:
    tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=dataset.column_names)
except Exception as e:
    print(f"dataset.map Error: {e}")
print("Tokenization complete.")

# --- 极简的模型加载 ---
# 我们不再使用 bitsandbytes 和 peft
print("Loading model for full finetuning...")
try:
    model = AutoModelForCausalLM.from_pretrained(
        TrainingConfig.MODEL_ID,
        device_map=0, # 直接加载到 GPU 0
        # 不再指定 torch_dtype，使用默认的 float32 以保证最大稳定性
    )
    # 调整嵌入层大小以匹配分词器，这是一个好习惯
    model.resize_token_embeddings(len(tokenizer))
except Exception as e:
    print(f"AutoModelForCausalLM.from_pretrained Error: {e}")
print("Model prepared for training.")

# --- 使用标准的训练参数 ---
training_args = TrainingArguments(
    output_dir=TrainingConfig.OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=2,  # 完整微调需要更多显存，批次大小可能需要减小
    gradient_accumulation_steps=8,
    learning_rate=2e-5, # 完整微调通常使用更小的学习率
    logging_strategy="steps",
    logging_steps=10,
    save_strategy="epoch",
    dataloader_num_workers=0,
    # 使用标准的 fp16 混合精度训练，这是在 GPU 上最常用、最稳定的加速方式
    fp16=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

# --- 开始训练 ---
print("Starting training...")
try:
    trainer.train()
except Exception as e:
    print(f"train Error: {e}")
print("Training finished.")

# --- 保存完整的微调后模型 ---
print(f"Saving final model to {TrainingConfig.OUTPUT_DIR}...")
trainer.save_model(TrainingConfig.OUTPUT_DIR)
tokenizer.save_pretrained(TrainingConfig.OUTPUT_DIR) # 同时保存分词器
print("Script finished successfully.")