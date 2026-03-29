import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";

const BLOCKS = ["B1", "B2"];
const BAYS_PER_BLOCK = 4;
const STACKS_PER_BAY = 5;

const INITIAL_STACKS = {
  "B1-Bay1-S1": ["C03", "C11", "C17"],
  "B1-Bay1-S2": ["C08"],
  "B1-Bay1-S3": ["C20", "C52"],
  "B1-Bay2-S1": ["C24", "C35"],
  "B1-Bay2-S2": ["C18", "C41", "C63"],
  "B1-Bay2-S4": ["C29"],
  "B1-Bay3-S2": ["C31", "C56"],
  "B1-Bay3-S5": ["C39"],
  "B1-Bay4-S1": ["C44", "C61"],
  "B2-Bay1-S1": ["C09", "C13"],
  "B2-Bay1-S3": ["C22", "C47"],
  "B2-Bay2-S2": ["C05", "C27", "C58"],
  "B2-Bay2-S4": ["C12"],
  "B2-Bay3-S1": ["C15", "C28"],
  "B2-Bay3-S3": ["C26", "C49", "C72"],
  "B2-Bay4-S2": ["C34"],
  "B2-Bay4-S4": ["C46", "C70"],
};

const CONTAINERS = {
  C03: { priority: 2, departureBatch: "V2" },
  C05: { priority: 1, departureBatch: "V1" },
  C08: { priority: 1, departureBatch: "V1" },
  C09: { priority: 3, departureBatch: "V3" },
  C11: { priority: 2, departureBatch: "V2" },
  C12: { priority: 2, departureBatch: "V2" },
  C13: { priority: 1, departureBatch: "V1" },
  C15: { priority: 3, departureBatch: "V4" },
  C17: { priority: 1, departureBatch: "V1" },
  C18: { priority: 2, departureBatch: "V3" },
  C20: { priority: 3, departureBatch: "V4" },
  C22: { priority: 2, departureBatch: "V2" },
  C24: { priority: 3, departureBatch: "V4" },
  C26: { priority: 2, departureBatch: "V3" },
  C27: { priority: 2, departureBatch: "V2" },
  C28: { priority: 1, departureBatch: "V1" },
  C29: { priority: 3, departureBatch: "V4" },
  C31: { priority: 1, departureBatch: "V2" },
  C34: { priority: 2, departureBatch: "V3" },
  C35: { priority: 2, departureBatch: "V2" },
  C39: { priority: 1, departureBatch: "V1" },
  C41: { priority: 3, departureBatch: "V4" },
  C44: { priority: 2, departureBatch: "V3" },
  C46: { priority: 1, departureBatch: "V1" },
  C47: { priority: 2, departureBatch: "V2" },
  C49: { priority: 3, departureBatch: "V4" },
  C52: { priority: 2, departureBatch: "V2" },
  C56: { priority: 1, departureBatch: "V1" },
  C58: { priority: 3, departureBatch: "V4" },
  C61: { priority: 2, departureBatch: "V3" },
  C63: { priority: 1, departureBatch: "V2" },
  C66: { priority: 2, departureBatch: "V2" },
  C70: { priority: 2, departureBatch: "V3" },
  C72: { priority: 3, departureBatch: "V4" },
  C60: { priority: 1, departureBatch: "V1" },
};

const REQUESTS = [
  { id: "R1", time: 0, type: "retrieve", containerId: "C17", block: "B1" },
  { id: "R2", time: 1.2, type: "store", containerId: "C60", block: "B1" },
  { id: "R3", time: 2.6, type: "retrieve", containerId: "C08", block: "B1" },
  { id: "R4", time: 3.4, type: "retrieve", containerId: "C52", block: "B1" },
  { id: "R5", time: 4.2, type: "store", containerId: "C66", block: "B2" },
  { id: "R6", time: 5.4, type: "retrieve", containerId: "C46", block: "B2" },
];

const BATCH_COLORS = {
  V1: "#ef4444",
  V2: "#2563eb",
  V3: "#14b8a6",
  V4: "#d97706",
};

function formatHours(value) {
  return `${value.toFixed(1)} h`;
}

