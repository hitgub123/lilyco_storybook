from dotenv import load_dotenv
import os
import subprocess,shlex

load_dotenv()
START_BROWSER_CMD = os.getenv("START_BROWSER_CMD")
START_BROWSER_CMD_LIST = START_BROWSER_CMD.split("@@@")
# START_BROWSER_CMD_LIST = [
#     "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
#     "--remote-debugging-port=9222",
#     "--user-data-dir=C:\\edge-debug-profile",  # 确保这个路径是你想用的
# ]

try:
    a = 1 / 0
except Exception as e:
    print(f"发生错误: {e}")

    # 执行命令并获取输出
    result = subprocess.Popen(
        START_BROWSER_CMD_LIST
        # START_BROWSER_CMD
    )

    # 输出命令结果
    print("标准输出:", result)
    # print("标准错误:", result.stderr)
    # print("返回码:", result.returncode)
