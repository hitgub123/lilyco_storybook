
<iframe src="desc/workflow.md" style="width:100%;height:500px;"></iframe>

# 项目介绍：Lilyco Storybook 自动化创作平台

##  项目概述

`lilyco_storybook` 是一个旨在探索和学习前沿技术的全栈项目。其核心目标是构建一个自动化的内容创作流水线，特别是用于生成“故事绘本”。

整个项目从后端的内容生成、AI Agent 的任务编排，到前端的内容展示，构成了一个完整的端到端应用。它不仅仅是一个应用，更是一个学习和实践以下技术的试验场：
- 大语言模型（LLM）的智能代理（Agent）技术
- 本地化大模型的部署与使用
- 先进的 Web 前端框架
- Serverless 架构和云服务集成

## 2. 核心架构

本项目主要由两大核心部分组成：

- **后端自动化核心 (`/batch`)**: 使用 Python 构建，是整个内容创作的“大脑”。它负责接收指令，通过 AI Agent 和工作流来执行多步骤任务，如生成故事、生成图片、上传资源并最终更新数据库。

- **前端展示平台 (`/web`)**: 使用现代 Web 技术栈构建，负责将后端生成的绘本故事优雅地展示给最终用户。同时，它也包含了与后端服务进行交互的接口。

## 3. 技术栈详解

### 后端 & AI 自动化 (`/batch`)

- **主要语言**: **Python**

- **AI 核心框架**: **LangChain**
  - **智能代理 (Agents)**: 项目深入使用了 `AgentExecutor` 和 `create_tool_calling_agent` 来构建能够自主决策、并行调用工具的智能代理。
  - **图工作流 (Graphs)**: 探索了 `LangGraph` 来编排更稳定、更可控的工作流。实践了两种模式：
    1.  **Agentic Loop**: 通过条件节点（如 `should_call_tool`）让 Agent 自主循环决策。
    2.  **State Machine**: 通过路由（Router）节点实现一个确定性的、按预定顺序执行的有限状态机工作流。
  - **模型集成**: 实践了多种大语言模型（LLM）的集成方式：
    - `langchain-google-genai`: 用于调用 Google 的 **Gemini** 系列模型。
    - `langchain-ollama`: 用于与本地部署的开源模型进行交互。

- **本地 LLM 运行环境**: **Ollama**
  - 这是项目的一大亮点。通过 Ollama，成功在本地运行了多个强大的开源模型，并将其集成到 LangChain Agent 中，实现了模型的私有化部署和无限次调用。
  - **实践过的模型**: Phi-3 , Gemma 3 等。

- **云服务与外部工具**:
  - **Cloudinary**: 用于存储和管理由 AI 生成的图片资源。
  - **Cloudflare D1**: 作为项目的无服务器（Serverless）数据库，存储最终的故事和绘本数据。
  - **Node.js**: 通过 Python 的 `subprocess` 调用 Node.js 脚本来执行与数据库的交互，展示了跨语言协作的能力。

### 前端 & Web 平台 (`/web`)

- **核心框架**: **Next.js (React)**
  - 项目的前端主体采用 Next.js 构建，这是一个业界领先的 React 框架，提供了服务端渲染（SSR）、静态站点生成（SSG）等强大功能。

- **UI 样式**: **Tailwind CSS**
  - 使用了流行的原子化 CSS 框架 Tailwind CSS，能够快速构建现代化、响应式的用户界面。

- **部署与服务平台**: **Cloudflare 全栈生态**
  - **Cloudflare Pages**: 用于托管和全球分发通过 Next.js 构建的静态前端站点。
  - **Cloudflare Workers**: 用于编写和部署独立的、高性能的 Serverless API 端点。
  - **Cloudflare Pages Functions**: 结合静态站点，提供服务端的 API 功能，实现了真正的前后端一体化边缘计算。

### 跨领域技术

- **数据库**: **Cloudflare D1**，通过编写原生 SQL (`schema.sql`) 进行表结构管理。
- **版本控制**: **Git / GitHub**，用于代码管理和（通过 `.github/workflows`）CI/CD 自动化部署。

## 4. 核心工作流解读

项目实现了一个完整的自动化内容创作与部署流程：
1.  **任务启动**: 用户通过命令行或前端界面给出一个故事主题。
2.  **故事生成**: 后端的 LangChain Agent 或 LangGraph 工作流接收到主题，调用第一个工具（LLM），生成故事文本。
3.  **图片生成**: 工作流根据生成的故事文本，调用图片生成工具，创造出与故事匹配的绘本图片。
4.  **资源上传**: 图片被上传到 Cloudinary，并返回一个可公开访问的 URL。
5.  **数据入库**: 包含故事文本、图片 URL 等信息的最终数据，被写入到 Cloudflare D1 数据库中。
6.  **静态站点构建**: 数据更新后，Next.js 前端应用在本地（或通过 CI/CD）被构建为优化的静态文件（HTML/CSS/JS）。
7.  **部署到边缘网络**: 构建好的静态文件被无缝部署到 **Cloudflare Pages**。
8.  **全球访问**: 用户最终通过 Cloudflare Pages 提供的全球 CDN 网络访问这个静态站点，浏览最新的绘本故事。

该项目充分展现了如何将多种现代技术栈有机地结合起来，打造一个功能强大且有趣的自动化应用。
