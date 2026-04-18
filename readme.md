# 智绘数航 / NavMath Vision

数学可视化与航运知识融合学习辅助系统。

当前仓库已经不是早期概念原型，而是一套可运行的前后端分离 MVP，核心能力分为两条主线：

- 数学公式识别、函数可视化、MATLAB 代码导出
- 航运知识检索、题库匹配、动画教学场景演示

## 1. 当前进展概览

当前版本已经完成的重点如下：

- 首页交互链路已打通：提问、随机示例、结果展示、图形展示、CSV 导入都可用
- 后端已支持本地知识检索优先、模型兜底回答
- 绘图系统已升级为统一中间层驱动，前端出图和 MATLAB 导出共用一套逻辑
- 绘图类型已覆盖显式函数、显式曲面、参数曲线、极坐标、二维隐式曲线
- 支持多图叠加、图层开关、基于当前图继续修改
- `/demo` 已接入 5 个教学动画场景
- 项目已补齐基础测试、开发脚本和批量绘图导出脚本
- 知识库已整合远洋运输业务 500 题（共 559 道题、81 个知识点）
- 新增 10 条跨学科案例库（`data/interdisciplinary_cases.json`），覆盖球面几何、微分方程、排队论、多目标优化等
- 新增向量语义检索层（sentence-transformers），650 条向量入库，作为关键词检索的补充兜底层
- 新增大圆航线可视化组件（`GreatCircleMap.vue`），已接入 `/demo`，基于 globe.gl 渲染 3D 地球仪，展示 Haversine 公式的航运应用

## 2. 技术栈

- 后端：FastAPI
- 前端：Vue 3 + Vite
- 图形渲染：Plotly + globe.gl（3D 地球仪）
- 数学解析：SymPy + NumPy
- 语义检索：sentence-transformers（paraphrase-multilingual-MiniLM-L12-v2）
- 大模型兜底：Kimi / Moonshot
- 数据导入：CSV / XLSX

## 3. 首页当前实现

首页对应文件：

- [frontend/src/App.vue](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\App.vue)
- [frontend/src/components/HeroSection.vue](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\components\HeroSection.vue)
- [frontend/src/components/InputPanel.vue](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\components\InputPanel.vue)
- [frontend/src/components/ResultPanel.vue](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\components\ResultPanel.vue)
- [frontend/src/components/PlotPanel.vue](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\components\PlotPanel.vue)
- [frontend/src/components/ImportPanel.vue](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\components\ImportPanel.vue)
- [frontend/src/composables/useNavMathVision.js](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\composables\useNavMathVision.js)

首页目前包含 4 个部分：

### 3.1 标题与快速启动

- 主标题：`智绘数航`
- 英文名：`NavMath Vision`
- 副标题：`数学可视化与航运知识融合学习辅助系统`
- 右侧快速启动示例会随机生成
- 公式类快速启动支持随机显示本地常见公式题

### 3.2 输入区

- 支持文本提问
- 支持图片上传，走 OCR 提取文本
- 支持点击示例一键带入

### 3.3 结果区

- 显示回答内容
- 显示来源模式、本地命中类型、置信度、处理过程
- 支持区分题库命中、知识点命中、绘图结果、模型兜底

### 3.4 绘图区

- 展示 Plotly 图形
- 展示 MATLAB 代码
- 展示教学提示
- 支持图层开关
- 支持“基于当前图像修改”输入框

### 3.5 导入区

- 支持导入知识点表
- 支持导入题目表
- 支持 `CSV` 和 `XLSX`

## 4. 场景演示页当前实现

场景演示入口文件：

- [frontend/src/DemoPage.vue](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\DemoPage.vue)
- [frontend/src/components/TopNav.vue](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\components\TopNav.vue)

当前页面结构是：

- 右上角导航在 `首页 / 场景演示` 之间切换
- `/demo` 页面按 3 个大类组织场景
- 点击大类后弹出该类下的小场景选项框

当前 3 个大类为：

- 港口运营优化
- 供应链与系统仿真
- 预测、监测与韧性

当前已落地的场景是 5 个。

### 4.1 场景 1：泊位分配与岸桥调度

对应文件：

- [frontend/src/components/demo/BerthScenarioView.vue](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\components\demo\BerthScenarioView.vue)
- [frontend/src/composables/useBerthSchedulingDemo.js](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\composables\useBerthSchedulingDemo.js)

当前页面重点已经从“港口总览图”收敛为“等待诊断页”，核心想讲清三件事：

- 哪条船在等
- 它在等哪个泊位
- 为什么还不能靠泊

当前具体实现包括：