function cloneStacks(stacks) {
  return Object.fromEntries(Object.entries(stacks).map(([key, value]) => [key, [...value]]));
}

function getContainerMeta(containerId) {
  return CONTAINERS[containerId] || { priority: 2, departureBatch: "V2" };
}

function parseStackId(stackId) {
  const [block, bayText, stackText] = stackId.split("-");
  return {
    block,
    bay: Number(bayText.replace("Bay", "")),
    stack: Number(stackText.replace("S", "")),
  };
}

function stackDistance(a, b) {
  const source = typeof a === "string" ? parseStackId(a) : a;
  const target = typeof b === "string" ? parseStackId(b) : b;
  return Math.abs(source.bay - target.bay) * 1.6 + Math.abs(source.stack - target.stack) * 0.8;
}

function findContainer(stacks, containerId) {
  for (const [stackId, stack] of Object.entries(stacks)) {
    const tierIndex = stack.indexOf(containerId);
    if (tierIndex !== -1) {
      return { stackId, tierIndex, stack };
    }
  }
  return null;
}

function futureBlockingScore(stack, meta, pendingRequests) {
  const batchNumber = Number(meta.departureBatch.replace("V", ""));
  const stackPenalty = stack.reduce((sum, containerId) => {
    const itemMeta = getContainerMeta(containerId);
    const itemBatch = Number(itemMeta.departureBatch.replace("V", ""));
    return sum + (itemBatch < batchNumber ? 1.6 : 0.45);
  }, 0);
  const pendingPenalty = pendingRequests.reduce((sum, request) => {
    if (request.type !== "retrieve") {
      return sum;
    }
    const requestMeta = getContainerMeta(request.containerId);
    return sum + (requestMeta.departureBatch === meta.departureBatch ? 0.7 : 0.2);
  }, 0);
  return stackPenalty + pendingPenalty;
}

function legalDestinations(stacks, fromStackId, request, settings) {
  return Object.entries(stacks)
    .filter(([stackId, stack]) => {
      if (fromStackId && stackId === fromStackId) {
        return false;
      }
      const parsed = parseStackId(stackId);
      return parsed.block === request.block && stack.length < settings.maxTier;
    })
    .map(([stackId, stack]) => ({ stackId, stack }));
}

function chooseRelocationTarget(stacks, fromStackId, containerId, request, pendingRequests, settings) {
  const meta = getContainerMeta(containerId);
  const candidates = legalDestinations(stacks, fromStackId, request, settings);
  if (!candidates.length) {
    return null;
  }

  return candidates
    .map((candidate) => {
      const distance = stackDistance(fromStackId, candidate.stackId);
      const futureBlocking = futureBlockingScore(candidate.stack, meta, pendingRequests);
      const top = candidate.stack[candidate.stack.length - 1];
      const topMeta = top ? getContainerMeta(top) : null;
      const batchFit = topMeta ? (topMeta.departureBatch === meta.departureBatch ? -1.2 : 0.8) : -1.6;
      let score = 0;
      if (settings.strategy === "nearest_slot") {
        score = distance + candidate.stack.length * 0.15;
      } else if (settings.strategy === "batch_friendly") {
        score = distance * 0.45 + batchFit + futureBlocking * 0.45;
      } else {
        score = distance * 0.55 + futureBlocking + candidate.stack.length * 0.18;
      }
      return { stackId: candidate.stackId, distance, futureBlocking, score };
    })
    .sort((a, b) => a.score - b.score)[0];
}

function chooseStoreTarget(stacks, request, settings) {
  const meta = getContainerMeta(request.containerId);
  const candidates = legalDestinations(stacks, null, request, settings);
  if (!candidates.length) {
    return null;
  }

  return candidates
    .map((candidate) => {
      const parsed = parseStackId(candidate.stackId);
      const travel = parsed.bay * 0.8 + parsed.stack * 0.35;
      const futureBlocking = futureBlockingScore(candidate.stack, meta, []);
      const top = candidate.stack[candidate.stack.length - 1];
      const topMeta = top ? getContainerMeta(top) : null;
      const batchFit = topMeta ? (topMeta.departureBatch === meta.departureBatch ? -1.3 : 0.7) : -1.2;
      let score = 0;
      if (settings.strategy === "nearest_slot") {
        score = travel + candidate.stack.length * 0.12;
      } else if (settings.strategy === "batch_friendly") {
        score = travel * 0.5 + batchFit + futureBlocking * 0.4;
      } else {
        score = travel * 0.45 + futureBlocking * 0.85;
      }
      return { stackId: candidate.stackId, futureBlocking, score };
    })
    .sort((a, b) => a.score - b.score)[0];
}

