# %% [code]
# =======================================================================
# 1. 安装依赖库
# =======================================================================
!pip install -q -U transformers datasets accelerate peft bitsandbytes


# =======================================================================
# 2. 登录 Hugging Face
# =======================================================================
from huggingface_hub import login
from kaggle_secrets import UserSecretsClient

# 从 Kaggle Secrets 获取你的 Hugging Face 令牌并登录
user_secrets = UserSecretsClient()
hf_token = user_secrets.get_secret("HUGGINGFACE_TOKEN")
login(token=hf_token)

# =======================================================================
# 3. 导入库并设置参数 (这是你的主脚本)
# =======================================================================
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from datasets import load_dataset
from transformers import BitsAndBytesConfig
import torch
from peft import LoraConfig, get_peft_model
import json

# --- 修改这里的路径 ---
# 数据集路径 (指向你在 Kaggle 上传的数据)
data_file_path = "/kaggle/input/test01/training_data_for_agent.jsonl" 
# 模型输出路径 (Kaggle 的可写目录)
output_dir = "/kaggle/working/gemma3_270m_finetuned"

try:
    with open(data_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines, 1):
            try:
                json.loads(line.strip())
            except json.JSONDecodeError as e:
                print(f"--- FAILED: Line {i} is NOT a valid JSON. ---")
                print(f"Error details: {e}")
                exit(1)
        else:
            print(f"--- SUCCESS! All {len(lines)} lines are valid JSONL. ---")
            print(f"Loaded {len(lines)} records.")
except Exception as e:
    print(f"检查 JSONL 文件失败: {e}")
    exit(1)
    

# --- 其他参数保持不变 ---
model_name = "google/gemma-3-270m"
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

tokenizer = AutoTokenizer.from_pretrained(model_name)
if tokenizer.eos_token is None:
    tokenizer.add_special_tokens({'eos_token': '<eos>'})

# --- 修改模型加载参数 ---
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quantization_config,
    attn_implementation='eager',
    device_map={"": torch.cuda.current_device()}
)
model.resize_token_embeddings(len(tokenizer))

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    target_modules=["q_proj", "o_proj", "k_proj", "v_proj", "gate_proj", "up_proj", "down_proj"],
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)

# --- 加载和处理数据 ---
dataset = load_dataset("json", data_files=data_file_path)

def tokenize_function(examples):
    texts = []
    for prompt, tool_calls in zip(examples['prompt'], examples['tool_calls']):
        completion_obj = {"tool_calls": tool_calls}
        completion_str = json.dumps(completion_obj)
        text = f"PROMPT: {prompt}\nCOMPLETION: {completion_str}{tokenizer.eos_token}"
        texts.append(text)
    
    tokenized_output = tokenizer(
        texts,
        padding="max_length", 
        truncation=True,
        max_length=128
    )
    tokenized_output["labels"] = [x[:] for x in tokenized_output["input_ids"]]
    return tokenized_output

tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=dataset['train'].column_names)

# --- 设置训练参数并开始训练 ---
training_args = TrainingArguments(
    output_dir=output_dir,
    num_train_epochs=3,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    save_steps=10_000,
    save_total_limit=2,
    logging_strategy="steps",
    logging_steps=1,
    logging_dir="/kaggle/working/log", # 日志也输出到可写目录
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
)
try:
    trainer.train()
except Exception as e:
    print(f"失败了 {e}")
# --- 保存最终模型 ---
model.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)

print(f"训练完成！模型已保存到 {output_dir}")