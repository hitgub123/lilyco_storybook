import torch

print(torch.__version__)
print(torch.cuda.is_available())  # 应返回 False
print("Running on:", torch.device("cpu").type)
