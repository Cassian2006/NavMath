# 操作日志

说明：
- 本文件用于记录我对仓库执行的实际操作。
- 记录格式为“时间戳 + 操作内容”，统一使用中文。
- 从本次开始，后续每次实际修改、移动、校验或生成文件，都会继续追加到本文件。

## 2026-03-20 19:39:54 +08:00

- 读取仓库目录与 `readme.md`，确认项目需要从零实现 MVP。
- 创建项目基础目录：`app/`、`app/services/`、`templates/`、`static/`、`data/`。
- 新建后端文件，完成 `FastAPI` 服务骨架、知识点匹配、公式绘图、OCR 接口封装。
- 新建前端页面与静态资源，完成单页输入、结果展示与 Plotly 图形渲染。
- 新建本地样例知识库 `data/knowledge_base.json`。
- 新建 `requirements.txt`、`run.py` 与 `.gitignore`。
- 更新 `readme.md`，补充当前 MVP 已实现内容、目录结构、启动方式与 OCR 说明。
- 安装项目依赖，并执行 Python 语法级校验，确认核心文件可编译。
- 将用户提供的 `superiorMath` 与 `sealesson` 中的原始资料移动到：
  - `data/raw_materials/advanced_algebra/`
  - `data/raw_materials/ship_security_course/`
- 新建 `data/source_manifest.json`，登记原始资料分类、用途与后续处理流程。
- 执行接口验证，确认 `/api/health` 与 `/api/analyze-text` 可正常返回结果。
- 尝试删除已迁移后的空目录 `superiorMath` 与 `sealesson`，但被当前策略拦截，目录目前仍保留在仓库根目录。
- 新建本日志文件 `AGENT.md`，用于持续记录后续操作。

## 2026-03-20 19:43:08 +08:00

- 在桌面创建 `知识点模板.csv`，写入字段定义、填写要求和两条例子，供队友整理知识点数据使用。
- 在桌面创建 `题目模板.csv`，写入字段定义、填写要求和两条例子，供队友整理题库数据使用。
- 按用户要求继续维护本日志文件，记录本次模板创建操作。

## 2026-03-20 19:48:22 +08:00

- 修正 `app/main.py`、`app/services/math_plot.py`、`data/knowledge_base.json` 等文件中的中文内容，避免出现乱码文本。
- 扩展知识库结构，加入“高等数学 + 船舶保安”双课程的样例知识点与问答数据。
- 在 `app/services/knowledge.py` 中加入知识点匹配、课程识别和后续 CSV 导入预留逻辑。
- 在 `app/services/math_plot.py` 中加入 MATLAB 示例代码生成与教学提示生成。
- 新建 `app/services/visualization.py`，吸收 `teaching` 项目中可复用的预设三维图形能力，作为非公式输入时的演示图形后备能力。
- 更新前端页面与脚本，新增知识点问答展示区、MATLAB 代码区和教学提示区。
- 检查 `C:\Users\sgddsf\Desktop\teaching` 目录，确认其中“固定模板图形 + MATLAB 代码”部分可复用，但不直接沿用其硬编码流程。

## 2026-03-20 19:52:49 +08:00

- 定位到 `teaching` 复用代码中的中文关键词出现编码污染，导致“圆环面”等中文图形名称无法被匹配。
- 重写 `app/services/visualization.py` 中的中文别名与展示文案，改为稳定的 Unicode 转义写法，保证中文匹配可用。
- 同步修正 `app/main.py` 中的后备提示文案，避免继续出现乱码字符串。

## 2026-03-20 20:00:42 +08:00

- 重做前端主页面结构，加入三种结果模式展示：题目解析、知识问答、图形演示。
- 在前端加入 CSV 状态区与上传区，支持后续直接上传 `knowledge_points.csv` 和 `problems.csv`。
- 新增 `app/services/imports.py`，并在后端提供 `/api/import-status` 与 `/api/import-csv` 接口。
- 重写 `app/services/knowledge.py` 中的课程识别与 CSV 导入逻辑，修正可见的中文乱码点。
- 更新 `app/main.py`，增加 `view_mode` 返回字段和导入接口。
- 在 `data/imports/` 下创建占位目录，作为队友整理后的 CSV 落盘位置。

