<script setup>
defineProps({
  currentPage: {
    type: String,
    required: true,
  },
});

const navItems = [
  { key: "home", label: "首页", href: "/" },
  { key: "demo", label: "场景演示", href: "/demo" },
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
