<script setup>
defineProps({
  currentPage: {
    type: String,
    required: true,
  },
});

const navItems = [
  { key: "home", label: "主页面", href: "/" },
  { key: "demo", label: "页面占位", href: "/demo" },
];
</script>

<template>
  <header class="top-nav">
    <a class="brand-link" href="/">
      <span class="brand-mark">NV</span>
      <span class="brand-text">
        <strong>智绘数航</strong>
        <small>NavMath Vision</small>
      </span>
    </a>

    <nav class="nav-switch">
      <a
        v-for="item in navItems"
        :key="item.key"
        :href="item.href"
        class="nav-pill"
        :class="{ active: currentPage === item.key }"
      >
        {{ item.label }}
      </a>
    </nav>
  </header>
</template>