## 2026-03-20 20:04:03 +08:00

- 调整 `view_mode` 判定逻辑，使船舶保安这类纯知识问答优先进入“知识问答”模式，而不是被归入题目解析。
- 准备继续验证 CSV 上传接口和三种前端模式的联调结果。

## 2026-03-20 20:04:57 +08:00

- 使用临时样例文件验证 `/api/import-csv` 和 `/api/import-status` 接口可用，确认 CSV 上传后能够落盘并计数。
- 验证完成后删除测试产生的 `data/imports/knowledge_points.csv`，避免干扰后续接入队友的真实数据。

## 2026-03-20 20:17:51 +08:00

- 按用户要求将前端切换为独立的 `Vue + Vite` 工程，新增 `frontend/` 目录及 `package.json`、`vite.config.js`、`src/App.vue` 等核心文件。
- 将原有页面能力迁移到 Vue 单文件组件中，保留题目解析、知识问答、图形演示、CSV 上传和 Plotly 绘图能力。
- 将 FastAPI 入口改为纯 API 服务，去除模板页面依赖，新增跨域配置以支持 `Vite` 开发服务器访问后端接口。
- 更新 `.gitignore`，忽略 `frontend/node_modules/` 和 `frontend/dist/`。
- 本机当前未安装 `node/npm`，因此本轮无法实际执行 `vite dev` 和 `vite build`，仅完成工程结构与代码迁移。

## 2026-03-20 20:53:12 +08:00

- 使用 `winget` 安装 Node.js LTS，并确认 `node` 与 `npm` 可用。
- 在 `frontend/` 目录执行 `npm install`，完成 Vue + Vite 前端依赖安装。
- 启动后端开发服务 `python run.py`，确认 `http://127.0.0.1:8000/api/health` 返回正常。
- 启动 Vite 开发服务，确认 `http://127.0.0.1:5173/` 可访问。
- 执行 `npm run build`，确认 Vue 前端可以成功生成生产构建。
- 记录构建告警：当前打包出的前端主包较大，后续需要处理 Plotly 带来的体积问题。

## 2026-03-20 20:57:31 +08:00

- 将 `frontend/src/App.vue` 拆分为多个组件：输入区、结果区、图形区、导入区和头部区，降低单文件复杂度。
- 新建 `frontend/src/composables/useAiTeacher.js`，集中管理前端状态、API 调用和 Plotly 渲染逻辑。
- 保留现有功能不变的前提下完成前端组件化，便于后续继续扩展样式、模式和接口。

## 2026-03-20 21:12:30 +08:00

- 将 `frontend/src/composables/useAiTeacher.js` 中的 `Plotly` 改为动态导入，避免首屏主包直接包含整个绘图库。
- 在 `frontend/vite.config.js` 中为 `plotly.js-dist-min` 单独设置构建拆包，进一步减轻主包压力。
- 保持当前图形展示功能不变，仅优化前端加载策略和打包结果。

## 2026-03-20 21:15:04 +08:00

- 继续优化图表加载方式，将前端中的 Plotly 改为运行时从 CDN 按需加载，不再进入 Vite 构建产物。
- 从 `frontend/package.json` 中移除 `plotly.js-dist-min` 依赖，避免无效打包和依赖膨胀。
- 移除 `vite.config.js` 中仅为 Plotly 服务的手动拆包配置，转为更轻的 CDN 方案。

## 2026-03-20 21:18:39 +08:00

- 检查前后端开发服务状态，确认后端 `http://127.0.0.1:8000/api/health` 可访问。
- 检查前端 Vite 开发服务状态，确认 `http://127.0.0.1:5173/` 可访问。
- 当前无需重复启动服务，直接继续使用现有运行中的前后端实例。

