from dotenv import load_dotenv
import os
import subprocess,shlex

load_dotenv()
START_BROWSER_CMD = os.getenv("START_BROWSER_CMD")
START_BROWSER_CMD_LIST = START_BROWSER_CMD.split("@@@")

result = subprocess.run(
    "cd", shell=True,capture_output=True, text=True, encoding="utf-8"
)
result = subprocess.run(
    ["node", "batch/post_stories.js"], capture_output=True, text=True, encoding="utf-8"
)

print(9)