- 主画面只突出焦点船、目标泊位、阻塞船
- 焦点船有单独状态标签，如 `WAITING`
- 目标泊位有 `TARGET`
- 被占用泊位有 `OCCUPIED`
- 时间轴中单独展示等待空窗 `ETA -> Actual Start`
- 顶部指标采用 `1 主 2 次`
- 控制区默认收敛，只保留播放、速度、规则和资源数量
- 高级参数折叠

当前场景涉及的核心公式：

- `start_time[i] >= eta[i]`
- `service_time[i] = workload[i] / (base_rate * num_cranes[i]^alpha)`
- `Min waiting + turnaround + idle - throughput`

增强模式还吸收了论文里的联合调度思想，例如：

- 泊位与岸桥联合决策
- 等待时间与最大完工时间双目标
- 岸桥不可穿越
- 安全距离约束

### 4.2 场景 2：堆场重定位与场桥协同

对应文件：

- [frontend/src/components/demo/YardScenarioView.vue](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\components\demo\YardScenarioView.vue)
- [frontend/src/composables/useYardRelocationDemo.js](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\composables\useYardRelocationDemo.js)

当前页面定位已经改成“当前动作展示页”，不再强调完整堆场总览。

当前具体实现包括：

- 把一次动作拆成 4 步：
  - 锁定目标
  - 识别阻塞
  - 分配车辆/场桥
  - 执行动作
- 支持播放 / 暂停 / 单步 / 重置
- 主动作区突出：
  - 目标箱
  - 挡路箱
  - 推荐搬移位置
  - 车辆与场桥路径
- 保留显微镜区，用于说明为什么当前箱不能直接提取
- 额外保留整体堆场位置视角，作为辅助视图
- 支持堆位策略和车辆派遣策略切换

当前场景涉及的核心公式：

- `stack[s] = [bottom ... top]`
- `retrieve(target) => relocate(blockers)`
- `Min travel + relocation + truck_waiting + makespan`

这个场景现在更强调：

- 目标箱是不是在顶层
- 挡路箱要搬到哪里
- 当前一步是否会影响未来总代价

### 4.3 场景 3：海运库存—航线联合决策

对应文件：

- [frontend/src/components/demo/InventoryScenarioView.vue](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\components\demo\InventoryScenarioView.vue)
- [frontend/src/composables/useInventoryRoutingDemo.js](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\composables\useInventoryRoutingDemo.js)

当前页面重点是“库存风险 + 航线决策”。

当前具体实现包括：

- 海上网络图展示港口与船舶位置
- 港口库存条动态显示库存高低
- 当前风险港口高亮
- 当前航线高亮
- 支持策略切换：
  - 滚动时域贪心
  - 最低库存率优先
  - 最大需求优先
  - 最短航程优先
- 支持播放、暂停、单步、重置
- 统一展示关键方程、当前状态、当前策略与对比策略

当前场景涉及的核心公式：

- `inventory[p][t+1] = inventory[p][t] - demand[p][t] + deliver[p][t] - pickup[p][t]`
- `load[v][t+1] = load[v][t] + pickup[v][t] - deliver[v][t]`
- `Min sailing_cost + stockout_penalty + holding_cost + port_call_cost`

页面想讲清的是：

- 哪个港口快缺货
- 船下一步该去哪
- 为什么 routing 不能脱离 inventory 单独看

### 4.4 场景 4：干散货港口卸船全流程

对应文件：

- [frontend/src/components/demo/BulkPortScenarioView.vue](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\components\demo\BulkPortScenarioView.vue)
- [frontend/src/composables/useBulkPortDemo.js](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\composables\useBulkPortDemo.js)

当前页面已经从“流程框说明页”重构成“生产链实时诊断页”。

当前具体实现包括：

- 主链路固定为四段：
  - 泊位
  - 卸船机
  - 水平运输
  - 堆场接卸
- 支持货流粒子推进动画
- 支持识别并高亮当前瓶颈段
- 前段、后段会随着瓶颈状态表现出拥堵和积压
- 支持播放 / 暂停 / 重置
- 支持协同策略和资源数量调节
- 右侧只保留瓶颈结论、两条解释和关键指标

当前场景涉及的核心公式：

- `throughput = min(berth_rate, unloader_rate, transport_rate, yard_rate)`
- `makespan ≈ total_volume / bottleneck_rate`

页面想讲清的是：

- 这是一条连续生产链
- 当前瓶颈在哪一段
- 为什么前段提速无法自动消除后段瓶颈

### 4.5 场景 5：大圆航线 vs 恒向线

对应文件：

- [frontend/src/components/GreatCircleMap.vue](C:\Users\cai yuan qi\Desktop\NavMath-main\frontend\src\components\GreatCircleMap.vue)

当前页面重点是把球面几何和真实航线规划直接连起来。

当前具体实现包括：

