import { computed, nextTick, onMounted, reactive, ref } from "vue";

const PLOTLY_CDN_URL = "https://cdn.plot.ly/plotly-2.35.2.min.js";
let plotlyLoaderPromise = null;

function loadPlotlyFromCdn() {
  if (window.Plotly) {
    return Promise.resolve(window.Plotly);
  }

  if (!plotlyLoaderPromise) {
    plotlyLoaderPromise = new Promise((resolve, reject) => {
      const existing = document.querySelector('script[data-plotly-cdn="true"]');
      if (existing) {
        existing.addEventListener("load", () => resolve(window.Plotly), { once: true });
        existing.addEventListener("error", () => reject(new Error("Plotly CDN 加载失败。")), {
          once: true,
        });
        return;
      }

      const script = document.createElement("script");
      script.src = PLOTLY_CDN_URL;
      script.async = true;
      script.dataset.plotlyCdn = "true";
      script.onload = () => resolve(window.Plotly);
      script.onerror = () => reject(new Error("Plotly CDN 加载失败。"));
      document.head.appendChild(script);
    });
  }

  return plotlyLoaderPromise;
}

async function parseApiResponse(response) {
  const rawText = await response.text();
  let data = null;

  if (rawText) {
    try {
      data = JSON.parse(rawText);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    const message = data?.detail || data?.message || rawText || `请求失败，HTTP ${response.status}`;
    throw new Error(String(message));
  }

  if (data === null) {
    throw new Error(`接口返回的不是有效 JSON：${rawText.slice(0, 120)}`);
  }

  return data;
}

function pickRandom(pool) {
  return pool[Math.floor(Math.random() * pool.length)];
}

const demoExamples = [
  {
    key: "math_surface",
    title: "函数可视化",
    text: pickRandom([
      "判断曲面 z = x^2 - y^2 的类型，并说明为什么它是双曲抛物面。",
      "求曲面 z = x^2 + y^2 与平面 z = 4 的截线，并说明图形特征。",
      "画出曲面 z = x^2 - y^2，并观察 x=0 与 y=0 截面的开口方向。",
      "比较曲面 z = x^2 + y^2 和 z = x^2 - y^2 的几何形状差异。",
    ]),
  },
  {
    key: "math_limit",
    title: "极限与导数",
    text: pickRandom([
      "计算极限 lim(x→0) sinx/x。",
      "求函数 f(x)=sin(x^2) 的导数。",
      "求函数 f(x)=xlnx 的导数。",
      "求极限 lim(x→∞)(1+1/x)^x。",
    ]),
  },
  {
    key: "ocean_trade",
    title: "航运知识问答",
    text: pickRandom([
      "国际贸易术语的主要作用是什么？",
      "FOB 术语下风险转移的界限是什么？",
      "提单的功能不包括什么？",
      "班轮运输的主要特点不包括哪一项？",
    ]),
  },
  {
    key: "plot_nl",
    title: "公式随机启动",
    text: pickRandom([
      "请画出曲面 z = x^2 - y^2，并附上 MATLAB 代码。",
      "请画出函数 y = exp(-x^2)，并说明图形特征。",
      "请画出参数曲线 x = cos(t), y = sin(t)，并附上 MATLAB 代码。",
      "请画出极坐标曲线 r = 1 + 2cos(theta)。",
      "请画出曲面 z = x^2 + y^2 与平面 z = 4 的交线。",
    ]),
  },
];

const sampleAliasMap = {
  math: "math_surface",
  sea: "ocean_trade",
  shape: "plot_nl",
};

export function useNavMathVision() {
  const questionText = ref("");
  const plotEditText = ref("");
  const imageFile = ref(null);
  const statusText = ref("等待输入。");
  const plotTarget = ref(null);

  const result = reactive({
    input_text: "",
    detected_course: "",
    view_mode: "problem",
    matched_problem: {
      title: "暂无匹配",
      course: "",
      knowledge_points: [],
      analysis_steps: [],
      solution: "",
    },
    matched_knowledge_point: null,
    matched_case: null,
    web_results: [],
    source_breakdown: {
      local: false,
      vector: false,
      web: false,
      llm: false,
    },
    plot: null,
    ocr: null,
    filename: "",
    parser: "local",
    source_detail: "",
    match_meta: {
      type: "fallback",
      score: 0,
      confidence: "未命中",
    },
  });

  const importState = reactive({
    summary: "正在读取导入状态。",
    files: [],
    counts: {
      knowledge_points: 0,
      problems: 0,
    },
  });

  const processSteps = reactive([
    { key: "input", label: "识别输入", detail: "等待开始", status: "idle" },
    { key: "match", label: "匹配知识点", detail: "等待开始", status: "idle" },
    { key: "plot", label: "生成绘图", detail: "等待开始", status: "idle" },
    { key: "done", label: "整理结果", detail: "等待开始", status: "idle" },
  ]);

  const demoState = reactive({
    active: false,
    currentIndex: -1,
  });

  const currentDemoExample = computed(() => demoExamples[demoState.currentIndex] || null);

  const demoStepText = computed(() => {
    if (!demoState.active || demoState.currentIndex < 0) {
      return "演示模式未启动。可以直接点单条示例，也可以按固定流程连续演示。";
    }
    return `演示模式进行中：第 ${demoState.currentIndex + 1} / ${demoExamples.length} 步`;
  });

  const modeItems = computed(() => [
    { key: "problem", label: "题目解析", active: result.view_mode === "problem" },
    { key: "knowledge", label: "知识问答", active: result.view_mode === "knowledge" },
    { key: "visualization", label: "图形演示", active: result.view_mode === "visualization" },
  ]);

  const modeText = computed(() => {
    if (result.view_mode === "visualization") {
      return `当前模式：图形演示${result.plot?.plot_label ? ` / ${result.plot.plot_label}` : ""}`;
    }
    if (result.view_mode === "knowledge") {
      return "当前模式：知识问答";
    }
    return "当前模式：题目解析";
  });

  const sourceText = computed(() => (result.parser === "kimi" ? "Kimi 二级中转" : "本地知识库"));
  const sourceDetail = computed(() => result.source_detail || "等待解析后显示来源说明。");

  const matchTypeText = computed(() => {
    const mapping = {
      problem: "命中类型：题库",
      knowledge_point: "命中类型：知识点",
      formula_record: "命中类型：公式记录",
      plot_rule: "命中类型：绘图规则",
      llm_fallback: "命中类型：模型兜底",
      fallback: "命中类型：默认回退",
    };
    return mapping[result.match_meta?.type] || "命中类型：未识别";
  });

  const confidenceText = computed(() => {
    const confidence = result.match_meta?.confidence || "未命中";
    const score = result.match_meta?.score ?? 0;
    return `置信度：${confidence} / 分数 ${score}`;
  });

  const courseBadgeClass = computed(() => {
    const course = result.detected_course || "";
    if (course.includes("高等数学")) {
      return "course-math";
    }
    if (course.includes("远洋运输")) {
      return "course-ocean";
    }
    return "course-default";
  });

  const plotSummary = computed(() => result.plot?.summary || "当前未生成图形。");
  const matlabCode = computed(() => result.plot?.matlab_code || "暂无代码");
  const teachingTip = computed(() => result.plot?.teaching_tip || "暂无教学提示。");

  const plotLayers = computed(() =>
    (result.plot?.plot_spec?.traces || result.plot?.data || []).map((trace, index) => ({
      index,
      name: trace.name || `图层 ${index + 1}`,
      visible: trace.visible !== false && trace.visible !== "legendonly",
      kind: trace.kind || trace.type || "trace",
    }))
  );

  const plotMeta = computed(() => ({
    expressionType: result.plot?.expression_type || result.plot?.plot_spec?.expression_type || "",
    dimension: result.plot?.dimension || result.plot?.plot_spec?.dimension || "",
    traceCount: plotLayers.value.length,
    formulas: result.plot?.formulas || result.plot?.plot_spec?.formulas || [],
    parameterRanges: result.plot?.plot_spec?.parameter_ranges || {},
  }));

  const knowledgeDefinition = computed(() => {
    if (!result.matched_knowledge_point) {
      return "当前未匹配到知识点问答内容。";
    }
    return `${result.matched_knowledge_point.definition || ""} ${result.matched_knowledge_point.summary || ""}`.trim();
  });

  const ocrText = computed(() => {
    if (!result.ocr) {
      return "本次未走 OCR 流程。";
    }
    return `${result.ocr.message}${result.filename ? ` 文件：${result.filename}` : ""}`;
  });

  function updateStep(key, status, detail) {
    const target = processSteps.find((item) => item.key === key);
    if (!target) {
      return;
    }
    target.status = status;
    target.detail = detail;
  }

  function resetSteps() {
    processSteps.forEach((item) => {
      item.status = "idle";
      item.detail = "等待开始";
    });
  }

  function resolveSampleKey(kind) {
    return sampleAliasMap[kind] || kind;
  }

  function applySample(kind) {
    imageFile.value = null;
    const target = demoExamples.find((item) => item.key === resolveSampleKey(kind));
    if (!target) {
      return;
    }
    questionText.value = target.text;
  }

  function startDemoMode() {
    demoState.active = true;
    demoState.currentIndex = 0;
    applySample(demoExamples[0].key);
  }

  function nextDemoStep() {
    if (!demoState.active) {
      startDemoMode();
      return;
    }

    if (demoState.currentIndex >= demoExamples.length - 1) {
      demoState.currentIndex = demoExamples.length - 1;
      applySample(demoExamples[demoState.currentIndex].key);
      return;
    }

    demoState.currentIndex += 1;
    applySample(demoExamples[demoState.currentIndex].key);
  }

  function stopDemoMode() {
    demoState.active = false;
    demoState.currentIndex = -1;
  }

  function onImageChange(file) {
    imageFile.value = file;
  }

  function setPlotTarget(element) {
    plotTarget.value = element;
  }

  async function submitAnalysis() {
    resetSteps();
    statusText.value = "正在解析，请稍候。";
    updateStep("input", "active", "正在读取文字或图片输入");

    const payload = new FormData();
    payload.append("question_text", questionText.value.trim());
    payload.append("formula", "");
    payload.append("previous_plot", "");

    let endpoint = "/api/analyze-text";
    if (imageFile.value) {
      endpoint = "/api/analyze-image";
      payload.delete("question_text");
      payload.append("file", imageFile.value);
    }

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        body: payload,
      });
      const data = await parseApiResponse(response);

      updateStep("input", "done", "输入内容已提交");
      updateStep("match", "active", "正在匹配课程、知识点和题目");

      Object.assign(result, data);
      plotEditText.value = "";

      updateStep(
        "match",
        "done",
        result.parser === "kimi"
          ? "本地未命中，已切换到 Kimi 二级中转"
          : `已完成本地匹配，当前置信度为 ${result.match_meta?.confidence || "未命中"}`
      );
      updateStep("plot", "active", result.plot ? "正在生成图形和 MATLAB 代码" : "当前请求无需绘图");

      statusText.value = "解析完成。";
      await nextTick();
      await renderPlot();

      updateStep("plot", result.plot ? "done" : "idle", result.plot ? "图形或代码已生成" : "未生成图形");
      updateStep("done", "done", "结果已显示到页面");
    } catch (error) {
      updateStep("done", "error", `失败：${error.message || error}`);
      statusText.value = `解析失败：${error.message || error}`;
    }
  }

  async function submitPlotEdit() {
    if (!result.plot) {
      statusText.value = "当前还没有可修改的图像。";
      return;
    }

    if (!plotEditText.value.trim()) {
      statusText.value = "请输入图像修改指令。";
      return;
    }

    resetSteps();
    statusText.value = "正在基于当前图像执行修改。";
    updateStep("input", "active", "正在读取图像修改指令");
    updateStep("match", "active", "正在加载上一张图像状态");

    const payload = new FormData();
    payload.append("question_text", plotEditText.value.trim());
    payload.append("formula", "");
    payload.append("previous_plot", JSON.stringify(result.plot));

    try {
      const response = await fetch("/api/analyze-text", {
        method: "POST",
        body: payload,
      });
      const data = await parseApiResponse(response);

      updateStep("input", "done", "修改指令已提交");
      updateStep("match", "done", "已完成上一张图像状态匹配");

      Object.assign(result, data);
      statusText.value = "图像修改完成。";
      await nextTick();
      await renderPlot();

      updateStep("plot", "done", "图像已按修改指令更新");
      updateStep("done", "done", "修改结果已显示到页面");
    } catch (error) {
      updateStep("done", "error", `失败：${error.message || error}`);
      statusText.value = `图像修改失败：${error.message || error}`;
    }
  }

  async function renderPlot() {
    if (!plotTarget.value) {
      return;
    }

    if (!result.plot?.data?.length) {
      if (window.Plotly) {
        window.Plotly.purge(plotTarget.value);
      } else {
        plotTarget.value.innerHTML = "";
      }
      return;
    }

    const Plotly = await loadPlotlyFromCdn();
    await Plotly.newPlot(plotTarget.value, result.plot.data, result.plot.layout, {
      responsive: true,
      displaylogo: false,
    });
  }

  async function togglePlotLayer(index) {
    if (!result.plot?.data?.[index]) {
      return;
    }

    const current = result.plot.data[index];
    const nextVisible = current.visible === "legendonly" || current.visible === false ? true : "legendonly";
    result.plot.data[index] = { ...current, visible: nextVisible };

    if (result.plot.plot_spec?.traces?.[index]) {
      result.plot.plot_spec.traces[index] = {
        ...result.plot.plot_spec.traces[index],
        visible: nextVisible === true,
      };
    }

    if (plotTarget.value && window.Plotly) {
      await window.Plotly.react(plotTarget.value, result.plot.data, result.plot.layout, {
        responsive: true,
        displaylogo: false,
      });
    }
  }

  async function loadImportStatus() {
    try {
      const response = await fetch("/api/import-status");
      const data = await parseApiResponse(response);
      importState.files = data.files;
      importState.counts = data.counts;
      importState.summary = `知识点 ${data.counts.knowledge_points} 条，题目 ${data.counts.problems} 条。`;
    } catch (error) {
      importState.summary = `读取导入状态失败：${error.message || error}`;
    }
  }

  async function uploadCsv(kind, file) {
    if (!file) {
      importState.summary = "请选择 CSV 文件后再上传。";
      return;
    }

    const payload = new FormData();
    payload.append("kind", kind);
    payload.append("file", file);

    try {
      const response = await fetch("/api/import-csv", {
        method: "POST",
        body: payload,
      });
      const data = await parseApiResponse(response);
      importState.summary = `上传完成：${data.kind}，共导入 ${data.count} 条记录。正在重建向量索引。`;
      await loadImportStatus();
      await rebuildVectorIndex();
    } catch (error) {
      importState.summary = `上传失败：${error.message || error}`;
    }
  }

  async function rebuildVectorIndex() {
    try {
      const response = await fetch("/api/build-index", { method: "POST" });
      const data = await parseApiResponse(response);
      if (data.status === "ok") {
        importState.summary += ` 向量索引已更新（${data.message}）。`;
      }
    } catch {
      // 索引重建失败不阻断主流程，静默忽略
    }
  }

  async function uploadKnowledgeCsv(file) {
    await uploadCsv("knowledge_points", file);
  }

  async function uploadProblemsCsv(file) {
    await uploadCsv("problems", file);
  }

  onMounted(() => {
    loadImportStatus();
  });

  return {
    questionText,
    plotEditText,
    statusText,
    result,
    importState,
    processSteps,
    modeItems,
    modeText,
    sourceText,
    sourceDetail,
    matchTypeText,
    confidenceText,
    courseBadgeClass,
    plotSummary,
    matlabCode,
    teachingTip,
    plotLayers,
    plotMeta,
    knowledgeDefinition,
    ocrText,
    demoExamples,
    demoState,
    demoStepText,
    currentDemoExample,
    applySample,
    startDemoMode,
    nextDemoStep,
    stopDemoMode,
    submitAnalysis,
    submitPlotEdit,
    togglePlotLayer,
    onImageChange,
    setPlotTarget,
    uploadKnowledgeCsv,
    uploadProblemsCsv,
  };
}
