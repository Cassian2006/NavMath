<script setup>
import { computed, ref } from "vue";
import { useYardRelocationDemo } from "../../composables/useYardRelocationDemo";

const {
  settings,
  requestQueue,
  yardBlocks,
  craneVisuals,
  truckVisuals,
  currentAction,
  plan,
  playing,
  playbackSpeed,
  simulationTime,
  containerTone,
  selectStack,
  resetPlayback,
  stepOnce,
  togglePlayback,
  formatHours,
  blockLabel,
  dispatchLabel,
} = useYardRelocationDemo();

const advancedOpen = ref(false);

const activeRequest = computed(
  () => requestQueue.value.find((item) => item.status === "active") || requestQueue.value[0] || null
);

const allStacks = computed(() =>
  yardBlocks.value.flatMap((block) =>
    block.bays.flatMap((bay) =>
      bay.stacks.map((stack) => ({
        ...stack,
        blockId: block.id,
        bayId: bay.id,
      }))
    )
  )
);

const stackMap = computed(() => Object.fromEntries(allStacks.value.map((stack) => [stack.id, stack])));

const sourceStackId = computed(() => {
  if (!currentAction.value) {
    return activeRequest.value?.block ? `${activeRequest.value.block}-Bay1-S1` : null;
  }
  return currentAction.value.fromStackId?.includes("Gate") ? null : currentAction.value.fromStackId;
});

const targetContainerId = computed(() => activeRequest.value?.containerId || null);

const blockerContainerId = computed(() => {
  if (currentAction.value?.type === "relocate") {
    return currentAction.value.containerId;
  }
  return null;
});

const destinationLabel = computed(() => {
  if (!currentAction.value || currentAction.value.type === "retrieve") {
    return "Quay / 交付位";
  }
  return currentAction.value.toStackId;
});

const currentTruck = computed(() => truckVisuals.value.find((item) => item.active) || truckVisuals.value[0] || null);
const currentCrane = computed(() => craneVisuals.value.find((item) => item.active) || craneVisuals.value[0] || null);

const sourceStack = computed(() => (sourceStackId.value ? stackMap.value[sourceStackId.value] : null));
const destinationStack = computed(() => {
  if (!currentAction.value || currentAction.value.toStackId?.includes("Quay")) {
    return null;
  }
  return stackMap.value[currentAction.value.toStackId];
});

const sourceTiers = computed(() => [...(sourceStack.value?.tiers || [])].reverse());
const destinationTiers = computed(() => [...(destinationStack.value?.tiers || [])].reverse());

const currentActionProgress = computed(() => {
  if (!currentAction.value) {
    return 0;
  }
  const clock = simulationTime.value % plan.value.duration;
  const duration = Math.max(currentAction.value.end - currentAction.value.start, 0.1);
  return Math.min(1, Math.max(0, (clock - currentAction.value.start) / duration));
});

const currentStepIndex = computed(() => {
  if (!activeRequest.value) return -1;
  if (!currentAction.value) return 0;
  return Math.min(3, Math.floor(currentActionProgress.value * 4));
});

const stepItems = computed(() => {
  const items = [
    {
      key: "lock",
      label: "1. 锁定目标",
      detail: targetContainerId.value ? `目标箱 ${targetContainerId.value}` : "等待目标箱",
    },
    {
      key: "block",
      label: "2. 识别阻塞",
      detail: blockerContainerId.value ? `挡路箱 ${blockerContainerId.value}` : "无阻塞，可直接提取",
    },
    {
      key: "dispatch",
      label: "3. 分配车辆 / 场桥",
      detail: currentTruck.value ? `${currentTruck.value.id} / ${currentCrane.value?.craneId || "YC"}` : "等待设备接手",
    },
    {
      key: "execute",
      label: "4. 执行动作",
      detail: currentAction?.value?.type === "retrieve" ? "送往 Quay / 交付位" : destinationLabel.value,
    },
  ];

  return items.map((item, index) => ({
    ...item,
    active: currentStepIndex.value === index,
    done: currentStepIndex.value > index,
  }));
});

const actionTitle = computed(() => {
  if (!activeRequest.value) {
    return "当前动作：等待下一条提箱请求";
  }
  if (!currentAction.value) {
    return `当前动作：锁定目标箱 ${activeRequest.value.containerId}，准备进入执行阶段`;
  }
  if (currentAction.value.type === "relocate") {
    return `当前动作：先搬走挡路箱 ${currentAction.value.containerId}，为提取 ${activeRequest.value.containerId} 让路`;
  }
  if (currentAction.value.type === "retrieve") {
    return `当前动作：提取 ${currentAction.value.containerId}，由 ${currentTruck.value?.id || "IT"} 送往 Quay / 交付位`;
  }
  return `当前动作：${currentAction.value.containerId} 入位到 ${currentAction.value.toStackId}`;
});