- 支持预设港口与自定义经纬度输入
- 计算大圆航线距离与恒向线距离
- 展示节省距离与估算燃油节省
- 用 3D 地球仪展示两种航线
- 同步给出 Haversine 公式说明与 MATLAB 代码

当前场景涉及的核心公式：

- `d = 2R · arcsin(√(sin²((φ2-φ1)/2) + cosφ1·cosφ2·sin²((λ2-λ1)/2)))`

页面想讲清的是：

- 地图上的“直线”不一定是球面上的最短路径
- 大圆航线为什么更短
- 数学公式如何直接影响航线与燃油决策

## 5. 后端当前实现

后端入口：

- [app/main.py](C:\Users\cai yuan qi\Desktop\NavMath-main\app\main.py)

核心服务：

- [app/services/knowledge.py](C:\Users\cai yuan qi\Desktop\NavMath-main\app\services\knowledge.py)
- [app/services/math_plot.py](C:\Users\cai yuan qi\Desktop\NavMath-main\app\services\math_plot.py)
- [app/services/llm_answer.py](C:\Users\cai yuan qi\Desktop\NavMath-main\app\services\llm_answer.py)
- [app/services/llm_plot.py](C:\Users\cai yuan qi\Desktop\NavMath-main\app\services\llm_plot.py)
- [app/services/imports.py](C:\Users\cai yuan qi\Desktop\NavMath-main\app\services\imports.py)
- [app/services/ocr.py](C:\Users\cai yuan qi\Desktop\NavMath-main\app\services\ocr.py)
- [app/services/visualization.py](C:\Users\cai yuan qi\Desktop\NavMath-main\app\services\visualization.py)

### 5.1 主分析链路

当前后端大致流程是：

1. 接收文本、图片、公式或修改指令
2. 规范化文本，识别课程方向
3. 先做本地题库匹配和知识点匹配
4. 如果像绘图请求，则进入本地绘图 pipeline
5. 如果本地知识或绘图都未命中，再调用 Kimi 兜底

### 5.2 知识检索逻辑

当前知识检索不是纯大模型聊天，而是“本地优先”的轻量检索增强链路。

当前逻辑包括：

- 加载 `data/knowledge_base.json`
- 叠加 `data/imports/` 下导入的知识点表和题目表
- 对用户问题做文本规范化
- 做语义改写、别名扩展、停用短语清洗
- 分别尝试匹配：
  - 题目
  - 知识点
  - 公式记录
- 匹配依据包含：
  - 文本重合
  - token 重合
  - 模糊相似度

当前命中后会返回：

- 来源类型
- 命中模式
- 置信度
- 结果内容

### 5.3 绘图系统逻辑

绘图核心文件：

- [app/services/math_plot.py](C:\Users\cai yuan qi\Desktop\NavMath-main\app\services\math_plot.py)

当前绘图系统已经不是“每种图单独写一套”，而是统一生成 `PlotSpec` 风格的中间描述，再同时服务：

- 前端 Plotly 渲染
- MATLAB 代码导出

当前支持的表达类型：

- `explicit2d`：显式二维函数
- `explicit3d`：显式三维曲面
- `parametric2d`：二维参数曲线
- `parametric3d`：三维参数曲线
- `polar2d`：极坐标曲线
- `implicit2d`：二维隐式曲线

当前支持的能力包括：

- 二维函数绘图
- 三维曲面绘图
- 多曲线叠加
- 多曲面叠加
- 极坐标曲线
- 二维隐式曲线
- 参数方程
- 标注点
- 图层开关
- 基于当前图像继续修改
- MATLAB 代码同步导出

当前已经补过的稳定性增强点包括：

- 支持隐式乘法，如 `2cos(theta)`、`3x`
- 支持 `e^x`
- 支持常数线和常数面，如 `y = 0`、`z = 2`
- 支持 `xy = 1` 这类隐式关系

## 6. 数据导入与本地知识库

当前导入目录：

- `data/imports/knowledge_points.csv`
- `data/imports/problems.csv`
- 也支持同名 `.xlsx`

当前导入逻辑：

- 前端上传文件
- 后端保存到 `data/imports/`
- 重新纳入知识库检索范围

当前首页文案中“课本知识点检索”和“支持知识点表与题目 CSV 导入”已经和这一实现对应。

## 7. 测试与验证

当前已具备的工程检查包括：

- 后端接口测试
- 绘图回归测试
- 批量绘图目录测试
- 前端生产构建检查

主要测试文件：

- `tests/test_api.py`
- `tests/test_plot_catalog.py`

当前还额外提供了几类批量导出脚本，用于人工审图：

- `scripts/export_plot_catalog.py`
- `scripts/export_overlay_catalog.py`
- `scripts/export_surface_pipeline_catalog.py`
- `scripts/render_matlab_export_examples.py`

产物目录在：

