# =======================================================================
# 单元格 1: 安装所有必需的库
# =======================================================================
print("Installing necessary libraries: transformers, peft, bitsandbytes, datasets, accelerate")
!pip install -q -U transformers peft bitsandbytes datasets accelerate
print("Installation complete.")


# =======================================================================
# 单元格 2: 登录 Hugging Face Hub
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
# 单元格 3: 配置所有参数
# 将所有可变参数放在这里，方便修改
# =======================================================================
class TrainingConfig:
    MODEL_ID = "google/gemma-3-270m-it"  # 您可以选择 270m 或 1b 模型
    # --- 请确保这里的路径与您上传的数据集路径一致 ---
    DATA_FILE_PATH = "/kaggle/input/test01/training_data_for_agent.jsonl"
    OUTPUT_DIR = "/kaggle/working/gemma3_finetuned_adapters" # 训练好的模型适配器保存路径

# 打印配置以供检查
print("Training Configuration:")
print(f"  - Model: {TrainingConfig.MODEL_ID}")
print(f"  - Data file: {TrainingConfig.DATA_FILE_PATH}")
print(f"  - Output directory: {TrainingConfig.OUTPUT_DIR}")


# =======================================================================
# 单元格 4: 主要的训练逻辑
# =======================================================================
import torch
import json
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# 1. 加载数据集
#    load_dataset 会自动识别 .jsonl 文件格式（每行一个JSON对象）
print(f"Loading dataset from {TrainingConfig.DATA_FILE_PATH}...")
try:
    dataset = load_dataset("json", data_files=TrainingConfig.DATA_FILE_PATH, split="train")
    print(f"Dataset loaded successfully with {len(dataset)} records.")
except Exception as e:
    print(f"Failed to load dataset. Please check the file path and format. Error: {e}")
    # 如果数据集加载失败，就停止执行
    raise e

# 2. 加载分词器 (Tokenizer)
tokenizer = AutoTokenizer.from_pretrained(TrainingConfig.MODEL_ID)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token # 设置 padding token 以进行批处理

# 3. 定义数据处理函数
def tokenize_function(examples):
    texts = []
    for prompt, tool_calls in zip(examples['prompt'], examples['tool_calls']):
        completion_obj = {"tool_calls": tool_calls}
        completion_str = json.dumps(completion_obj, ensure_ascii=False) # ensure_ascii=False 保证中文不被转义
        text = f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n{completion_str}<end_of_turn>"
        texts.append(text)
    
    tokenized_output = tokenizer(texts, padding=True, truncation=True, max_length=512)
    tokenized_output["labels"] = [x[:] for x in tokenized_output["input_ids"]]
    return tokenized_output

# 4. 处理数据集
print("Tokenizing dataset...")
tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=dataset.column_names)
print("Tokenization complete.")

# 5. 配置4-bit量化 (QLoRA)
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

# 6. 配置 LoRA
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    target_modules=["q_proj", "o_proj", "k_proj", "v_proj", "gate_proj", "up_proj", "down_proj"],
    task_type="CAUSAL_LM",
)

# 7. 加载并准备模型
print("Loading model with QLoRA configuration...")
model = AutoModelForCausalLM.from_pretrained(
    TrainingConfig.MODEL_ID,
    quantization_config=quantization_config,
    device_map="auto", # 自动将模型分布到可用设备（GPU）
    torch_dtype=torch.float16, # 使用 float16 兼容性最好
)
model = prepare_model_for_kbit_training(model)
model = get_peft_model(model, lora_config)
print("Model prepared for training.")

# 8. 配置训练参数
training_args = TrainingArguments(
    output_dir=TrainingConfig.OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=4, # 根据显存大小可适当调整
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    logging_strategy="steps",
    logging_steps=10, # 每 10 步打印一次日志
    save_strategy="epoch", # 每个 epoch 保存一次模型
    fp16=True, # 在支持的硬件上开启 fp16 训练
)

# 9. 创建并开始训练
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

print("Starting training...")
try:
    trainer.train()
except Exception as e:
    print('e:',e)
print("Training finished.")

# 10. 保存最终的模型适配器
print(f"Saving final model adapters to {TrainingConfig.OUTPUT_DIR}...")
trainer.save_model(TrainingConfig.OUTPUT_DIR)
print("Script finished successfully.")