const processConclusion = computed(() => {
  if (!activeRequest.value) {
    return "当前没有活跃动作。";
  }
  if (blockerContainerId.value) {
    return `${targetContainerId.value} 当前不能直接提取，系统正在先处理挡路箱。`;
  }
  return `${targetContainerId.value} 已可直接提取，系统正在安排运输到交付位。`;
});

const processReasons = computed(() => [
  blockerContainerId.value ? `目标箱当前不在顶层，挡路箱是 ${blockerContainerId.value}。` : "目标箱当前就在顶层。",
  blockerContainerId.value ? "本次动作需要先重定位，再释放目标箱。" : "本次动作无需重定位，直接进入运输。",
  currentTruck.value
    ? `当前接手设备：${currentTruck.value.id}${currentCrane.value ? ` / ${currentCrane.value.craneId}` : ""}。`
    : "设备尚未进入执行阶段。",
]);

const keyMetrics = computed(() => [
  { label: "总搬运时间", value: formatHours(plan.value.metrics.totalMoveTime) },
  { label: "重定位次数", value: `${plan.value.metrics.relocations} 次` },
]);

const microscopeSummary = computed(() => {
  if (!targetContainerId.value) {
    return "当前没有目标箱。";
  }
  if (blockerContainerId.value) {
    return `${targetContainerId.value} 被 ${blockerContainerId.value} 挡住，需要先重定位。`;
  }
  return `无阻塞，可直接提取 ${targetContainerId.value}。`;
});

const explainabilityCards = computed(() => [
  {
    label: "STACK",
    formula: "target on top ? retrieve : block",
    plain: "目标箱不在顶层时，不能直接提取。",
    live: blockerContainerId.value
      ? `${targetContainerId.value} 上方仍有 ${blockerContainerId.value}。`
      : `${targetContainerId.value} 已在顶层。`,
  },
  {
    label: "RELOCATE",
    formula: "blocker -> free(target)",
    plain: "如有挡路箱，必须先搬走再释放目标箱。",
    live: blockerContainerId.value ? `当前先执行 ${blockerContainerId.value} 的重定位。` : "本次动作不需要重定位。",
  },
  {
    label: "COST",
    formula: "min travel + relocation + future blocking",
    plain: "策略会在即时搬运与未来阻塞之间权衡。",
    live: `当前策略是 ${blockLabel(settings.strategy)} + ${dispatchLabel(settings.dispatchRule)}。`,
  },
]);

const actionCargoClass = computed(() => {
  if (currentStepIndex.value <= 0) return "at-source";
  if (currentStepIndex.value === 1) return "lifting";
  if (currentStepIndex.value === 2) return "in-transit";
  return "delivered";
});

const focusBlockId = computed(() => sourceStackId.value?.split("-")[0] || activeRequest.value?.block || "B1");

const overviewBlocks = computed(() =>
  yardBlocks.value.map((block) => ({
    ...block,
    muted: block.id !== focusBlockId.value,
  }))
);
</script>

