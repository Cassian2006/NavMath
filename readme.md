# 智绘数航 / NavMath Vision

面向高等数学与航运课程的学习辅助系统 MVP。

当前版本聚焦两门课程：

- 高等数学
- 远洋运输业务

系统已经具备以下核心能力：

- 题目解析与知识点问答
- 本地知识库优先检索
- 本地未命中时由 Kimi 二级中转回答
- 公式绘图与自然语言绘图
- 二维函数与三维曲面可视化
- MATLAB 示例代码生成
- 知识点表与题目表导入

## 当前状态

当前仓库已经不是早期静态原型，而是一套可运行的前后端分离 MVP：

- 后端：FastAPI
- 前端：Vue + Vite
- 图形：Plotly，前端按需从 CDN 加载
- 大模型：Kimi / Moonshot

本地已接入的数据规模：

- 知识点：77 条
- 题目：55 条

其中数据来源已覆盖：

- 高等数学上、下册知识点与题目
- 远洋运输业务题库

## 系统链路

系统当前采用“本地优先，模型兜底”的混合模式：

1. 用户输入题目、公式、自然语言图形描述，或上传图片。
2. 后端先做课程识别、文本清洗、本地题库和知识点匹配。
3. 如果识别到公式或绘图意图，则生成二维/三维图形和 MATLAB 代码。
4. 如果本地问答未命中，则调用 Kimi 进行二级回答。
5. 前端统一展示答案来源、命中类型、置信度、处理进程和图形结果。

## 已实现功能

### 1. 高等数学

- 支持公式输入，例如 `z = x^2 - y^2`
- 支持从中文题干中自动提取公式
- 支持自然语言绘图，例如“画一个像帐篷一样中间高四周低的三维曲面”
- 支持二维函数与三维曲面展示
- 支持返回 MATLAB 绘图代码

### 2. 远洋运输业务

- 支持本地题库问答
- 支持本地知识点检索
- 本地未命中时自动切换到 Kimi 补答

### 3. 数据导入

- 支持 `CSV` 导入
- 支持 `XLSX` 导入
- 当前导入层已适配知识点表和题目表

## 目录结构

```text
app/
  main.py                     # FastAPI 入口
  services/
    imports.py                # CSV 导入接口
    knowledge.py              # 课程识别、知识检索、题库匹配
    llm_answer.py             # Kimi 二级问答
    llm_plot.py               # Kimi 自然语言绘图转述
    math_plot.py              # 公式解析与绘图数据生成
    ocr.py                    # OCR 封装
    visualization.py          # 预设图形与可视化辅助
data/
  imports/
    knowledge_points.csv      # 当前知识点数据
    problems.csv              # 当前题目数据
frontend/
  src/
    components/               # Vue 组件
    composables/              # 前端状态与接口逻辑
  vite.config.js
AGENT.md                      # 仓库操作日志
requirements.txt
readme.md
```

## 环境要求

### 后端

- Python 3.11+

安装依赖：

```bash
pip install -r requirements.txt
```

### 前端

- Node.js 18+

安装依赖：

```bash
cd frontend
npm install
```

## 环境变量

项目根目录支持通过 `.env` 读取 Kimi 配置。

示例：

```env
KIMI_API_KEY=your_api_key
KIMI_API_BASE=https://api.moonshot.cn/v1
KIMI_MODEL=moonshot-v1-8k
```

说明：

- `.env` 仅保留在本地，不应提交到仓库
- 当前项目已经按项目级方式读取 `.env`

## 启动方式

### 1. 启动后端

在仓库根目录执行：

```bash
uvicorn app.main:app --reload
```

默认地址：

```text
http://127.0.0.1:8000
```

健康检查：

```text
http://127.0.0.1:8000/api/health
```

### 2. 启动前端

在 `frontend` 目录执行：

```bash
npm run dev
```

默认地址：

```text
http://127.0.0.1:5173
```

前端已在 `vite.config.js` 中代理 `/api` 到本地后端。

### 3. 一键重启前后端

仓库根目录提供了一个 Windows 脚本：

```bat
start_dev.cmd
```

作用：

- 自动清理占用 `8000` 和 `5173` 端口的旧进程
- 在两个新命令行窗口中分别启动后端和前端

### 4. 一键执行基础检查

仓库根目录提供了一个开发检查脚本：

```bat
dev_check.cmd
```

作用：

- 运行后端 `pytest`
- 运行前端生产构建检查

## 演示示例

可以直接用这些问题测试：

- `判断曲面 z = x^2 - y^2 的类型`
- `计算极限 lim(x→0) sinx/x`
- `国际贸易术语的主要作用是什么`
- `什么是狄拉克函数`
- `请画一个像帐篷一样中间高四周低的三维曲面，并给我 MATLAB 代码`

## OCR 说明

当前 OCR 采用本地方案：

- Python `pytesseract`
- 本机 `Tesseract OCR` 引擎

优点：

- 不按调用次数收费
- 可以离线部署

局限：

- 中文复杂版面识别不稳定
- 数学公式识别效果有限
- 不适合作为正式结构化数据主来源

因此当前项目的主数据策略仍然是：

- 人工整理知识点表和题目表为主
- OCR 作为补充输入手段

## 当前开发重点

当前最适合继续推进的方向：

- 扩充高等数学与远洋运输业务数据
- 提升本地知识匹配效果
- 继续完善高数可视化场景
- 准备项目申报与答辩展示材料