## 2026-03-20 21:20:56 +08:00

- 在 `data/imports/knowledge_points.csv` 中加入 5 条演示知识点，覆盖高等数学与船舶保安两门课程。
- 在 `data/imports/problems.csv` 中加入 5 条演示例题，覆盖题目解析、知识问答和图形演示三类场景。
- 使用项目既定的 CSV 接入结构落样例数据，确保前端当前即可读取并展示导入数据效果。

## 2026-03-20 21:23:47 +08:00

- 新建 `app/services/llm_plot.py`，用于在配置 `DEEPSEEK_API_KEY` 后调用 DeepSeek 将自然语言绘图需求转成结构化绘图意图和 MATLAB 代码。
- 重写 `app/main.py`、`app/services/math_plot.py`、`app/services/visualization.py`，将“本地规则绘图 + DeepSeek 语义转述 + MATLAB 代码兜底”三层链路接起来。
- 当前实现策略为：能本地识别的直接本地出图；识别不了且配置了 DeepSeek 时，优先转公式或预设图形，否则至少返回 MATLAB 代码。

## 2026-03-20 21:23:47 +08:00（更新）

- 按用户要求将自然语言绘图的 LLM 中间层从 DeepSeek 调整为 Kimi / Moonshot API。
- `app/services/llm_plot.py` 现优先读取 `KIMI_API_KEY` 或 `MOONSHOT_API_KEY`，默认调用 `https://api.moonshot.cn/v1/chat/completions`。

## 2026-03-20 21:23:47 +08:00（联调）

- 重启后端进程，并通过环境变量方式为当前运行中的服务注入 Kimi API Key，未将密钥写入代码仓库文件。
- 使用自然语言绘图请求验证 Kimi 链路，确认模型可将自然语言转成公式、MATLAB 代码和前端可视化所需的绘图结果。

## 2026-03-20 21:49:32 +08:00

- 修正公式抽取逻辑，避免把“判断曲面 z = x^2 - y^2 的类型”整句题干误当成公式送入 SymPy。
- 在 `app/services/math_plot.py` 中加入公式提纯函数，支持从中文题干中提取真正的 `x=`、`y=`、`z=` 表达式。
- 同步清理 `app/main.py` 中与绘图失败相关的后端提示文本，减少旧乱码残留对排查的干扰。

## 2026-03-20 21:51:25 +08:00

- 继续收紧公式提纯规则，避免正则把中文后缀如“的类型”继续吞进公式表达式。
- 将公式字符集限制为数学表达式常见 ASCII 字符，并在提纯时遇到中文字符立即截断。

## 2026-03-20 21:57:53 +08:00

- 修正前端三维图形空白问题，将 Plotly 绘图容器改为由 `PlotPanel` 在挂载后主动回传真实 DOM 节点。
- 在前端结果区新增“处理进程”模块，实时显示输入识别、知识点匹配、绘图生成和结果整理四个阶段的状态。
- 执行 `frontend` 的生产构建验证，确认这轮前端联动修改未破坏 Vue 工程。

## 2026-03-20 21:43:44 +08:00

- 将 Kimi 配置改为项目级持久化方案，新增项目根目录 `.env` 与 `.env.example`。
- 在 `app/main.py` 中接入 `.env` 自动加载，使后端重启后仍能读取 Kimi 配置。
- 在 `.gitignore` 中加入 `.env`，避免后续误提交本地密钥文件。
- 在 `requirements.txt` 中补充 `python-dotenv` 依赖声明，保证环境重建时配置读取能力可用。

## 2026-03-21 22:26:21 +08:00

