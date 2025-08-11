## how to use generate_storybook.py

### 首先，完全关闭所有正在运行的 Edge 浏览器窗口。

### 然后，在命令行（CMD 或 PowerShell）中运行下面的命令：
`"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir="C:\edge-debug-profile"`

### 运行这个命令后，执行generated_stprybook.py


## ai agent
- 在这个路径生成python文件。写个函数，函数输入是类型string的a和int类型的b和int类型的c和函数d，操作是d生成json格式的回答，内容是b条c字左右字符串的数组，每一条是一个跟a有关很短的小故事，函数输出是这个list。这里的形参你改成合适的名字。 

- 在这个路径生成python文件。使用langchain写个ai agent，任务是根据输入提示词，生成多个短故事，再生成图片，再上传到cloudinary。可用的tool有。agent和提示词生成多个短故事都使用gemini cli，这一步如果做不到使用dummy的llm，生成的方法叫invoke。
    - generate_stories.py的generate_stories_by_generation_func，它根据提示词生成多个短故事
    - generate_storybooks.py的run，它用短故事生成图片，保存到本地
    - cloudinary_util的main，它把生成的图片上传到cloudinary
    