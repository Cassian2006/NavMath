import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";

const BASE_VESSELS = [
  {
    id: "V1",
    eta: 1.5,
    length: 280,
    workload: 1200,
    minCranes: 1,
    maxCranes: 3,
    priorityWeight: 1.0,
    preferred: ["B1", "B2"],
    color: "#0f766e",
  },
  {
    id: "V2",
    eta: 2.2,
    length: 340,
    workload: 1680,
    minCranes: 2,
    maxCranes: 4,
    priorityWeight: 1.2,
    preferred: ["B1"],
    color: "#2563eb",
  },
  {
    id: "V3",
    eta: 3.4,
    length: 220,
    workload: 980,
    minCranes: 1,
    maxCranes: 2,
    priorityWeight: 0.9,
    preferred: ["B2", "B3"],
    color: "#ea580c",
  },
  {
    id: "V4",
    eta: 4.8,
    length: 260,
    workload: 1120,
    minCranes: 1,
    maxCranes: 3,
    priorityWeight: 1.1,
    preferred: ["B2"],
    color: "#9333ea",
  },
  {
    id: "V5",
    eta: 5.1,
    length: 300,
    workload: 1560,
    minCranes: 2,
    maxCranes: 4,
    priorityWeight: 1.4,
    preferred: ["B1", "B2"],
    color: "#d97706",
  },
  {
    id: "V6",
    eta: 6.3,
    length: 210,
    workload: 860,
    minCranes: 1,
    maxCranes: 2,
    priorityWeight: 0.8,
    preferred: ["B3"],
    color: "#0ea5e9",
  },
  {
    id: "V7",
    eta: 7.0,
    length: 320,
    workload: 1430,
    minCranes: 2,
    maxCranes: 3,
    priorityWeight: 1.3,
    preferred: ["B1", "B2"],
    color: "#ef4444",
  },
  {
    id: "V8",
    eta: 8.1,
    length: 240,
    workload: 1040,
    minCranes: 1,
    maxCranes: 2,
    priorityWeight: 0.95,
    preferred: ["B2", "B3"],
    color: "#14b8a6",
  },
];

const BASE_BERTHS = [
  { id: "B1", length: 400 },
  { id: "B2", length: 350 },
  { id: "B3", length: 300 },
];

const RATE_PER_CRANE = 30;
const ALPHA = 0.86;
const SLOT_SIZE = 0.5;
const HORIZON = 72;
const TOTAL_CRANE_POSITIONS = 8;

function cloneBaseVessels() {
  return BASE_VESSELS.map((vessel) => ({ ...vessel }));
}

function formatHours(value) {
  return `${value.toFixed(1)} h`;
}

function sortVessels(vessels, rule) {
  const sorted = [...vessels];
  if (rule === "fcfs") {
    sorted.sort((a, b) => a.eta - b.eta);
  } else if (rule === "shortest") {
    sorted.sort((a, b) => a.workload - b.workload || a.eta - b.eta);
  } else if (rule === "priority") {
    sorted.sort((a, b) => b.priorityWeight - a.priorityWeight || a.eta - b.eta);
  } else {
    sorted.sort((a, b) => {
      const scoreA = a.eta * 0.6 + a.workload / 1300 - a.priorityWeight * 0.8;
      const scoreB = b.eta * 0.6 + b.workload / 1300 - b.priorityWeight * 0.8;
      return scoreA - scoreB;
    });
  }
  return sorted;
}

function candidateBerths(vessel, berths) {
  const preferred = berths.filter((berth) => vessel.preferred.includes(berth.id));
  const fallback = berths.filter((berth) => !vessel.preferred.includes(berth.id));
  return [...preferred, ...fallback];
}

function slotIndex(time) {
  return Math.max(0, Math.floor(time / SLOT_SIZE));
}

function getCranesAt(craneUsage, time) {
  return craneUsage[slotIndex(time)] || 0;
}