- `artifacts/plot_catalog/`
- `artifacts/overlay_catalog/`
- `artifacts/surface_pipeline_catalog/`
- `artifacts/`

## 8. 目录结构

```text
app/
  main.py
  services/
    imports.py
    knowledge.py
    llm_answer.py
    llm_plot.py
    math_plot.py
    ocr.py
    vector_search.py        ← 向量语义检索
    visualization.py

data/
  knowledge_base.json
  interdisciplinary_cases.json  ← 跨学科案例库（10条）
  vector_index.pkl              ← 向量索引缓存（运行时生成）
  imports/
    knowledge_points.csv / .xlsx
    problems.csv / .xlsx

frontend/
  src/
    App.vue
    DemoPage.vue
    main.js
    styles.css
    components/
      GreatCircleMap.vue    ← 大圆航线 3D 可视化
      HeroSection.vue
      ImportPanel.vue
      InputPanel.vue
      PlotPanel.vue
      ResultPanel.vue
      TopNav.vue
      demo/
        BerthScenarioView.vue
        YardScenarioView.vue
        InventoryScenarioView.vue
        BulkPortScenarioView.vue
    composables/
      useNavMathVision.js
      useBerthSchedulingDemo.js
      useYardRelocationDemo.js
      useInventoryRoutingDemo.js
      useBulkPortDemo.js

scripts/
  export_plot_catalog.py
  export_overlay_catalog.py
  export_surface_pipeline_catalog.py
  render_matlab_export_examples.py

tests/
  test_api.py
  test_plot_catalog.py

start_dev.cmd
dev_check.cmd
requirements.txt
README.md
```

## 9. 环境要求

### 9.1 后端

- Python 3.11+

安装依赖：

```bash
pip install -r requirements.txt
```

### 9.2 前端

- Node.js 18+

安装依赖：

```bash
cd frontend
npm install
```

## 10. 环境变量

项目根目录支持 `.env`：

```env
KIMI_API_KEY=your_api_key
KIMI_API_BASE=https://api.moonshot.cn/v1
KIMI_MODEL=moonshot-v1-8k
```

说明：

- `.env` 只保留在本地
- 未配置时，本地检索与本地绘图仍可运行
- 只有模型兜底和自然语言绘图增强依赖 Kimi

## 11. 启动方式

### 11.1 启动后端

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

### 11.2 启动前端

```bash
cd frontend
npm run dev
```

默认地址：

```text
http://127.0.0.1:5173
```

### 11.3 一键重启前后端

仓库根目录提供：

```bat
start_dev.cmd
```

作用：

- 清理占用 `8000` 和 `5173` 端口的旧进程
- 分别启动后端和前端

### 11.4 一键开发检查

仓库根目录提供：

```bat
dev_check.cmd
```

作用：

- 执行后端 `pytest`
- 执行前端 `npm run build`

## 12. 当前适合继续推进的方向

### 12.1 已完成但仍需打磨的功能

- **大圆航线组件**：`GreatCircleMap.vue` 已接入 `/demo`，但仍可以继续增强港口点位、航迹标签和移动端适配。
- **跨学科案例卡片**：首页结果区已支持 `matched_case`，但样式和展示层级还可以进一步统一。
- **向量索引重建提示**：导入成功后已经会尝试触发 `POST /api/build-index`，但目前仍缺少单独的状态提示与管理入口。

### 12.2 知识库扩充方向

- 继续补充跨学科案例（当前 10 条，目标 30 条以上），重点覆盖：
  - 船舶稳性与流体力学（微积分、微分方程）
  - 港口吞吐量预测（概率统计、时间序列）
  - 集装箱配载优化（线性规划、整数规划）
  - 航运运价指数分析（统计学、回归分析）
- 把 `data/knowledge_base.json` 中的高等数学知识点从 81 条扩充到 200 条以上

### 12.3 检索质量提升

- 当前向量检索阈值（0.55/0.65/0.60）是经验值，可以通过构建一批标注样本做系统性评估
- 考虑引入 RAG 模式：先向量检索召回 top-3，再把检索结果拼入 Kimi 的 prompt，让模型基于文档回答而非凭空生成
- 向量索引目前每次启动从 pickle 文件加载，知识库更新后需手动重建，可以加一个启动时自动检测版本的机制

### 12.4 前端体验优化

- 首页结果区增加”跨学科案例”卡片展示
- `/demo` 页面增加”球面几何与航线”场景（接入 `GreatCircleMap.vue`）
- 移动端适配（当前布局在小屏幕下有溢出问题）
- 绘图区支持全屏展开

### 12.5 工程健壮性

- `requirements.txt` 补充 `sentence-transformers`（当前已安装但未写入）
- 解决 Python 多版本共存问题：建议统一用虚拟环境（`python -m venv .venv`）管理依赖
- 补充向量检索相关的单元测试
