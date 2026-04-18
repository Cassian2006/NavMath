<template>
  <section class="gc-wrap">
    <header class="gc-header">
      <p class="gc-eyebrow">Scenario 05</p>
      <h2>大圆航线 vs 恒向线</h2>
      <p class="gc-sub">
        用真实港口坐标说明球面几何在航运中的作用：地图上“看起来更直”的路线，不一定更短。
      </p>
    </header>

    <div class="gc-inputs">
      <div class="port-group">
        <label>出发港</label>
        <select v-model="fromKey" @change="onPortChange">
          <option v-for="(port, key) in PORTS" :key="key" :value="key">{{ port.name }}</option>
          <option value="custom_from">自定义坐标</option>
        </select>
        <div v-if="fromKey === 'custom_from'" class="custom-coord">
          <input v-model.number="customFrom.lat" placeholder="纬度 (°N)" type="number" step="0.1" />
          <input v-model.number="customFrom.lng" placeholder="经度 (°E)" type="number" step="0.1" />
        </div>
      </div>

      <div class="arrow">→</div>

      <div class="port-group">
        <label>目的港</label>
        <select v-model="toKey" @change="onPortChange">
          <option v-for="(port, key) in PORTS" :key="key" :value="key">{{ port.name }}</option>
          <option value="custom_to">自定义坐标</option>
        </select>
        <div v-if="toKey === 'custom_to'" class="custom-coord">
          <input v-model.number="customTo.lat" placeholder="纬度 (°N)" type="number" step="0.1" />
          <input v-model.number="customTo.lng" placeholder="经度 (°E)" type="number" step="0.1" />
        </div>
      </div>

      <button class="calc-btn" @click="calculate">计算航线</button>
    </div>

    <div v-if="result" class="gc-stats">
      <article class="stat-card blue">
        <span class="stat-label">大圆航线</span>
        <strong class="stat-value">{{ result.gcDist.toFixed(0) }} <span>海里</span></strong>
      </article>
      <article class="stat-card orange">
        <span class="stat-label">恒向线</span>
        <strong class="stat-value">{{ result.rlDist.toFixed(0) }} <span>海里</span></strong>
      </article>
      <article class="stat-card green">
        <span class="stat-label">节省距离</span>
        <strong class="stat-value">{{ (result.rlDist - result.gcDist).toFixed(0) }} <span>海里</span></strong>
      </article>
      <article class="stat-card purple">
        <span class="stat-label">估算节省燃油</span>
        <strong class="stat-value">{{ result.fuelSaved.toFixed(1) }} <span>吨</span></strong>
      </article>
    </div>

    <div ref="globeContainer" class="globe-container"></div>

    <div v-if="result" class="math-panel">
      <section class="formula-block">
        <p class="formula-title">Haversine 公式</p>
        <pre class="formula-code">d = 2R · arcsin( √( sin²((φ₂ - φ₁)/2) + cosφ₁ · cosφ₂ · sin²((λ₂ - λ₁)/2) ) )</pre>
        <p class="formula-text">
          其中 φ 表示纬度，λ 表示经度，R 取地球平均半径。当前从
          {{ fromName }} 到 {{ toName }} 的大圆距离约为
          <strong>{{ result.gcDist.toFixed(1) }} 海里</strong>。
        </p>
      </section>

      <section class="insight-block">
        <h3>核心洞察</h3>
        <p>
          地球是球面，不是平面。大圆航线对应球面上的最短路径，而恒向线只是在投影地图上更容易保持固定航向。
        </p>
        <p>
          当前这组港口组合中，若选择大圆航线，相比恒向线可少走
          <strong>{{ (result.rlDist - result.gcDist).toFixed(0) }} 海里</strong>，
          按每百海里约 2.5 吨燃油估算，可节省
          <strong>{{ result.fuelSaved.toFixed(1) }} 吨</strong>燃油。
        </p>
      </section>

      <section class="matlab-block">
        <p class="matlab-title">MATLAB 代码</p>
        <pre class="matlab-code">{{ result.matlabCode }}</pre>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from "vue";