function estimateRemainingRelocations(stacks, pendingRequests) {
  return pendingRequests.reduce((sum, request) => {
    if (request.type !== "retrieve") {
      return sum;
    }
    const location = findContainer(stacks, request.containerId);
    if (!location) {
      return sum;
    }
    return sum + Math.max(0, location.stack.length - location.tierIndex - 1);
  }, 0);
}

function moveContainer(stacks, fromStackId, toStackId, containerId) {
  stacks[fromStackId] = stacks[fromStackId].filter((item) => item !== containerId);
  stacks[toStackId] = [...(stacks[toStackId] || []), containerId];
}

function pushRequestSummary(map, request, action) {
  const current = map[request.id] || {
    id: request.id,
    request,
    start: action.start,
    end: action.end,
    relocations: 0,
    vehicleMoves: 0,
  };
  current.start = Math.min(current.start, action.start);
  current.end = Math.max(current.end, action.end);
  if (action.type === "relocate") {
    current.relocations += 1;
  }
  if (action.truckId) {
    current.vehicleMoves += 1;
  }
  map[request.id] = current;
}

function createTruckPool(settings) {
  return Array.from({ length: settings.truckCount }, (_, index) => ({
    id: `IT${index + 1}`,
    availableAt: 0,
    location: index % 2 === 0 ? "Gate" : "Quay",
  }));
}

function travelFromNode(fromNode, stackId, block) {
  if (!fromNode || fromNode === "Gate") {
    return { distance: 2.4, lane: `${block}-Gate` };
  }
  if (fromNode === "Quay") {
    return { distance: 3.2, lane: `${block}-Quay` };
  }
  return { distance: stackDistance(fromNode, stackId), lane: `${block}-Yard` };
}

function travelToNode(stackId, toNode, block) {
  if (toNode === "Gate") {
    return { distance: 2.6, lane: `${block}-Gate` };
  }
  if (toNode === "Quay") {
    return { distance: 3.4, lane: `${block}-Quay` };
  }
  if (toNode === "YardBuffer") {
    return { distance: 1.2, lane: `${block}-Yard` };
  }
  return { distance: stackDistance(stackId, toNode), lane: `${block}-Yard` };
}

function scoreTruckCandidate(truck, request, readyAt, stackId, settings) {
  const inbound = request.type === "store" ? travelFromNode(truck.location, stackId, request.block) : travelFromNode(truck.location, stackId, request.block);
  const outbound = request.type === "store" ? travelToNode(stackId, "YardBuffer", request.block) : travelToNode(stackId, "Quay", request.block);
  const travelDistance = inbound.distance + outbound.distance;
  const predictedStart = Math.max(readyAt, truck.availableAt) + inbound.distance * 0.25;
  let score = predictedStart + travelDistance * 0.2;
  if (settings.dispatchRule === "nearest") {
    score = travelDistance * 0.8 + Math.max(0, truck.availableAt - readyAt);
  } else if (settings.dispatchRule === "queue_balance") {
    score = predictedStart + truck.availableAt * 0.15;
  }
  return { inbound, outbound, travelDistance, predictedStart, score };
}

function assignTruck(trucks, request, readyAt, stackId, settings) {
  const candidates = trucks.map((truck) => {
    const evaluation = scoreTruckCandidate(truck, request, readyAt, stackId, settings);
    return { truck, ...evaluation };
  });
  candidates.sort((a, b) => a.score - b.score);
  return candidates[0];
}

function updateTruck(truck, request, stackId, end, movement) {
  truck.availableAt = end;
  if (request.type === "retrieve") {
    truck.location = "Quay";
  } else {
    truck.location = stackId;
  }
  return {
    truckId: truck.id,
    truckDistance: movement.travelDistance,
    truckPath: `${movement.inbound.lane} -> ${movement.outbound.lane}`,
  };
}