function reserveCranes(craneUsage, start, end, cranes) {
  for (let time = start; time < end; time += SLOT_SIZE) {
    const index = slotIndex(time);
    craneUsage[index] = (craneUsage[index] || 0) + cranes;
  }
}

function overlappingAssignments(assignments, start, end) {
  return assignments.filter((item) => start < item.end && end > item.start);
}

function findCraneWindow(assignments, berthIndex, start, end, cranes, settings) {
  const overlaps = overlappingAssignments(assignments, start, end);
  const safetyDistance = settings.safetyDistance;
  const maxStart = TOTAL_CRANE_POSITIONS - cranes + 1;
  for (let craneStart = 1; craneStart <= maxStart; craneStart += 1) {
    const craneEnd = craneStart + cranes - 1;
    let feasible = true;
    for (const active of overlaps) {
      const gap =
        berthIndex > active.berthIndex
          ? craneStart - active.craneEnd
          : berthIndex < active.berthIndex
            ? active.craneStart - craneEnd
            : -1;
      if (berthIndex === active.berthIndex) {
        feasible = false;
        break;
      }
      if (gap < safetyDistance) {
        feasible = false;
        break;
      }
    }
    if (feasible) {
      return { craneStart, craneEnd, overlapCount: overlaps.length };
    }
  }
  return null;
}

function serviceTime(workload, cranes) {
  return workload / (RATE_PER_CRANE * Math.pow(cranes, ALPHA));
}

function evaluateAssignment(vessel, berth, berthAvailability, craneUsage, settings, assignments, berthIndexMap) {
  if (vessel.length > berth.length) {
    return null;
  }

  let best = null;
  let start = Math.max(vessel.eta, berthAvailability[berth.id] || 0);
  const craneCap = Math.min(settings.cranes, vessel.maxCranes);
  if (craneCap < vessel.minCranes) {
    return null;
  }

  while (start <= HORIZON) {
    for (let cranes = craneCap; cranes >= vessel.minCranes; cranes -= 1) {
      const duration = serviceTime(vessel.workload, cranes);
      const end = start + duration;
      let feasible = true;
      for (let time = start; time < end; time += SLOT_SIZE) {
        if (getCranesAt(craneUsage, time) + cranes > settings.cranes) {
          feasible = false;
          break;
        }
      }
      if (!feasible) {
        continue;
      }

      let craneWindow = null;
      let interferencePenalty = 0;
      if (settings.optimizationMode === "advanced") {
        craneWindow = findCraneWindow(assignments, berthIndexMap[berth.id], start, end, cranes, settings);
        if (!craneWindow) {
          continue;
        }
        interferencePenalty = craneWindow.overlapCount * 0.4;
      }

      const wait = Math.max(0, start - vessel.eta);
      const turnaround = end - vessel.eta;
      const idle = Math.max(0, start - (berthAvailability[berth.id] || 0));
      const throughputBonus = vessel.workload / 1000;
      const makespanPenalty = settings.optimizationMode === "advanced" ? end * settings.weights.makespan : 0;
      const score =
        settings.weights.waiting * wait +
        settings.weights.turnaround * turnaround * vessel.priorityWeight +
        makespanPenalty +
        settings.weights.idle * idle -
        settings.weights.throughput * throughputBonus +
        interferencePenalty -
        cranes * 0.12;

      if (!best || score < best.score) {
        best = {
          berthId: berth.id,
          start,
          end,
          cranes,
          score,
          wait,
          turnaround,
          craneStart: craneWindow?.craneStart ?? 1,
          craneEnd: craneWindow?.craneEnd ?? cranes,
          overlapCount: craneWindow?.overlapCount ?? 0,
        };
      }
    }

    if (best) {
      return best;
    }
    start += SLOT_SIZE;
  }

  return null;
}

