import { createApp } from "vue";
import App from "./App.vue";
import DemoPage from "./DemoPage.vue";
import "./styles.css";

const path = window.location.pathname.replace(/\/+$/, "") || "/";
const RootComponent = path === "/demo" ? DemoPage : App;

createApp(RootComponent).mount("#app");
