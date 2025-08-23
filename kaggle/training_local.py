from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from datasets import load_dataset
from transformers import BitsAndBytesConfig
import torch
from peft import LoraConfig, get_peft_model
import json

model_name = "google/gemma-3-270m"
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"正在使用的设备 (Using device): {device}")
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

tokenizer = AutoTokenizer.from_pretrained(model_name)
# Add EOS token if it's missing, which is common for some models
if tokenizer.eos_token is None:
    tokenizer.add_special_tokens({"eos_token": "<eos>"})


model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quantization_config,
    attn_implementation="eager",
    # device_map="auto" # This is recommended for multi-gpu or letting transformers handle device placement
)
# Resize token embeddings if a new token was added to the tokenizer
model.resize_token_embeddings(len(tokenizer))


lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    target_modules=[
        "q_proj",
        "o_proj",
        "k_proj",
        "v_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)

output_dir = "./model/gemma3_270m_finetuned"
dataset = load_dataset("json", data_files="./data/training_data_for_agent.jsonl")


def tokenize_function(examples):
    texts = []
    # The data structure has changed. We now use the 'tool_calls' column.
    for prompt, tool_calls in zip(examples["prompt"], examples["tool_calls"]):
        # Reconstruct the original JSON object structure that the model should learn to output.
        completion_obj = {"tool_calls": tool_calls}
        completion_str = json.dumps(completion_obj)
        text = f"PROMPT: {prompt}\nCOMPLETION: {completion_str}{tokenizer.eos_token}"
        texts.append(text)

    tokenized_output = tokenizer(
        texts, padding="max_length", truncation=True, max_length=128
    )

    tokenized_output["labels"] = [x[:] for x in tokenized_output["input_ids"]]

    return tokenized_output


# Remove original columns to avoid passing them to the model
tokenized_dataset = dataset.map(
    tokenize_function, batched=True, remove_columns=dataset["train"].column_names
)

training_args = TrainingArguments(
    output_dir=output_dir,
    num_train_epochs=3,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    save_steps=10_000,
    save_total_limit=2,
    logging_dir="./log",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
)

trainer.train()
model.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)