function buildSchedule(vessels, berths, settings) {
  const berthAvailability = Object.fromEntries(berths.map((berth) => [berth.id, 0]));
  const craneUsage = Array.from({ length: Math.ceil(HORIZON / SLOT_SIZE) + 1 }, () => 0);
  const assignments = [];
  const berthIndexMap = Object.fromEntries(berths.map((berth, index) => [berth.id, index]));

  sortVessels(vessels, settings.rule).forEach((vessel) => {
    let best = null;
    candidateBerths(vessel, berths).forEach((berth) => {
      const assignment = evaluateAssignment(vessel, berth, berthAvailability, craneUsage, settings, assignments, berthIndexMap);
      if (assignment && (!best || assignment.score < best.score)) {
        best = assignment;
      }
    });

    if (!best) {
      return;
    }

    berthAvailability[best.berthId] = best.end;
    reserveCranes(craneUsage, best.start, best.end, best.cranes);
    assignments.push({
      ...vessel,
      berthId: best.berthId,
      start: best.start,
      end: best.end,
      cranes: best.cranes,
      wait: best.wait,
      turnaround: best.turnaround,
      serviceDuration: best.end - best.start,
      craneStart: best.craneStart,
      craneEnd: best.craneEnd,
      overlapCount: best.overlapCount,
      berthIndex: berthIndexMap[best.berthId],
    });
  });

  const totalWaiting = assignments.reduce((sum, vessel) => sum + vessel.wait, 0);
  const avgWaiting = assignments.length ? totalWaiting / assignments.length : 0;
  const maxEnd = assignments.reduce((max, vessel) => Math.max(max, vessel.end), 0);
  const berthBusyTime = assignments.reduce((sum, vessel) => sum + vessel.serviceDuration, 0);
  const berthUtilization = maxEnd > 0 ? berthBusyTime / (berths.length * maxEnd) : 0;
  const craneBusyTime = assignments.reduce((sum, vessel) => sum + vessel.serviceDuration * vessel.cranes, 0);
  const craneUtilization = maxEnd > 0 ? craneBusyTime / (settings.cranes * maxEnd) : 0;
  const delayPenalty = assignments.reduce((sum, vessel) => sum + vessel.wait * vessel.priorityWeight * 18, 0);
  const throughput = assignments.reduce((sum, vessel) => sum + vessel.workload, 0);
  const maxCompletion = assignments.reduce((max, vessel) => Math.max(max, vessel.end), 0);
  const craneInterferenceRisk = assignments.reduce((sum, vessel) => sum + vessel.overlapCount, 0);

  return {
    assignments,
    maxEnd: Math.max(18, maxEnd + 2),
    metrics: {
      totalWaiting,
      avgWaiting,
      berthUtilization,
      craneUtilization,
      completedShips: assignments.length,
      delayPenalty,
      throughput,
      maxCompletion,
      craneInterferenceRisk,
    },
  };
}

function roundRect(ctx, x, y, width, height, radius) {
  const r = Math.min(radius, width / 2, height / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + width, y, x + width, y + height, r);
  ctx.arcTo(x + width, y + height, x, y + height, r);
  ctx.arcTo(x, y + height, x, y, r);
  ctx.arcTo(x, y, x + width, y, r);
  ctx.closePath();
}

function drawStatusBadge(ctx, x, y, text, tone) {
  ctx.save();
  ctx.font = "700 10px 'Noto Sans SC'";
  const paddingX = 10;
  const width = ctx.measureText(text).width + paddingX * 2;
  roundRect(ctx, x, y, width, 22, 11);
  ctx.fillStyle = tone.fill;
  ctx.fill();
  ctx.strokeStyle = tone.stroke;
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.fillStyle = tone.text;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, x + width / 2, y + 11);
  ctx.restore();
}

