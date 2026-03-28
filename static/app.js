const form = document.getElementById("analyze-form");
const fillMathButton = document.getElementById("fill-math");
const fillSeaButton = document.getElementById("fill-sea");
const fillShapeButton = document.getElementById("fill-shape");
const statusText = document.getElementById("statusText");
const inputText = document.getElementById("inputText");
const courseName = document.getElementById("courseName");
const modeText = document.getElementById("modeText");
const knowledgeTags = document.getElementById("knowledgeTags");
const analysisSteps = document.getElementById("analysisSteps");
const solutionText = document.getElementById("solutionText");
const knowledgePointName = document.getElementById("knowledgePointName");
const knowledgeDefinition = document.getElementById("knowledgeDefinition");
const ocrText = document.getElementById("ocrText");
const plotSummary = document.getElementById("plotSummary");
const matlabCode = document.getElementById("matlabCode");
const teachingTip = document.getElementById("teachingTip");
const importSummary = document.getElementById("importSummary");
const importTags = document.getElementById("importTags");
const modeProblem = document.getElementById("modeProblem");
const modeKnowledge = document.getElementById("modeKnowledge");
const modeVisualization = document.getElementById("modeVisualization");
const knowledgeImportForm = document.getElementById("knowledge-import-form");
const problemImportForm = document.getElementById("problem-import-form");

fillMathButton.addEventListener("click", () => {
  document.getElementById("questionText").value = "判断曲面 z = x^2 - y^2 的类型，并说明为什么它是鞍面。";
  document.getElementById("formula").value = "z = x^2 - y^2";
});

fillSeaButton.addEventListener("click", () => {
  document.getElementById("questionText").value = "ISPS 规则的主要目标是什么？";
  document.getElementById("formula").value = "";
});

fillShapeButton.addEventListener("click", () => {
  document.getElementById("questionText").value = "生成一个圆环面";
  document.getElementById("formula").value = "";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusText.textContent = "正在解析，请稍候...";

  const fileInput = document.getElementById("file");
  const questionTextValue = document.getElementById("questionText").value.trim();
  const formulaValue = document.getElementById("formula").value.trim();
  const formData = new FormData();
  formData.append("question_text", questionTextValue);
  formData.append("formula", formulaValue);

  let endpoint = "/api/analyze-text";
  if (fileInput.files[0]) {
    endpoint = "/api/analyze-image";
    formData.delete("question_text");
    formData.append("file", fileInput.files[0]);
  }

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    renderResult(data);
    statusText.textContent = "解析完成。";
  } catch (error) {
    statusText.textContent = "解析失败，请检查服务是否已启动。";
    ocrText.textContent = String(error);
  }
});

knowledgeImportForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = document.getElementById("knowledgeCsv").files[0];
  await uploadCsv("knowledge_points", file);
});

problemImportForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = document.getElementById("problemCsv").files[0];
  await uploadCsv("problems", file);
});

async function uploadCsv(kind, file) {
  if (!file) {
    importSummary.textContent = "请选择 CSV 文件后再上传。";
    return;
  }

  const formData = new FormData();
  formData.append("kind", kind);
  formData.append("file", file);
  importSummary.textContent = `正在上传 ${file.name} ...`;

  try {
    const response = await fetch("/api/import-csv", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    importSummary.textContent = `上传完成：${data.kind}，共导入 ${data.count} 条记录。`;
    await loadImportStatus();
  } catch (error) {
    importSummary.textContent = `上传失败：${error}`;
  }
}

function renderResult(data) {
  inputText.textContent = data.input_text || "无内容";
  courseName.textContent = `${data.detected_course} / ${data.matched_problem.title}`;
  modeText.textContent = describeMode(data.view_mode, data.plot?.plot_label);
  solutionText.textContent = data.matched_problem.solution || "";
  plotSummary.textContent = data.plot?.summary || "当前未生成图形。";
  matlabCode.textContent = data.plot?.matlab_code || "暂无代码";
  teachingTip.textContent = data.plot?.teaching_tip || "暂无教学提示。";
  ocrText.textContent = data.ocr
    ? `${data.ocr.message}${data.filename ? ` 文件: ${data.filename}` : ""}`
    : "本次未走 OCR 流程。";
  knowledgePointName.textContent = data.matched_knowledge_point?.knowledge_point || "暂无匹配";
  knowledgeDefinition.textContent = data.matched_knowledge_point
    ? `${data.matched_knowledge_point.definition || ""} ${data.matched_knowledge_point.summary || ""}`.trim()
    : "当前未匹配到知识点问答内容。";

  setActiveMode(data.view_mode);

  knowledgeTags.innerHTML = "";
  (data.matched_problem.knowledge_points || []).forEach((item) => {
    const tag = document.createElement("span");
    tag.textContent = item;
    knowledgeTags.appendChild(tag);
  });

  analysisSteps.innerHTML = "";
  (data.matched_problem.analysis_steps || []).forEach((item) => {
    const step = document.createElement("li");
    step.textContent = item;
    analysisSteps.appendChild(step);
  });

  if (data.plot?.data?.length) {
    Plotly.newPlot("plot", data.plot.data, data.plot.layout, {
      responsive: true,
      displaylogo: false,
    });
  } else {
    Plotly.purge("plot");
  }
}

function describeMode(mode, plotLabel) {
  if (mode === "visualization") {
    return `当前模式：图形演示${plotLabel ? ` / ${plotLabel}` : ""}`;
  }
  if (mode === "knowledge") {
    return "当前模式：知识点问答";
  }
  return "当前模式：题目解析";
}

function setActiveMode(mode) {
  [modeProblem, modeKnowledge, modeVisualization].forEach((item) => {
    item.classList.remove("active");
  });

  if (mode === "visualization") {
    modeVisualization.classList.add("active");
    return;
  }
  if (mode === "knowledge") {
    modeKnowledge.classList.add("active");
    return;
  }
  modeProblem.classList.add("active");
}

async function loadImportStatus() {
  try {
    const response = await fetch("/api/import-status");
    const data = await response.json();
    importSummary.textContent = `知识点 ${data.counts.knowledge_points} 条，题目 ${data.counts.problems} 条。`;
    importTags.innerHTML = "";
    data.files.forEach((file) => {
      const tag = document.createElement("span");
      tag.textContent = file.exists ? `${file.name} 已就绪` : `${file.name} 未上传`;
      importTags.appendChild(tag);
    });
  } catch (error) {
    importSummary.textContent = "读取导入状态失败。";
  }
}

loadImportStatus();