- 检查仓库根目录新增的 `高等数学下册（同济大学第八版）.xlsx`，确认字段与当前知识点模板一致，内容为 `77` 条高等数学知识点。
- 为本地环境安装 `openpyxl`，并在 `requirements.txt` 中补充 `pandas` 与 `openpyxl` 依赖声明，避免后续环境重建后无法读取 Excel。
- 修改 `app/services/knowledge.py`，让导入层同时支持 `CSV` 和 `XLSX` 两种表格格式，并将导入状态改为自动识别实际存在的导入文件。
- 将 `高等数学下册（同济大学第八版）.xlsx` 转换覆盖到 `data/imports/knowledge_points.csv`，使系统当前直接加载这批教材知识点。
- 通过本地脚本验证导入状态，确认当前导入计数为 `knowledge_points = 77`、`problems = 5`，知识点文件已被系统实际读入。

## 2026-03-22 21:24:29 +08:00

- 检查仓库新增的 `高等数学上.xlsx` 与 `远洋运输业务题库.xlsx`，确认两者均为题库结构，字段与现有 `problems.csv` 模板一致。
- 更新 `app/services/knowledge.py` 中的课程识别与匹配规则，新增远洋运输相关关键词，并加入更宽松的文本简化匹配，避免自由问句因“是什么”等尾缀差异而错配到旧题库。
- 将两份新题库合并写入 `data/imports/problems.csv`，保留原有 5 条演示题，并为新增题目补上 `MATHUP-` 与 `OCEAN-` 前缀，避免不同来源的题号冲突。
- 通过本地脚本验证题库导入结果，确认当前导入计数为 `knowledge_points = 77`、`problems = 55`。
- 用实际问句回归验证两条链路：`国际贸易术语的主要作用是什么` 已命中远洋运输题库，`计算极限 lim(x→0) sinx/x` 已命中高等数学上题库。

## 2026-03-22 21:47:32 +08:00

- 新增 `app/services/llm_answer.py`，复用当前 Kimi 配置，为“本地未命中时由 Kimi 直接回答”提供二级中转服务。
- 调整 `app/main.py` 的主链路顺序：先做本地题库、知识点、公式记录检索；仅在本地确实未命中时才调用 `answer_question_with_kimi`。
- 收紧自然语言绘图链路，只在明显包含绘图意图时才调用 Kimi 做绘图转述，避免普通问答被误标记成 `parser = kimi`。
- 通过三组回归验证新逻辑：远洋运输题目问答保持本地命中；本地不存在的概念题 `什么是狄拉克函数` 会由 Kimi 直接回答；自然语言绘图请求仍会走 Kimi 绘图转述。

## 2026-03-25 08:37:41 +08:00

- 将项目对外名称统一调整为 `智绘数航`，更新了后端 API 标题与前端页面标题。
- 重写 `frontend/src/components/HeroSection.vue`、`InputPanel.vue`、`ResultPanel.vue`、`PlotPanel.vue`、`ImportPanel.vue` 以及 `frontend/src/composables/useAiTeacher.js`，清理旧的乱码文案并统一为正常中文界面文本。
- 在前端结果区新增“答案来源”展示，区分 `本地知识库` 与 `Kimi 二级中转`，便于演示时说明系统链路。
- 通过 `npm run build` 验证前端构建成功，并用三组样例回归验证后端分支：本地题库命中、Kimi 二级问答、Kimi 自然语言绘图均正常。

## 2026-03-25 08:46:00 +08:00

- 将 `AiTeacher` 的英文对外名称统一替换为 `NavMath Vision`，更新了后端 API 名称、前端页面标题以及前端包名。
- 将前端状态管理文件重命名为 `frontend/src/composables/useNavMathVision.js`，并同步更新 `App.vue` 的引用。
- 在后端 `app/main.py` 中新增 `source_detail` 返回字段，用于区分“本地题库命中”“本地知识点命中”“Kimi 二级中转回答”“Kimi 绘图转述”等不同来源。
- 在前端结果区补充来源细节展示，不再只显示 `本地知识库` / `Kimi 二级中转`，而是给出更完整的链路说明。
- 再次执行前端构建与三组回归测试，确认 `NavMath Vision` 命名更新和来源说明增强未破坏现有功能。