function drawShip(ctx, vessel, x, y, width, height, options = {}) {
  const { emphasis = "muted", badgeText = "", pulse = 0 } = options;
  const styles = {
    focus: {
      fillA: vessel.color,
      fillB: "#10253f",
      stroke: "rgba(125, 211, 252, 0.92)",
      shadow: "rgba(56, 189, 248, 0.28)",
      alpha: 1,
    },
    blocking: {
      fillA: "#f97316",
      fillB: "#7c2d12",
      stroke: "rgba(251, 146, 60, 0.82)",
      shadow: "rgba(249, 115, 22, 0.18)",
      alpha: 0.96,
    },
    active: {
      fillA: "#2563eb",
      fillB: "#10253f",
      stroke: "rgba(148, 163, 184, 0.7)",
      shadow: "rgba(37, 99, 235, 0.18)",
      alpha: 0.96,
    },
    muted: {
      fillA: "rgba(71, 85, 105, 0.56)",
      fillB: "rgba(30, 41, 59, 0.72)",
      stroke: "rgba(148, 163, 184, 0.32)",
      shadow: "rgba(15, 23, 42, 0.08)",
      alpha: 0.56,
    },
  };
  const style = styles[emphasis] || styles.muted;
  const hullPulse = emphasis === "focus" ? 1 + pulse * 0.02 : 1;

  ctx.save();
  ctx.translate(x, y);
  ctx.scale(hullPulse, hullPulse);
  ctx.globalAlpha = style.alpha;

  if (emphasis === "focus") {
    ctx.shadowColor = style.shadow;
    ctx.shadowBlur = 18 + pulse * 6;
  } else {
    ctx.shadowColor = style.shadow;
    ctx.shadowBlur = 10;
  }

  const hull = ctx.createLinearGradient(0, 0, width, height);
  hull.addColorStop(0, style.fillA);
  hull.addColorStop(1, style.fillB);

  ctx.beginPath();
  ctx.moveTo(12, height * 0.12);
  ctx.lineTo(width - 22, height * 0.12);
  ctx.quadraticCurveTo(width - 2, height * 0.5, width - 22, height * 0.88);
  ctx.lineTo(12, height * 0.88);
  ctx.quadraticCurveTo(0, height * 0.5, 12, height * 0.12);
  ctx.closePath();
  ctx.fillStyle = hull;
  ctx.fill();

  ctx.shadowBlur = 0;
  ctx.strokeStyle = style.stroke;
  ctx.lineWidth = emphasis === "focus" ? 2.2 : 1.3;
  ctx.stroke();

  roundRect(ctx, width * 0.26, height * 0.28, width * 0.2, height * 0.18, 6);
  ctx.fillStyle = "rgba(255,255,255,0.14)";
  ctx.fill();

  roundRect(ctx, width * 0.48, height * 0.23, width * 0.14, height * 0.12, 5);
  ctx.fillStyle = "rgba(255,255,255,0.1)";
  ctx.fill();

  ctx.strokeStyle = "rgba(255,255,255,0.08)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(width * 0.18, height * 0.5);
  ctx.lineTo(width * 0.8, height * 0.5);
  ctx.stroke();

  ctx.fillStyle = "#f8fafc";
  ctx.font = "700 12px 'Noto Sans SC'";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(vessel.id, width * 0.48, height * 0.5);

  ctx.restore();

  if (badgeText) {
    const toneMap = {
      WAITING: {
        fill: "rgba(15, 23, 42, 0.84)",
        stroke: "rgba(125, 211, 252, 0.44)",
        text: "#e2e8f0",
      },
      TARGET: {
        fill: "rgba(8, 47, 73, 0.86)",
        stroke: "rgba(56, 189, 248, 0.42)",
        text: "#e0f2fe",
      },
      BLOCKING: {
        fill: "rgba(124, 45, 18, 0.88)",
        stroke: "rgba(251, 146, 60, 0.44)",
        text: "#ffedd5",
      },
      "IN SERVICE": {
        fill: "rgba(15, 118, 110, 0.84)",
        stroke: "rgba(45, 212, 191, 0.4)",
        text: "#ecfeff",
      },
      DEPARTED: {
        fill: "rgba(51, 65, 85, 0.82)",
        stroke: "rgba(148, 163, 184, 0.36)",
        text: "#e2e8f0",
      },
    };
    drawStatusBadge(ctx, x + width * 0.1, y - 24, badgeText, toneMap[badgeText] || toneMap.WAITING);
  }
}

