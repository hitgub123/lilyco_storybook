# for folder web

## only build new file by using cache static file @seeing [[...slug]].tsx

`	"scripts": {
		"dev": "next dev",
		"build": "next build",
		"start": "next start",
		"lint": "next lint",
		"build-backup": "shx cp -r out/p/* out-1/p || true",
		"post-build": "shx cp -r out-1/p out",
		"my-build": "npm run build && npm run build-backup && npm run post-build"
	}, `

# for folder batch

## how to use generate_storybook.py

### 首先，完全关闭所有正在运行的 Edge 浏览器窗口。

### 然后，在命令行（CMD 或 PowerShell）中运行下面的命令：

`  "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir="C:\edge-debug-profile" `

### 运行这个命令后，执行 generated_stprybook.py

## ai agent

- 在这个路径生成 python 文件。写个函数，函数输入是类型 string 的 a 和 int 类型的 b 和 int 类型的 c 和函数 d，操作是 d 生成 json 格式的回答，内容是 b 条 c 字左右字符串的数组，每一条是一个跟 a 有关很短的小故事，函数输出是这个 list。这里的形参你改成合适的名字。

- 在这个路径生成 python 文件。使用 langchain 的 LangGraph 写个 ai agent，任务是根据输入提示词，生成多个短故事，再生成图片，再上传到 cloudinary。代码结构可参考 agent-demo.py，如果有更好的实现可自由发挥。agent 和提示词生成多个短故事都使用 gemini cli，这一步如果做不到使用 dummy 的 llm，生成的方法叫 invoke。可用的 tool 如下：
  - generate_stories.py 的 generate_stories_by_generation_func，它根据提示词生成多个短故事
  - generate_storybooks.py 的 run，它用短故事生成图片，保存到本地
  - cloudinary_util 的 main，它把生成的图片上传到 cloudinary

## wrangler d1

- wrangler d1 execute novel-comic-db --command "SELECT name FROM sqlite_master WHERE type='table';"
- npx wrangler d1 execute novel-comic-db --local --command="SELECT \* FROM novels"

 <!-- 很好，本地已经实现了利用缓存只更新部分文件的功能，这个能在github action实现吗？ -->
 <!-- 怎么用gemini cli做llm？ -->

## ollama run gemma3:1b-it-qat
wandb token:2a69e4f62fe6b6784160c54e633ffdf133f3a48c
显卡是amd radeon graphics processor 0x1681，16内存，处理器是amd ryzen 7 6800hs
- 使用save & run all(commit)跑，并删除跟模型(/kaggle/working/f*.tar.gz)无关的文件后再下载。模型比较大，浏览器直接下载很慢，在cmd用kaggle命令下载
- kaggle kernels output ceriac/gemma3-kaggle-train-lora -p "D:\workspace-lilyco\lilyco_storybook\model"
- USE Modelfile to build model
- ollama list
- ollama create gemma3-4b-finetuned -f ./Modelfile
- ollama run gemma3-4b-finetuned 
- model runner has unexpectedly stopped, this may be due to resource limitations or an internal error, check ollama server logs for details

## build
npx wrangler pages dev ./public --port=8788
npx next build
npx wrangler pages deploy