## 2026-03-25 08:45:10 +08:00

- 在 `app/services/knowledge.py` 中新增本地命中评分函数，为题库和知识点匹配提供可量化分数。
- 在 `app/main.py` 中新增 `match_meta` 返回字段，包含命中类型、命中分数和置信度标签，用于前端展示更细的判定信息。
- 重写 `frontend/src/components/ResultPanel.vue` 与 `frontend/src/composables/useNavMathVision.js`，在结果区新增“命中类型”和“置信度”标签展示。
- 重写 `frontend/src/components/HeroSection.vue`，加入可直接点击的答辩演示样例入口，覆盖高数曲面、高数极限、远洋运输问答、Kimi 兜底、自然语言绘图五类场景。
- 更新 `frontend/src/styles.css` 以支持首页演示样例卡片样式，并再次通过前端构建和三组接口回归验证本轮改动。

## 2026-03-25 09:31:16 +08:00

- 继续强化答辩展示层，重写 `frontend/src/components/HeroSection.vue`，新增能力卡片与固定演示流程说明，方便现场按顺序演示。
- 重写 `frontend/src/components/ResultPanel.vue`，加入课程徽标展示，并用不同课程样式区分高等数学与远洋运输业务。
- 重写 `frontend/src/composables/useNavMathVision.js`，清理旧乱码文本，补充课程徽标计算逻辑与更完整的答辩样例数据。
- 更新 `frontend/src/styles.css`，为能力卡片、演示流程、课程徽标等展示元素补充样式。
- 再次执行前端构建与三组接口回归，确认新增展示层未破坏本地命中、Kimi 二级中转和自然语言绘图链路。

## 2026-03-25 09:35:03 +08:00

- 继续加强首页答辩展示信息，在 `frontend/src/components/HeroSection.vue` 中新增“系统架构流转”和“答辩前检查”两个展示块。
- 更新 `frontend/src/styles.css`，为架构流转卡片和检查清单补充样式，提升首页信息表达的完整度。
- 执行前端构建验证，确认新增展示块未影响 Vue 页面打包与现有交互。
## 2026-03-25 10:07:33 +08:00

- 重新创建 `frontend/src/components/HeroSection.vue`，补回缺失的首页组件，并加入“答辩模式”入口、能力卡片、系统架构流转和答辩前检查。
- 重写 `frontend/src/composables/useNavMathVision.js`，清理前端乱码文案，保留原有绘图与导入逻辑，并新增答辩模式状态、开始演示、下一条演示和退出演示能力。
- 重写 `frontend/src/components/InputPanel.vue`、`ResultPanel.vue`、`PlotPanel.vue`、`ImportPanel.vue`，统一当前前端的中文文案和展示说明。
- 重写 `readme.md`，同步为 `智绘数航 / NavMath Vision` 的当前真实架构、数据规模、启动方式和系统链路说明。
## 2026-03-25 10:14:11 +08:00

- 检查本地 `8000` 与 `5173` 端口监听状态，确认前后端均未运行。
- 后台启动 FastAPI 后端，并通过 `http://127.0.0.1:8000/api/health` 验证服务正常返回 `{"status":"ok"}`。
- 后台启动 Vue + Vite 前端开发服务，第一次静默启动未成功后改为输出 `frontend/frontend-dev.log` 的方式重新拉起，并确认 `http://127.0.0.1:5173/` 返回 `200`。
## 2026-03-25 10:18:59 +08:00

- 按用户要求把主页面中的“答辩模式”调整为“演示模式”，并从主页面抽离出去。
- 重写 `frontend/src/components/HeroSection.vue`，让主页恢复为正常交互视角，只保留系统介绍、能力卡片、样例入口和跳转到演示页面的链接。
- 新增 `frontend/src/DemoPage.vue`，将固定演示流程、样例切换和演示控制独立到 `/demo` 页面。
- 更新 `frontend/src/main.js`，根据当前路径在主页与演示页之间切换挂载组件；更新 `frontend/src/styles.css` 以支持页面跳转按钮样式。
- 执行 `npm run build`，确认主页面与演示页面拆分后前端构建仍然通过。
## 2026-03-25 10:24:43 +08:00

