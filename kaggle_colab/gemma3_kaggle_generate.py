# =======================================================================
# 单元格 1: 安装必要的库
# =======================================================================
print("Installing necessary libraries: transformers, accelerate")
!pip install -q -U transformers accelerate
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
    print(f"Could not log in to Hugging Face. Error: {e}")


# =======================================================================
# 单元格 3: (健壮版) 加载模型并进行文本生成
# =======================================================================
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

# 检查是否有可用的 GPU
if torch.cuda.is_available():
    print(f"GPU is available. Using device: {torch.cuda.get_device_name(0)}")
    
    # 您可以在这里切换模型 ID
    # model_id = "google/gemma-3-270m-it"
    model_id = "google/gemma-3-1b-it"

    # 1. 手动加载分词器和模型
    print(f"Loading tokenizer and model for: {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        # torch_dtype=torch.float16,
        device_map=0,
    )

    # 2. 关键修复步骤：确保模型和分词器配置同步
    #    这会检查分词器的词汇表大小，并相应地调整模型嵌入层的大小，
    #    从而修复任何可能存在的配置不匹配问题。
    print("Resizing model embeddings to match tokenizer...")
    model.resize_token_embeddings(len(tokenizer))
    
    # 同样，确保有 pad_token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # 3. 将加载并修复好的组件传给 pipeline
    print("Creating text-generation pipeline...")
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
    )
    print("Model pipeline loaded successfully.")

    # 4. 循环提问
    qs=["请给我写一个关于一只聪明的狐狸和一只骄傲的兔子的短篇故事。","请给我写一个关于鬼屋的短篇故事。"]
    for q in qs:
        print(f"\n--- Generating for prompt: '{q[:30]}...' ---")
        messages = [{"role": "user", "content": q}]
        prompt = pipe.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        outputs = pipe(
            prompt,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.7,
        )
        
        response_only = outputs[0]["generated_text"].replace(prompt, "", 1) # Use replace to remove only the first occurrence of prompt
        print("--- Model Response ---")
        print(response_only)
        print("----------------------")

else:
    print("GPU not available. This script is designed to run on a GPU.")