function buildPlan(settings) {
  const stacks = cloneStacks(INITIAL_STACKS);
  const actions = [];
  const snapshots = [{ at: 0, stacks: cloneStacks(stacks) }];
  const requestSummaries = {};
  const cranes = {
    B1: { id: "YC1", availableAt: 0, stackId: "B1-Bay1-S1" },
    B2: { id: "YC2", availableAt: 0, stackId: "B2-Bay1-S1" },
  };
  const trucks = createTruckPool(settings);

  REQUESTS.forEach((request, requestIndex) => {
    const crane = cranes[request.block];
    const pendingRequests = REQUESTS.slice(requestIndex + 1);
    const requestBaseStart = Math.max(request.time, crane.availableAt);

    if (request.type === "retrieve") {
      const location = findContainer(stacks, request.containerId);
      if (!location) {
        return;
      }

      let fromStackId = location.stackId;
      let stack = stacks[fromStackId];
      const blockers = stack.slice(location.tierIndex + 1).reverse();
      let cursor = requestBaseStart;

      blockers.forEach((containerId) => {
        const target = chooseRelocationTarget(stacks, fromStackId, containerId, request, pendingRequests, settings);
        if (!target) {
          return;
        }
        const emptyTravel = stackDistance(crane.stackId, fromStackId);
        const loadedTravel = stackDistance(fromStackId, target.stackId);
        const duration = 1 + (emptyTravel + loadedTravel) * 0.5;
        const start = Math.max(cursor, crane.availableAt);
        const end = start + duration;
        const remaining = estimateRemainingRelocations(stacks, pendingRequests);

        actions.push({
          id: `${request.id}-relocate-${containerId}`,
          requestId: request.id,
          type: "relocate",
          craneId: crane.id,
          block: request.block,
          containerId,
          fromStackId,
          toStackId: target.stackId,
          start,
          end,
          emptyTravel,
          vehicleTravel: 0,
          currentAction: `将挡路箱 ${containerId} 从 ${fromStackId} 移到 ${target.stackId}`,
          nextPrediction: `释放目标箱 ${request.containerId} 的上层阻塞`,
          futureEstimate: remaining + target.futureBlocking,
        });

        moveContainer(stacks, fromStackId, target.stackId, containerId);
        snapshots.push({ at: end, stacks: cloneStacks(stacks) });
        pushRequestSummary(requestSummaries, request, actions[actions.length - 1]);
        cursor = end;
        crane.availableAt = end;
        crane.stackId = target.stackId;
        stack = stacks[fromStackId];
      });

      const emptyTravel = stackDistance(crane.stackId, fromStackId);
      const handlingReady = Math.max(cursor, crane.availableAt);
      const truckAssignment = assignTruck(trucks, request, handlingReady, fromStackId, settings);
      const craneStart = Math.max(handlingReady, truckAssignment.truck.availableAt);
      const craneDuration = 0.95 + (emptyTravel + 1.4) * 0.45;
      const handoffBuffer = truckAssignment.inbound.distance * 0.25;
      const vehicleBuffer = truckAssignment.outbound.distance * 0.2;
      const start = craneStart;
      const end = start + craneDuration + handoffBuffer + vehicleBuffer;
      const remaining = estimateRemainingRelocations(stacks, pendingRequests);
      const truckMeta = updateTruck(truckAssignment.truck, request, fromStackId, end, truckAssignment);

      actions.push({
        id: `${request.id}-retrieve`,
        requestId: request.id,
        type: "retrieve",
        craneId: crane.id,
        block: request.block,
        containerId: request.containerId,
        fromStackId,
        toStackId: `${request.block}-Quay`,
        start,
        end,
        emptyTravel,
        vehicleTravel: truckAssignment.travelDistance,
        ...truckMeta,
        currentAction: `提取目标箱 ${request.containerId} 并交给 ${truckMeta.truckId} 运往岸侧`,
        nextPrediction: pendingRequests[0]
          ? `下一请求 ${pendingRequests[0].id} 将在 ${pendingRequests[0].time.toFixed(1)} h 到达`
          : "当前请求队列已接近处理完成",
        futureEstimate: remaining,
      });

      stacks[fromStackId] = stacks[fromStackId].filter((item) => item !== request.containerId);
      snapshots.push({ at: end, stacks: cloneStacks(stacks) });
      pushRequestSummary(requestSummaries, request, actions[actions.length - 1]);
      crane.availableAt = end;
      crane.stackId = fromStackId;
    } else {
      const target = chooseStoreTarget(stacks, request, settings);
      if (!target) {
        return;
      }

      const handlingReady = Math.max(requestBaseStart, crane.availableAt);
      const truckAssignment = assignTruck(trucks, request, handlingReady, target.stackId, settings);
      const craneStart = Math.max(handlingReady, truckAssignment.truck.availableAt);
      const emptyTravel = stackDistance(crane.stackId, target.stackId);
      const craneDuration = 0.8 + (emptyTravel + 1.1) * 0.42;
      const handoffBuffer = truckAssignment.inbound.distance * 0.24;
      const vehicleBuffer = truckAssignment.outbound.distance * 0.18;
      const start = craneStart;
      const end = start + craneDuration + handoffBuffer + vehicleBuffer;
      const remaining = estimateRemainingRelocations(stacks, pendingRequests);
      const truckMeta = updateTruck(truckAssignment.truck, request, target.stackId, end, truckAssignment);

      actions.push({
        id: `${request.id}-store`,
        requestId: request.id,
        type: "store",
        craneId: crane.id,
        block: request.block,
        containerId: request.containerId,
        fromStackId: `${request.block}-Gate`,
        toStackId: target.stackId,
        start,
        end,
        emptyTravel,
        vehicleTravel: truckAssignment.travelDistance,
        ...truckMeta,
        currentAction: `新到箱 ${request.containerId} 由 ${truckMeta.truckId} 运至 ${target.stackId}`,
        nextPrediction: `当前策略估计未来仍需 ${Math.round(remaining + target.futureBlocking)} 次翻箱`,
        futureEstimate: remaining + target.futureBlocking,
      });

      stacks[target.stackId] = [...(stacks[target.stackId] || []), request.containerId];
      snapshots.push({ at: end, stacks: cloneStacks(stacks) });
      pushRequestSummary(requestSummaries, request, actions[actions.length - 1]);
      crane.availableAt = end;
      crane.stackId = target.stackId;
    }
  });

  const totalMoveTime = actions.reduce((sum, action) => sum + (action.end - action.start), 0);
  const emptyTravel = actions.reduce((sum, action) => sum + action.emptyTravel, 0);
  const vehicleTravel = actions.reduce((sum, action) => sum + (action.vehicleTravel || 0), 0);
  const relocations = actions.filter((action) => action.type === "relocate").length;
  const responses = Object.values(requestSummaries).map((summary) => summary.end - summary.request.time);
  const avgResponse = responses.length ? responses.reduce((sum, value) => sum + value, 0) / responses.length : 0;
  const truckWaiting = Object.values(requestSummaries).reduce(
    (sum, summary) => sum + Math.max(0, summary.start - summary.request.time),
    0
  );
  const makespan = actions.length ? actions[actions.length - 1].end : 0;
  const activeVehicleHours = actions.reduce((sum, action) => sum + (action.truckId ? action.end - action.start : 0), 0);
  const vehicleUtilization = settings.truckCount && makespan
    ? Math.min(0.98, activeVehicleHours / (settings.truckCount * makespan))
    : 0;

  return {
    actions,
    snapshots,
    requestSummaries: Object.values(requestSummaries),
    duration: Math.max(14, makespan + 1.5),
    metrics: {
      totalMoveTime,
      emptyTravel,
      vehicleTravel,
      relocations,
      avgResponse,
      truckWaiting,
      makespan,
      vehicleUtilization,
    },
  };
}