const PORTS = {
  shanghai: { name: "上海港", lat: 31.23, lng: 121.47 },
  singapore: { name: "新加坡港", lat: 1.26, lng: 103.82 },
  rotterdam: { name: "鹿特丹港", lat: 51.95, lng: 4.14 },
  losangeles: { name: "洛杉矶港", lat: 33.73, lng: -118.27 },
  dubai: { name: "迪拜港", lat: 25.07, lng: 55.14 },
  hamburg: { name: "汉堡港", lat: 53.55, lng: 9.99 },
  newyork: { name: "纽约港", lat: 40.68, lng: -74.04 },
  busan: { name: "釜山港", lat: 35.1, lng: 129.04 },
  hongkong: { name: "香港港", lat: 22.31, lng: 114.17 },
  yokohama: { name: "横滨港", lat: 35.44, lng: 139.64 },
  dalian: { name: "大连港", lat: 38.93, lng: 121.65 },
};

const fromKey = ref("shanghai");
const toKey = ref("rotterdam");
const customFrom = ref({ lat: 0, lng: 0 });
const customTo = ref({ lat: 0, lng: 0 });
const result = ref(null);
const globeContainer = ref(null);
let globeInstance = null;

const fromCoord = computed(() => (fromKey.value === "custom_from" ? customFrom.value : PORTS[fromKey.value] || PORTS.shanghai));
const toCoord = computed(() => (toKey.value === "custom_to" ? customTo.value : PORTS[toKey.value] || PORTS.rotterdam));
const fromName = computed(() => (PORTS[fromKey.value]?.name ? PORTS[fromKey.value].name : "出发港"));
const toName = computed(() => (PORTS[toKey.value]?.name ? PORTS[toKey.value].name : "目的港"));

function toRad(degrees) {
  return (degrees * Math.PI) / 180;
}

function haversine(lat1, lng1, lat2, lng2) {
  const R = 3440.065;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

function rhumbDistance(lat1, lng1, lat2, lng2) {
  const R = 3440.065;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(Math.abs(lng2 - lng1));
  const dPsi = Math.log(
    Math.tan(toRad(lat2) / 2 + Math.PI / 4) /
      Math.tan(toRad(lat1) / 2 + Math.PI / 4)
  );
  const q = Math.abs(dPsi) > 1e-10 ? dLat / dPsi : Math.cos(toRad(lat1));
  return Math.sqrt(dLat * dLat + q * q * dLng * dLng) * R;
}

function buildMatlabCode(lat1, lng1, lat2, lng2) {
  return [
    "% Great-circle distance with Haversine formula",
    `phi1 = ${lat1} * pi/180;`,
    `lam1 = ${lng1} * pi/180;`,
    `phi2 = ${lat2} * pi/180;`,
    `lam2 = ${lng2} * pi/180;`,
    "dphi = phi2 - phi1;",
    "dlam = lam2 - lam1;",
    "a = sin(dphi/2)^2 + cos(phi1)*cos(phi2)*sin(dlam/2)^2;",
    "R_nm = 3440.065;",
    "d_gc = 2 * R_nm * asin(sqrt(a));",
    "fprintf('Great-circle distance: %.1f nautical miles\\n', d_gc);",
  ].join("\n");
}

async function renderGlobe() {
  if (!globeContainer.value || !result.value) {
    return;
  }

  if (globeInstance) {
    globeContainer.value.innerHTML = "";
    globeInstance = null;
  }

  const Globe = (await import("globe.gl")).default;
  const { lat: lat1, lng: lng1 } = fromCoord.value;
  const { lat: lat2, lng: lng2 } = toCoord.value;
  const midLat = (lat1 + lat2) / 2;
  const midLng = (lng1 + lng2) / 2;

  globeInstance = Globe()(globeContainer.value)
    .width(globeContainer.value.clientWidth || 900)
    .height(500)
    .backgroundColor("#07111f")
    .globeImageUrl("https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg")
    .pointsData([
      { lat: lat1, lng: lng1, name: fromName.value, color: "#38bdf8" },
      { lat: lat2, lng: lng2, name: toName.value, color: "#fb923c" },
    ])
    .pointColor("color")
    .pointAltitude(0.03)
    .pointRadius(0.5)
    .pointLabel("name")
    .arcsData([
      {
        startLat: lat1,
        startLng: lng1,
        endLat: lat2,
        endLng: lng2,
        color: ["#38bdf8", "#38bdf8"],
        label: "Great-circle route",
        dashLength: 0.85,
        dashGap: 0.12,
      },
      {
        startLat: lat1,
        startLng: lng1,
        endLat: lat2,
        endLng: lng2,
        color: ["#fb923c", "#fb923c"],
        label: "Rhumb line",
        dashLength: 0.35,
        dashGap: 0.22,
        arcAltitude: 0,
      },
    ])
    .arcColor("color")
    .arcAltitude((arc) => (arc.arcAltitude !== undefined ? arc.arcAltitude : 0.28))
    .arcStroke(1.8)
    .arcDashLength("dashLength")
    .arcDashGap("dashGap")
    .arcDashAnimateTime(2800);

  globeInstance.pointOfView({ lat: midLat, lng: midLng, altitude: 2.2 }, 900);
}

async function calculate() {
  const { lat: lat1, lng: lng1 } = fromCoord.value;
  const { lat: lat2, lng: lng2 } = toCoord.value;
  const gcDist = haversine(lat1, lng1, lat2, lng2);
  const rlDist = rhumbDistance(lat1, lng1, lat2, lng2);

  result.value = {
    gcDist,
    rlDist,
    fuelSaved: ((rlDist - gcDist) * 2.5) / 100,
    matlabCode: buildMatlabCode(lat1, lng1, lat2, lng2),
  };

  await nextTick();
  await renderGlobe();
}

function onPortChange() {
  result.value = null;
}

onMounted(() => {
  calculate();
});

onUnmounted(() => {
  if (globeInstance && globeContainer.value) {
    globeContainer.value.innerHTML = "";
    globeInstance = null;
  }
});
</script>

<style scoped>
.gc-wrap {
  max-width: 1120px;
  margin: 0 auto;
  padding: 24px 18px 48px;
}

.gc-header {
  text-align: center;
  margin-bottom: 22px;
}

.gc-eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #7dd3fc;
}