export function useBerthSchedulingDemo() {
  const settings = reactive({
    berthCount: 3,
    cranes: 6,
    arrivalScale: 1,
    workloadScale: 1,
    rule: "greedy",
    optimizationMode: "basic",
    safetyDistance: 1,
    weights: {
      waiting: 1,
      turnaround: 0.6,
      idle: 0.3,
      throughput: 0.8,
      makespan: 0.5,
    },
  });

  const editableVessels = ref(cloneBaseVessels());
  const selectedVesselId = ref(editableVessels.value[0].id);
  const canvasRef = ref(null);
  const simulationTime = ref(0);
  const playing = ref(false);
  const playbackSpeed = ref(1);
  const runtime = reactive({ frameId: 0, lastTick: 0 });

  const berths = computed(() => BASE_BERTHS.slice(0, settings.berthCount));

  const vessels = computed(() =>
    editableVessels.value.map((vessel, index) => ({
      ...vessel,
      eta: Number(vessel.eta),
      workload: Number(vessel.workload),
      maxCranes: Number(vessel.maxCranes),
      minCranes: Number(vessel.minCranes),
      adjustedEta: Number(vessel.eta) * settings.arrivalScale + index * 0.18,
      adjustedWorkload: Number(vessel.workload) * settings.workloadScale,
    }))
  );

  const schedule = computed(() =>
    buildSchedule(
      vessels.value.map((vessel) => ({
        ...vessel,
        eta: vessel.adjustedEta,
        workload: vessel.adjustedWorkload,
      })),
      berths.value,
      settings
    )
  );

  const selectedVessel = computed(() =>
    editableVessels.value.find((vessel) => vessel.id === selectedVesselId.value) || editableVessels.value[0]
  );

  const stageNarrative = computed(() => {
    const waitHeavy = schedule.value.assignments
      .slice()
      .sort((a, b) => b.wait - a.wait)
      .slice(0, 2)
      .map((item) => `${item.id} 等待 ${item.wait.toFixed(1)}h`)
      .join("，");
    return [
      {
        title: "为什么不是先来先服务",
        body: "短作业船和高优先级船适当前置，可以显著降低全局等待时间。",
      },
      {
        title: "岸桥为什么要动态分配",
        body:
          settings.optimizationMode === "advanced"
            ? "高级模式会同时检查岸桥不可穿越和安全距离，避免看似可行但实际冲突的分配。"
            : "同一时刻多给一条船多台岸桥，会压缩它的作业时间，但可能挤占别的船。",
      },
      {
        title: "当前方案最需要关注什么",
        body:
          settings.optimizationMode === "advanced"
            ? `最大完工时间 ${schedule.value.metrics.maxCompletion.toFixed(1)}h，冲突风险计数 ${schedule.value.metrics.craneInterferenceRisk}。`
            : waitHeavy || "当前方案等待时间分布较均衡，适合用于说明全局优化。",
      },
    ];
  });

  const logs = computed(() => {
    const top = schedule.value.assignments.slice().sort((a, b) => a.start - b.start).slice(0, 5);
    return top.map((assignment) => ({
      id: assignment.id,
      title: `${assignment.id} -> ${assignment.berthId}`,
      body:
        settings.optimizationMode === "advanced"
          ? `ETA ${assignment.eta.toFixed(1)}h，实际 ${assignment.start.toFixed(1)}h 靠泊，QC ${assignment.craneStart}-${assignment.craneEnd}，安全间隔 ${settings.safetyDistance}。`
          : `ETA ${assignment.eta.toFixed(1)}h，实际 ${assignment.start.toFixed(1)}h 靠泊，分配 ${assignment.cranes} 台岸桥。`,
    }));
  });

  function updateSelectedVessel(patch) {
    editableVessels.value = editableVessels.value.map((vessel) =>
      vessel.id === selectedVesselId.value ? { ...vessel, ...patch } : vessel
    );
  }

  function setCanvas(element) {
    canvasRef.value = element;
    drawScene();
  }

  function drawScene() {
    const canvas = canvasRef.value;
    if (!canvas) {
      return;
    }

    const width = canvas.clientWidth || 880;
    const height = canvas.clientHeight || 440;
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }

    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, width, height);

    const bg = ctx.createLinearGradient(0, 0, width, height);
    bg.addColorStop(0, "#eef3f7");
    bg.addColorStop(1, "#dde8ee");
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, width, height);

    const pulse = (Math.sin(performance.now() / 800) + 1) / 2;

    const sea = ctx.createLinearGradient(0, 0, 0, height);
    sea.addColorStop(0, "#d9eaf3");
    sea.addColorStop(1, "#bfd7e4");
    ctx.fillStyle = sea;
    roundRect(ctx, 28, 28, 252, height - 56, 28);
    ctx.fill();

    ctx.fillStyle = "rgba(255,255,255,0.16)";
    for (let i = 0; i < 5; i += 1) {
      ctx.fillRect(52, 68 + i * 72, 172, 1);
    }

    ctx.fillStyle = "rgba(15,23,42,0.72)";
    ctx.font = "700 14px 'Noto Sans SC'";
    ctx.fillText("海侧航道", 46, 54);

    ctx.fillStyle = "rgba(226,232,240,0.82)";
    roundRect(ctx, 296, 28, width - 324, height - 56, 28);
    ctx.fill();

    ctx.fillStyle = "#738293";
    ctx.fillRect(326, 78, width - 384, 4);

    const berthSlots = berths.value.map((berth, index) => ({
      ...berth,
      x: 344,
      y: 96 + index * 106,
      width: Math.min(width - 436, 350),
      height: 76,
    }));

    const clock = simulationTime.value % schedule.value.maxEnd;
    const activeAssignment =
      schedule.value.assignments.find((item) => clock >= item.start && clock <= item.end) || null;
    const waitingAssignment =
      schedule.value.assignments
        .filter((item) => item.start > clock)
        .sort((a, b) => (b.start - b.eta) - (a.start - a.eta))[0] || null;
    const blockingAssignment = waitingAssignment
      ? schedule.value.assignments.find(
          (item) =>
            item.berthId === waitingAssignment.berthId &&
            item.id !== waitingAssignment.id &&
            item.start <= waitingAssignment.start &&
            item.end >= waitingAssignment.start
        ) || null
      : null;

    berthSlots.forEach((berth) => {
      const isTarget = waitingAssignment?.berthId === berth.id;
      roundRect(ctx, berth.x, berth.y, berth.width, berth.height, 24);
      ctx.fillStyle = isTarget
        ? `rgba(255,255,255,${0.94 + pulse * 0.03})`
        : "rgba(255,255,255,0.7)";
      ctx.fill();
      ctx.strokeStyle = isTarget ? "rgba(56,189,248,0.55)" : "rgba(71,85,105,0.12)";
      ctx.lineWidth = isTarget ? 1.8 : 1;
      ctx.stroke();

      if (isTarget) {
        ctx.save();
        ctx.shadowColor = "rgba(56,189,248,0.22)";
        ctx.shadowBlur = 22 + pulse * 8;
        ctx.strokeStyle = "rgba(125,211,252,0.28)";
        ctx.lineWidth = 4;
        roundRect(ctx, berth.x - 2, berth.y - 2, berth.width + 4, berth.height + 4, 26);
        ctx.stroke();
        ctx.restore();
      }

      ctx.fillStyle = "#0f172a";
      ctx.font = "700 13px 'Noto Sans SC'";
      ctx.fillText(berth.id, berth.x + 14, berth.y + 20);
      ctx.fillStyle = "rgba(71,85,105,0.72)";
      ctx.font = "500 11px 'Noto Sans SC'";
      ctx.fillText(`${berth.length}m`, berth.x + 14, berth.y + 38);
    });

    const pendingAssignments = schedule.value.assignments
      .filter((item) => clock < item.start)
      .sort((a, b) => a.start - b.start);
    const departedAssignments = schedule.value.assignments
      .filter((item) => clock > item.end)
      .sort((a, b) => a.end - b.end);

    schedule.value.assignments.forEach((assignment, index) => {
      const berth = berthSlots.find((item) => item.id === assignment.berthId);
      if (!berth) {
        return;
      }

      let badgeText = "WAITING";
      let emphasis = "muted";
      const pendingIndex = pendingAssignments.findIndex((item) => item.id === assignment.id);
      const departedIndex = departedAssignments.findIndex((item) => item.id === assignment.id);
      let x = 76 + (Math.max(pendingIndex, 0) % 2) * 90;
      let y = 94 + Math.floor(Math.max(pendingIndex, 0) / 2) * 68;

      if (clock >= assignment.start && clock <= assignment.end) {
        badgeText = "IN SERVICE";
        emphasis =
          assignment.id === blockingAssignment?.id
            ? "blocking"
            : assignment.id === activeAssignment?.id
              ? "active"
              : "muted";
        x = berth.x + 26;
        y = berth.y + 24;

        for (let crane = 0; crane < assignment.cranes; crane += 1) {
          const craneX =
            settings.optimizationMode === "advanced"
              ? berth.x + 22 + (assignment.craneStart - 1 + crane) * 32
              : berth.x + 22 + crane * 38;
          const craneActive = assignment.id === blockingAssignment?.id || assignment.id === activeAssignment?.id;
          ctx.save();
          ctx.strokeStyle = craneActive ? "rgba(15,23,42,0.78)" : "rgba(100,116,139,0.4)";
          ctx.lineWidth = 1.4;
          ctx.beginPath();
          ctx.moveTo(craneX + 8, berth.y - 4);
          ctx.lineTo(craneX + 8, berth.y - 28);
          ctx.lineTo(craneX + 34, berth.y - 28);
          ctx.stroke();
          ctx.fillStyle = craneActive ? `rgba(45,212,191,${0.28 + pulse * 0.1})` : "rgba(148,163,184,0.18)";
          roundRect(ctx, craneX + 14, berth.y - 22, 18, 8, 4);
          ctx.fill();
          ctx.restore();
        }
      } else if (clock > assignment.end) {
        badgeText = "DEPARTED";
        emphasis = "muted";
        x = width - 208 + (Math.max(departedIndex, 0) % 2) * 92;
        y = 76 + Math.floor(Math.max(departedIndex, 0) / 2) * 54;
      } else if (assignment.id === waitingAssignment?.id) {
        badgeText = "WAITING";
        emphasis = "focus";
        x = 96;
        y = 138 + index * 18;
      }

      if (assignment.id === blockingAssignment?.id) {
        badgeText = "BLOCKING";
        emphasis = "blocking";
      }

      const shipWidth = Math.max(78, assignment.length / 4.5);
      drawShip(ctx, assignment, x, y, shipWidth, 30, {
        emphasis,
        badgeText,
        pulse,
      });
    });

    if (waitingAssignment) {
      const targetBerth = berthSlots.find((item) => item.id === waitingAssignment.berthId);
      const focusShipWidth = Math.max(78, waitingAssignment.length / 4.5);
      const focusShipX = 96;
      const focusShipY =
        138 + schedule.value.assignments.findIndex((item) => item.id === waitingAssignment.id) * 18;
      const startX = focusShipX + focusShipWidth + 14;
      const startY = focusShipY + 15;
      const endX = targetBerth.x - 12;
      const endY = targetBerth.y + targetBerth.height / 2;

      ctx.save();
      ctx.strokeStyle = "rgba(56,189,248,0.62)";
      ctx.lineWidth = 1.5;
      ctx.setLineDash([6, 7]);
      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.bezierCurveTo(startX + 88, startY - 8, endX - 76, endY - 8, endX, endY);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "rgba(56,189,248,0.82)";
      ctx.beginPath();
      ctx.moveTo(endX, endY);
      ctx.lineTo(endX - 10, endY - 6);
      ctx.lineTo(endX - 10, endY + 6);
      ctx.closePath();
      ctx.fill();
      ctx.restore();

      drawStatusBadge(ctx, targetBerth.x + targetBerth.width - 88, targetBerth.y + 12, "TARGET", {
        fill: "rgba(8,47,73,0.86)",
        stroke: "rgba(56,189,248,0.36)",
        text: "#e0f2fe",
      });

      if (blockingAssignment) {
        const blockBerth = berthSlots.find((item) => item.id === blockingAssignment.berthId);
        drawStatusBadge(ctx, blockBerth.x + blockBerth.width - 112, blockBerth.y + blockBerth.height - 34, "OCCUPIED", {
          fill: "rgba(124,45,18,0.86)",
          stroke: "rgba(251,146,60,0.36)",
          text: "#ffedd5",
        });
      }
    }

    roundRect(ctx, width - 206, height - 92, 174, 58, 18);
    ctx.fillStyle = "rgba(255,255,255,0.84)";
    ctx.fill();
    ctx.strokeStyle = "rgba(20,33,61,0.08)";
    ctx.stroke();
    ctx.fillStyle = "#0f172a";
    ctx.font = "700 13px 'Noto Sans SC'";
    ctx.fillText(`教学时钟：${clock.toFixed(1)} h`, width - 188, height - 61);
    ctx.font = "500 12px 'Noto Sans SC'";
    ctx.fillStyle = "#52606d";
    ctx.fillText(`当前规则：${settings.rule}`, width - 188, height - 41);
  }