function stackToTiers(stack, maxTier) {
  return Array.from({ length: maxTier }, (_, index) => stack[index] || null);
}

function blockLabel(strategy) {
  if (strategy === "nearest_slot") {
    return "最近空位";
  }
  if (strategy === "batch_friendly") {
    return "批次友好";
  }
  return "最少未来阻塞";
}

function dispatchLabel(rule) {
  if (rule === "nearest") {
    return "最近车辆";
  }
  if (rule === "queue_balance") {
    return "队列均衡";
  }
  return "集成平衡";
}

export function useYardRelocationDemo() {
  const settings = reactive({
    strategy: "min_future_blocking",
    dispatchRule: "integrated",
    maxTier: 4,
    truckCount: 2,
  });

  const selectedStackId = ref("B1-Bay1-S1");
  const playing = ref(false);
  const playbackSpeed = ref(1);
  const simulationTime = ref(0);
  const runtime = reactive({ frameId: 0, lastTick: 0 });
  const plan = computed(() => buildPlan(settings));

  const currentActionIndex = computed(() =>
    plan.value.actions.findIndex(
      (action) => simulationTime.value % plan.value.duration >= action.start && simulationTime.value % plan.value.duration < action.end
    )
  );
  const currentAction = computed(() => (currentActionIndex.value === -1 ? null : plan.value.actions[currentActionIndex.value]));
  const nextAction = computed(() => {
    if (!plan.value.actions.length) {
      return null;
    }
    const index = currentActionIndex.value === -1 ? 0 : Math.min(currentActionIndex.value + 1, plan.value.actions.length - 1);
    return plan.value.actions[index];
  });

  const displayStacks = computed(() => {
    const clock = simulationTime.value % plan.value.duration;
    const snapshot = [...plan.value.snapshots].reverse().find((item) => item.at <= clock) || plan.value.snapshots[0];
    return snapshot.stacks;
  });

  const yardBlocks = computed(() =>
    BLOCKS.map((blockId) => ({
      id: blockId,
      bays: Array.from({ length: BAYS_PER_BLOCK }, (_, bayIndex) => ({
        id: `${blockId}-Bay${bayIndex + 1}`,
        label: `Bay ${bayIndex + 1}`,
        stacks: Array.from({ length: STACKS_PER_BAY }, (_, stackIndex) => {
          const stackId = `${blockId}-Bay${bayIndex + 1}-S${stackIndex + 1}`;
          const stack = displayStacks.value[stackId] || [];
          return {
            id: stackId,
            shortLabel: `S${stackIndex + 1}`,
            height: stack.length,
            tiers: stackToTiers(stack, settings.maxTier),
          };
        }),
      })),
    }))
  );

  const selectedStack = computed(() => {
    const stack = displayStacks.value[selectedStackId.value] || [];
    return {
      id: selectedStackId.value,
      tiers: stackToTiers(stack, settings.maxTier),
      height: stack.length,
    };
  });

  const activeRequestId = computed(() => currentAction.value?.requestId || REQUESTS[0].id);

  const requestQueue = computed(() =>
    REQUESTS.map((request) => {
      const summary = plan.value.requestSummaries.find((item) => item.id === request.id);
      let status = "pending";
      if (activeRequestId.value === request.id) {
        status = "active";
      } else if (summary && summary.end <= simulationTime.value % plan.value.duration) {
        status = "done";
      }
      return {
        ...request,
        status,
        response: summary ? summary.end - request.time : null,
      };
    })
  );

  const craneVisuals = computed(() =>
    BLOCKS.map((blockId) => {
      const action = currentAction.value && currentAction.value.block === blockId ? currentAction.value : null;
      let x = 10;
      let y = 8;
      if (action) {
        const targetStackId = action.toStackId.includes("Quay") ? action.fromStackId : action.toStackId;
        const parsed = parseStackId(targetStackId);
        x = (parsed.stack - 1) * 18 + 10;
        y = (parsed.bay - 1) * 58 + 8;
      }
      return {
        id: blockId,
        craneId: blockId === "B1" ? "YC1" : "YC2",
        x,
        y,
        active: Boolean(action),
      };
    })
  );

  const truckVisuals = computed(() => {
    const currentTruckId = currentAction.value?.truckId;
    const visuals = [];
    for (let index = 0; index < settings.truckCount; index += 1) {
      const truckId = `IT${index + 1}`;
      const isActive = truckId === currentTruckId;
      const block = currentAction.value?.block || (index % 2 === 0 ? "B1" : "B2");
      const lane = currentAction.value?.truckPath?.includes("Gate") ? "gate" : currentAction.value?.truckPath?.includes("Quay") ? "quay" : "yard";
      visuals.push({
        id: truckId,
        block,
        lane,
        active: isActive,
        progress: isActive ? ((simulationTime.value % plan.value.duration) - currentAction.value.start) / (currentAction.value.end - currentAction.value.start) : 0,
      });
    }
    return visuals;
  });

  const stageNarrative = computed(() => [
    {
      title: "这不只是翻箱",
      body: currentAction.value?.truckId
        ? `当前动作同时绑定堆位选择、场桥作业和车辆 ${currentAction.value.truckId} 派遣。`
        : "当前场景把堆位分配和车辆调度放在同一条流程里，而不是分开看。",
    },
    {
      title: "当前动作",
      body: currentAction.value?.currentAction || "每一步都在同时权衡当前搬运时间、车辆空驶和未来翻箱压力。",
    },
    {
      title: "未来代价估计",
      body: `在“${blockLabel(settings.strategy)} + ${dispatchLabel(settings.dispatchRule)}”下，剩余翻箱约 ${Math.round(
        currentAction.value?.futureEstimate ?? estimateRemainingRelocations(displayStacks.value, REQUESTS)
      )} 次。`,
    },
  ]);

  const insightCards = computed(() => [
    { label: "当前动作", value: currentAction.value?.currentAction || "等待下一条请求进入服务" },
    { label: "下一步预测", value: currentAction.value?.nextPrediction || nextAction.value?.currentAction || "队列中暂时无后续动作" },
    { label: "车辆协同", value: currentAction.value?.truckId ? `${currentAction.value.truckId} · ${currentAction.value.truckPath}` : `${settings.truckCount} 辆车待命` },
  ]);

  function containerTone(containerId) {
    if (!containerId) {
      return "rgba(20, 33, 61, 0.06)";
    }
    return BATCH_COLORS[getContainerMeta(containerId).departureBatch] || "#64748b";
  }

  function selectStack(stackId) {
    selectedStackId.value = stackId;
  }

  function resetPlayback() {
    simulationTime.value = 0;
  }

  function togglePlayback() {
    playing.value = !playing.value;
  }

  function stepOnce() {
    playing.value = false;
    const duration = plan.value.duration;
    if (!plan.value.actions.length) {
      return;
    }

    const epsilon = 0.001;
    const clock = simulationTime.value % duration;
    const action = currentAction.value || nextAction.value || plan.value.actions[0];

    if (!currentAction.value && action) {
      simulationTime.value = action.start;
      return;
    }

    const actionDuration = Math.max(action.end - action.start, 0.1);
    const checkpoints = [
      action.start,
      action.start + actionDuration * 0.25,
      action.start + actionDuration * 0.5,
      action.start + actionDuration * 0.75,
      action.end + epsilon,
    ];

    const nextCheckpoint = checkpoints.find((point) => point > clock + epsilon);
    if (nextCheckpoint !== undefined) {
      simulationTime.value = nextCheckpoint;
      return;
    }

    const next = plan.value.actions.find((item) => item.start > action.end + epsilon);
    simulationTime.value = next ? next.start : 0;
  }

  function tick(now) {
    if (!runtime.lastTick) {
      runtime.lastTick = now;
    }
    const delta = (now - runtime.lastTick) / 1000;
    runtime.lastTick = now;
    if (playing.value) {
      simulationTime.value += delta * playbackSpeed.value * 1.35;
    }
    runtime.frameId = window.requestAnimationFrame(tick);
  }

  watch([() => settings.strategy, () => settings.maxTier, () => settings.truckCount, () => settings.dispatchRule], () => {
    resetPlayback();
  });

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
    selectedStackId,
    selectedStack,
    requestQueue,
    stageNarrative,
    insightCards,
    yardBlocks,
    craneVisuals,
    truckVisuals,
    currentAction,
    nextAction,
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
  };
}