.gc-header h2 {
  margin: 0 0 8px;
  font-size: 30px;
  color: #e2e8f0;
}

.gc-sub {
  max-width: 760px;
  margin: 0 auto;
  color: #94a3b8;
  line-height: 1.7;
}

.gc-inputs {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  flex-wrap: wrap;
  padding: 18px;
  margin-bottom: 20px;
  border-radius: 16px;
  background: #101a2b;
  border: 1px solid #1e293b;
}

.port-group {
  display: flex;
  flex: 1;
  min-width: 180px;
  flex-direction: column;
  gap: 8px;
}

.port-group label {
  font-size: 12px;
  color: #94a3b8;
}

.port-group select,
.port-group input {
  width: 100%;
  padding: 10px 12px;
  color: #e2e8f0;
  background: #07111f;
  border: 1px solid #334155;
  border-radius: 10px;
}

.custom-coord {
  display: flex;
  gap: 8px;
}

.arrow {
  align-self: center;
  padding-bottom: 6px;
  font-size: 22px;
  color: #64748b;
}

.calc-btn {
  align-self: flex-end;
  padding: 10px 18px;
  color: #fff;
  cursor: pointer;
  background: #2563eb;
  border: none;
  border-radius: 10px;
  font-weight: 600;
}

.calc-btn:hover {
  background: #1d4ed8;
}

.gc-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.stat-card {
  padding: 14px 16px;
  border-radius: 14px;
  background: #101a2b;
  border-left: 4px solid;
}

.stat-card.blue {
  border-color: #38bdf8;
}

.stat-card.orange {
  border-color: #fb923c;
}

.stat-card.green {
  border-color: #22c55e;
}

.stat-card.purple {
  border-color: #a78bfa;
}

.stat-label {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  color: #94a3b8;
}

.stat-value {
  font-size: 24px;
  color: #f8fafc;
}

.stat-value span {
  font-size: 13px;
  color: #94a3b8;
}

.globe-container {
  width: 100%;
  height: 500px;
  overflow: hidden;
  margin-bottom: 20px;
  border-radius: 18px;
  background: #07111f;
  border: 1px solid #1e293b;
}

.math-panel {
  display: grid;
  gap: 16px;
  padding: 20px;
  border-radius: 16px;
  background: #101a2b;
  border: 1px solid #1e293b;
}

.formula-title,
.matlab-title,
.insight-block h3 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #7dd3fc;
}

.formula-code,
.matlab-code {
  padding: 14px;
  overflow-x: auto;
  border-radius: 12px;
  background: #07111f;
  color: #bfdbfe;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  font-family: Consolas, "Courier New", monospace;
}

.formula-text,
.insight-block p {
  margin: 0;
  color: #cbd5e1;
  line-height: 1.75;
}

@media (max-width: 900px) {
  .gc-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .gc-wrap {
    padding: 18px 12px 36px;
  }

  .gc-stats {
    grid-template-columns: 1fr;
  }
}
</style>
