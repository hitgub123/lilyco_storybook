# =======================================================================
# 单元格 1: 安装所有必需的库
# =======================================================================
print("Installing libraries for QLoRA finetuning...")
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
# =======================================================================
class TrainingConfig:
    MODEL_ID = "google/gemma-3-270m-it"
    # MODEL_ID = "google/gemma-3-1bm-it"
    # MODEL_ID = "google/gemma-3-4b-it"
    DATA_FILE_PATH = "/kaggle/input/test01/training_data_for_agent.jsonl" # <-- 请务必修改为您的路径
    OUTPUT_DIR = "/kaggle/working/gemma3_qlora_finetuned"

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

# --- QLoRA 配置 ---
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)
lora_config = LoraConfig(
    r=16, # LoRA rank, 可以设为 8, 16, 32等
    lora_alpha=32, # LoRA alpha
    lora_dropout=0.05,
    target_modules=["q_proj", "o_proj", "k_proj", "v_proj", "gate_proj", "up_proj", "down_proj"],
    task_type="CAUSAL_LM",
)

# --- 加载并准备模型 (采纳建议进行修改) ---
print("Loading model with QLoRA configuration and best practices...")
model = AutoModelForCausalLM.from_pretrained(
    TrainingConfig.MODEL_ID,
    quantization_config=quantization_config,
    device_map=0,
    torch_dtype=torch.float16,
    attn_implementation='eager', # <-- 修改1: 使用 eager attention
    use_cache=False,             # <-- 修改2: 明确禁用 use_cache
)
model = prepare_model_for_kbit_training(model)
model = get_peft_model(model, lora_config)
print("Model prepared for QLoRA training.")
model.print_trainable_parameters()

# --- 训练参数 (采纳建议进行修改) ---
training_args = TrainingArguments(
    output_dir=TrainingConfig.OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    logging_strategy="steps",
    logging_steps=10,
    save_strategy="epoch",
    dataloader_num_workers=0,
    fp16=True,
     # 禁用 wandb，防止卡死
    report_to="none",
    # --- 修改3: 解决 use_reentrant 警告 ---
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={'use_reentrant': False},
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

# --- 开始训练 ---
print("Starting final training run...")
trainer.train()
print("Training finished.")

# --- 保存最终的 LoRA 适配器 ---
print(f"Saving final model adapters to {TrainingConfig.OUTPUT_DIR}...")
trainer.save_model(TrainingConfig.OUTPUT_DIR)
tokenizer.save_pretrained(TrainingConfig.OUTPUT_DIR)
print("Script finished successfully.")