- 新增 `frontend/src/components/TopNav.vue`，在页面右上角加入主页面与演示模式的统一切换入口。
- 重写 `frontend/src/components/HeroSection.vue`，弱化主页面中的演示导向，让主页面回到正常产品首页视角。
- 重写 `frontend/src/components/ResultPanel.vue`，将“处理进程”上移到“题目解析”之后，并将数据接入状态收敛为低强调度的底部信息。
- 调整 `frontend/src/components/ImportPanel.vue`，加入紧凑模式；在主页和演示页中都将 CSV 导入区下沉到页面最底部，降低工程信息展示权重。
- 重写 `frontend/src/DemoPage.vue` 与 `frontend/src/styles.css`，统一导航、卡片层级、页头结构和底部导入区样式，完成一轮整体 UI 结构梳理。
- 再次执行 `npm run build`，确认本轮页面结构和样式调整未破坏前端构建。
## 2026-03-25 10:29:02 +08:00

- 重写 `frontend/src/composables/useNavMathVision.js`，修复前端请求层在后端返回纯文本错误时直接执行 `response.json()` 导致的 `Unexpected token 'I'` 报错，并统一为可读错误提示。
- 直接调用 `app/services/llm_answer.py` 中的 `answer_question_with_kimi` 测试 Kimi 兜底链路，确认当前上游返回 `HTTP 429`，错误类型为 `engine_overloaded_error`，说明账号配置有效但当前被限流或上游拥塞。
- 修改 `app/main.py`，为 `/api/analyze-text` 和 `/api/analyze-image` 增加结构化错误返回；当 Kimi 或其他上游抛出异常时，接口将返回 JSON 格式的 `detail`，不再向前端抛出纯文本 `Internal Server Error`。
- 重启本地后端服务，并通过 `http://127.0.0.1:8000/api/health` 再次确认服务正常。
## 2026-03-25 10:32:33 +08:00

- 按用户要求优化 Kimi 问答的“回答格式”而不是单纯调整字段名，重写 `app/services/llm_answer.py` 的提示词与结果规范化逻辑。
- 保持现有前后端接口兼容，但要求模型在 `solution` 中按“先直接结论，再解释，再给提示”的教学式正文输出，在 `analysis_steps` 中返回 3 到 4 条简洁步骤说明。
- 为 Kimi 问答结果增加后端二次规范化，统一补齐 `title`、`course`、`knowledge_points`、`analysis_steps`、`solution`、`question`、`answer` 等字段，降低模型输出轻微漂移对主流程的影响。
- 通过 `py_compile` 对 `app/services/llm_answer.py` 做语法检查，确认修改后的模块可正常加载。
## 2026-03-25 10:34:11 +08:00

- 定位“国际贸易术语的主要作用是什么”渲染成逐字换行的问题，确认原因是本地题库中的 `analysis_steps` 仍是使用 `|` 拼接的字符串，前端按列表渲染时把字符串当成字符序列处理。
- 修改 `app/main.py`，新增本地题目与知识点结果标准化逻辑，将 `analysis_steps`、`knowledge_points`、`options`、`keywords` 等字段统一转换为标准数组结构。
- 重启本地后端并回归验证 `http://127.0.0.1:8000/api/analyze-text`，确认 `matched_problem.analysis_steps` 已变为 `list` 类型。
## 2026-03-25 10:43:15 +08:00

- 按用户要求删除前端“公式输入”字段，将输入区改为单一主输入框，统一承载问题、纯公式和图形描述三类输入。
- 重写 `frontend/src/components/InputPanel.vue`，更新标题、说明和占位提示，明确系统会自动判断输入类型。
- 更新 `frontend/src/App.vue`、`frontend/src/DemoPage.vue` 与 `frontend/src/composables/useNavMathVision.js`，移除前端对 `formula` 状态的依赖，样例数据也统一改为单文本输入。
- 执行 `npm run build`，确认单输入框改动后前端构建仍然通过。
## 2026-03-25 13:34:59 +08:00