<template>
  <section class="panel yard-action-panel">
    <div class="yard-action-header">
      <div>
        <p class="eyebrow">Scenario 02</p>
        <h1>码头堆场重定位与场桥协同</h1>
        <p class="scene-overview-text">这页拆成两块：左边看当前动作，右边看它在整个堆场里发生的位置，两边共用同一条执行过程。</p>
      </div>
      <div class="yard-action-kpis">
        <article class="yard-action-kpi-main">
          <span>当前目标</span>
          <strong>{{ targetContainerId || "等待请求" }}</strong>
          <small>{{ blockerContainerId ? "先处理挡路箱" : "进入直接提取流程" }}</small>
        </article>
        <article v-for="item in keyMetrics" :key="item.label" class="yard-action-kpi-sub">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </div>
    </div>

    <section class="yard-action-grid">
      <article class="yard-action-stage">
        <div class="panel-header">
          <h2>{{ actionTitle }}</h2>
          <p>这里专门看当前这一箱怎么动：先锁定目标，再识别阻塞，随后交给车辆和场桥执行。</p>
        </div>

        <div class="yard-process-steps">
          <article
            v-for="item in stepItems"
            :key="item.key"
            class="yard-process-step"
            :class="{ active: item.active, done: item.done }"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.detail }}</strong>
          </article>
        </div>

        <div class="yard-process-stage">
          <section class="yard-process-node source">
            <header>
              <span>当前堆位</span>
              <strong>{{ sourceStackId || "待锁定" }}</strong>
            </header>
            <div class="yard-process-stack">
              <div
                v-for="(tier, index) in sourceTiers"
                :key="`process-source-${index}`"
                class="yard-process-tier"
                :class="{
                  target: tier === targetContainerId,
                  blocker: tier === blockerContainerId,
                  muted: !tier,
                }"
                :style="tier ? { background: containerTone(tier) } : undefined"
              >
                <span>{{ tier || "空位" }}</span>
              </div>
            </div>
          </section>

          <section class="yard-process-transfer">
            <div class="yard-process-lane strong-lane">
              <div class="yard-process-path"></div>
              <div class="yard-process-arrowhead"></div>
              <div class="yard-process-vehicle" :class="{ active: Boolean(currentTruck?.active) }">
                {{ currentTruck?.id || "IT1" }}
              </div>
              <div class="yard-process-cargo" :class="actionCargoClass">
                {{ blockerContainerId || targetContainerId || "C" }}
              </div>
            </div>
            <div class="yard-process-dispatch">
              <strong>当前接手</strong>
              <span>{{ currentTruck?.id || "等待车辆" }}</span>
              <small>{{ currentCrane?.craneId || "等待场桥" }}</small>
            </div>
          </section>

          <section class="yard-process-node target">
            <header>
              <span>{{ currentAction?.type === "retrieve" || !currentAction ? "Quay / 交付位" : "推荐落位" }}</span>
              <strong>{{ destinationLabel }}</strong>
            </header>
            <div class="yard-process-dropzone">
              <div class="yard-process-drop-badge">
                {{ currentAction?.type === "retrieve" || !currentAction ? "交付" : "重定位" }}
              </div>
              <div v-if="destinationStack" class="yard-process-stack ghost">
                <div
                  v-for="(tier, index) in destinationTiers"
                  :key="`process-destination-${index}`"
                  class="yard-process-tier"
                  :class="{ relocation: blockerContainerId && index === 0, muted: !tier }"
                  :style="tier ? { background: containerTone(tier) } : undefined"
                >
                  <span>{{ tier || "空位" }}</span>
                </div>
              </div>
            </div>
          </section>
        </div>

        <div class="yard-action-toolbar process-toolbar">
          <button type="button" class="primary" @click="togglePlayback">
            {{ playing ? "暂停" : "播放" }}
          </button>
          <button type="button" class="secondary" @click="stepOnce">单步</button>
          <button type="button" class="secondary" @click="resetPlayback">重置</button>
          <label class="yard-action-inline">
            <span>播放速度</span>
            <input v-model="playbackSpeed" type="range" min="0.5" max="2.5" step="0.5" />
            <strong>{{ playbackSpeed.toFixed(1) }}x</strong>
          </label>
        </div>
      </article>

      <aside class="yard-action-brief">
        <p class="eyebrow">当前动作为什么能执行</p>
        <h2>{{ processConclusion }}</h2>
        <div class="yard-action-brief-list">
          <p v-for="item in processReasons" :key="item">{{ item }}</p>
        </div>
        <div class="yard-action-step-state">
          <span>当前步骤</span>
          <strong>{{ stepItems[Math.max(currentStepIndex, 0)]?.label || "1. 锁定目标" }}</strong>
        </div>
        <div class="yard-action-brief-metrics">
          <article v-for="item in keyMetrics" :key="item.label" class="yard-action-brief-metric">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </article>
        </div>
      </aside>
    </section>

    <section class="yard-action-support">
      <article class="yard-overview-mini">
        <div class="yard-overview-head">
          <h2>整体堆场位置</h2>
          <span>这块只负责说明当前动作发生在哪个 block / bay / stack，不再和主动作重叠。</span>
        </div>

        <div class="yard-overview-blocks">
          <section
            v-for="block in overviewBlocks"
            :key="block.id"
            class="yard-overview-block"
            :class="{ muted: block.muted }"
          >
            <header>
              <strong>{{ block.id }}</strong>
              <span>{{ block.id === focusBlockId ? "当前动作区" : "背景区" }}</span>
            </header>

            <div class="yard-overview-rows">
              <div v-for="bay in block.bays" :key="bay.id" class="yard-overview-row">
                <span>{{ bay.label }}</span>
                <button
                  v-for="stack in bay.stacks"
                  :key="stack.id"
                  type="button"
                  class="yard-overview-stack"
                  :class="{
                    targetBox: targetContainerId && stack.tiers.includes(targetContainerId),
                    blockerBox: blockerContainerId && stack.tiers.includes(blockerContainerId),
                    relocationBox: destinationStack && destinationStack.id === stack.id,
                  }"
                  @click="selectStack(stack.id)"
                ></button>
              </div>
            </div>
          </section>
        </div>

        <div class="yard-action-toolbar process-toolbar">
          <button type="button" class="primary" @click="togglePlayback">
            {{ playing ? "暂停" : "播放" }}
          </button>
          <button type="button" class="secondary" @click="stepOnce">单步</button>
          <button type="button" class="secondary" @click="resetPlayback">重置</button>
        </div>
      </article>

      <article class="yard-microscope-card yard-action-controls">
        <div class="panel-header">
          <h2>当前动作显微镜</h2>
          <p>{{ microscopeSummary }}</p>
        </div>

        <div class="yard-microscope-scene refined-process-microscope">
          <article class="yard-microscope-column source">
            <header>
              <span>堆位状态</span>
              <strong>{{ sourceStackId || "待锁定" }}</strong>
            </header>
            <div class="yard-microscope-stack-view">
              <div
                v-for="(tier, index) in sourceTiers"
                :key="`source-${index}`"
                class="yard-microscope-tier"
                :class="{
                  target: tier === targetContainerId,
                  blocker: tier === blockerContainerId,
                  muted: !tier,
                }"
                :style="tier ? { background: containerTone(tier) } : undefined"
              >
                <span>{{ tier || "空位" }}</span>
              </div>
            </div>
          </article>

          <div class="yard-microscope-arrow">
            <span>{{ blockerContainerId ? "先搬走挡路箱" : "无阻塞，可直接提取" }}</span>
            <div></div>
          </div>

          <article class="yard-microscope-column target">
            <header>
              <span>{{ currentAction?.type === "retrieve" || !currentAction ? "交付位" : "落位" }}</span>
              <strong>{{ destinationLabel }}</strong>
            </header>
            <div class="yard-microscope-stack-view ghost">
              <div
                v-for="(tier, index) in destinationStack ? destinationTiers : [null, null, null, null]"
                :key="`target-${index}`"
                class="yard-microscope-tier"
                :class="{ relocation: blockerContainerId && index === 0, muted: !tier }"
                :style="tier ? { background: containerTone(tier) } : undefined"
              >
                <span>{{ tier || (blockerContainerId && index === 0 ? blockerContainerId : "空位") }}</span>
              </div>
            </div>
          </article>
        </div>
      </article>
    </section>

    <section class="yard-action-support">
      <article class="yard-explain-card yard-action-explain">
        <div class="panel-header">
          <h2>实验面板与 Explainability</h2>
          <p>先看动作过程，再调整策略和资源。</p>
        </div>

        <div class="yard-action-toolbar compact-toolbar">
          <label class="yard-action-inline">
            <span>堆位策略</span>
            <select v-model="settings.strategy">
              <option value="min_future_blocking">最少未来阻塞</option>
              <option value="nearest_slot">最近空位</option>
              <option value="batch_friendly">批次友好</option>
            </select>
          </label>
          <label class="yard-action-inline">
            <span>车辆派遣</span>
            <select v-model="settings.dispatchRule">
              <option value="integrated">集成平衡</option>
              <option value="nearest">最近车辆</option>
              <option value="queue_balance">队列均衡</option>
            </select>
          </label>
        </div>

        <button type="button" class="berth-advanced-toggle" @click="advancedOpen = !advancedOpen">
          {{ advancedOpen ? "收起高级实验参数" : "展开高级实验参数" }}
        </button>

        <div v-if="advancedOpen" class="berth-advanced-panel">
          <label class="berth-slider-row">
            <span>最大堆高</span>
            <input v-model="settings.maxTier" type="range" min="3" max="5" step="1" />
            <strong>{{ settings.maxTier }}</strong>
          </label>
          <label class="berth-slider-row">
            <span>场内车辆数</span>
            <input v-model="settings.truckCount" type="range" min="1" max="3" step="1" />
            <strong>{{ settings.truckCount }}</strong>
          </label>
        </div>

        <div class="yard-explain-grid">
          <article v-for="item in explainabilityCards" :key="item.label" class="yard-explain-item">
            <span>{{ item.label }}</span>
            <strong class="mono">{{ item.formula }}</strong>
            <p>{{ item.plain }}</p>
            <small>{{ item.live }}</small>
          </article>
        </div>

        <div class="scenario-log-list compact-log-list">
          <article
            v-for="item in requestQueue.slice(0, 3)"
            :key="item.id"
            class="scenario-log-item"
            :data-status="item.status"
          >
            <strong>{{ item.id }}</strong>
            <span>{{ item.type === "retrieve" ? "提箱" : "存箱" }} {{ item.containerId }}</span>
          </article>
        </div>
      </article>
    </section>
  </section>
</template>
