model_list=["phi4-mini:3.8b","mistral:7b","llama3.1:8b","gemma3-1b-lora:model-f16","gemma3-1b-lora:model-Q4_K_M"]
s=[f'{i}:{model_list[i]}' for i in range(len(model_list))]
i = input(f"请输入想使用的模型：{s}")
a=int(i)
model_list(int(i))