- 重写 `app/services/knowledge.py`，清理乱码字符串，收紧本地匹配规则，加入最低命中分数，并在加载知识库时过滤明显损坏的题库/知识点记录。
- 重写 `app/main.py`、`app/services/llm_answer.py`、`app/services/llm_plot.py`、`app/services/math_plot.py`，统一中文文案、错误信息、绘图提示和 Kimi 提示词。
- 通过 `py_compile` 对后端核心模块做语法检查，并重启本地 FastAPI 服务。
- 使用接口回归验证三条关键链路：`国际贸易术语的主要作用是什么？` 重新命中本地题库；随机非课程问题切换到 Kimi 二级中转；`判断曲面 z = x^2 - y^2 的类型` 仍能命中本地绘图链路。
- 再次通过 `http://127.0.0.1:8000/api/health` 确认后端服务正常。
## 2026-03-25 13:50:05 +08:00

- 重写 `frontend/src/components/HeroSection.vue`、`frontend/src/components/ResultPanel.vue`、`frontend/src/components/InputPanel.vue`、`frontend/src/DemoPage.vue` 和 `frontend/src/composables/useNavMathVision.js`，清理当前用户可见页面中的残留乱码文案。
- 统一修正首页说明、示例标题、输入区提示、演示页说明、状态提示和错误提示，使前端展示恢复为正常中文。
- 执行 `npm run build`，确认本轮前端文案重写后构建仍然通过。
## 2026-03-25 13:52:59 +08:00

- 按用户要求取消独立演示页面的实际内容，保留页面切换结构但将 `/demo` 改为占位页。
- 重写 `frontend/src/components/TopNav.vue`，统一顶部切换为“主页面 / 页面占位”。
- 重写 `frontend/src/DemoPage.vue`，改为后续扩展的占位页面，不再重复主页面已有的演示交互。
- 再次执行 `npm run build`，确认占位页调整后前端构建仍然通过。
## 2026-03-25 13:54:54 +08:00

- 按用户要求删除主页面首页中的技术栈标签，不再在首屏展示 `Vue + Vite`、`FastAPI`、`本地知识库优先`、`Kimi 二级兜底` 等技术性信息。
- 重写 `frontend/src/components/HeroSection.vue`，同时清理该组件中的残留乱码文案，并将流程文案改为更面向用户的表达。
- 执行 `npm run build`，确认首页精简后前端构建仍然通过。
## 2026-03-25 21:53:15 +08:00

- 重写 `app/services/knowledge.py`，清理乱码并把本地检索升级为“弱语义推理”版本，加入问法归一化、术语别名扩展和多维评分逻辑。
- 重写 `app/main.py`、`app/services/llm_answer.py`、`app/services/llm_plot.py`、`app/services/math_plot.py`，统一清理中文乱码、修正 Kimi 提示词和绘图提示词，并整理主链路返回文案。
- 在 `requirements.txt` 中补充 `pytest` 与 `httpx` 依赖，准备后续按约定在大改后执行测试。
- 新建 `tests/test_api.py` 与 `tests/test_matching.py`，覆盖健康检查、公式绘图链路、远洋运输业务弱语义命中和无关问题不误命中等关键场景。
- 新建 `docs/智绘数航技术说明.md`，整理项目定位、技术架构、弱语义检索、绘图逻辑、Kimi 角色、OCR 边界和答辩口径，供后续现场说明使用。
- 执行 `python -m compileall app tests`，确认本轮后端与测试文件语法通过。
- 执行 `python -m pytest`，共 5 项测试全部通过。
- 检查当前目录 Git 状态，确认仓库尚未初始化，准备下一步执行 `git init`、绑定远程仓库并尝试推送。
