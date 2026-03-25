<script setup>
import TopNav from "./components/TopNav.vue";
import HeroSection from "./components/HeroSection.vue";
import InputPanel from "./components/InputPanel.vue";
import ResultPanel from "./components/ResultPanel.vue";
import PlotPanel from "./components/PlotPanel.vue";
import ImportPanel from "./components/ImportPanel.vue";
import { useNavMathVision } from "./composables/useNavMathVision";

const {
  questionText,
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
  knowledgeDefinition,
  ocrText,
  demoExamples,
  applySample,
  submitAnalysis,
  onImageChange,
  setPlotTarget,
  uploadKnowledgeCsv,
  uploadProblemsCsv,
} = useNavMathVision();
</script>

<template>
  <main class="page-shell">
    <TopNav current-page="home" />

    <HeroSection :demo-examples="demoExamples" @pick-example="applySample" />

    <section class="workspace">
      <InputPanel
        v-model:question-text="questionText"
        @submit="submitAnalysis"
        @sample="applySample"
        @image-change="onImageChange"
      />

      <ResultPanel
        :status-text="statusText"
        :result="result"
        :mode-items="modeItems"
        :mode-text="modeText"
        :source-text="sourceText"
        :source-detail="sourceDetail"
        :match-type-text="matchTypeText"
        :confidence-text="confidenceText"
        :course-badge-class="courseBadgeClass"
        :knowledge-definition="knowledgeDefinition"
        :ocr-text="ocrText"
        :import-state="importState"
        :process-steps="processSteps"
      />
    </section>

    <PlotPanel
      :plot-summary="plotSummary"
      :matlab-code="matlabCode"
      :teaching-tip="teachingTip"
      :plot="result.plot"
      @ready="setPlotTarget"
    />

    <ImportPanel
      compact
      :summary="importState.summary"
      @upload-knowledge="uploadKnowledgeCsv"
      @upload-problems="uploadProblemsCsv"
    />
  </main>
</template>