function tick(now) {
    if (!runtime.lastTick) {
      runtime.lastTick = now;
    }
    const delta = (now - runtime.lastTick) / 1000;
    runtime.lastTick = now;
    if (playing.value) {
      simulationTime.value += delta * playbackSpeed.value * 1.5;
    }
    drawScene();
    runtime.frameId = window.requestAnimationFrame(tick);
  }

  function resetPlayback() {
    simulationTime.value = 0;
  }

  function togglePlayback() {
    playing.value = !playing.value;
  }

  watch(
    [
      schedule,
      selectedVesselId,
      () => settings.rule,
      () => settings.berthCount,
      () => settings.cranes,
      () => settings.optimizationMode,
      () => settings.safetyDistance,
      () => settings.weights.makespan,
    ],
    () => {
      resetPlayback();
      drawScene();
    },
    { deep: true }
  );

  function startLoop() {
    if (runtime.frameId) {
      window.cancelAnimationFrame(runtime.frameId);
    }
    runtime.lastTick = 0;
    runtime.frameId = window.requestAnimationFrame(tick);
  }

  onBeforeUnmount(() => {
    if (runtime.frameId) {
      window.cancelAnimationFrame(runtime.frameId);
    }
  });

  startLoop();

  return {
    settings,
    selectedVesselId,
    selectedVessel,
    berths,
    vessels,
    schedule,
    stageNarrative,
    logs,
    simulationTime,
    playing,
    playbackSpeed,
    setCanvas,
    resetPlayback,
    togglePlayback,
    updateSelectedVessel,
    formatHours,
  };
}
