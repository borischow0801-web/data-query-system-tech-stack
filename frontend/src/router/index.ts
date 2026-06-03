import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import { useAuthStore } from "@/store/auth";

const Login = () => import("@/views/Login.vue");
const MainLayout = () => import("@/layouts/MainLayout.vue");
const Dashboard = () => import("@/views/Dashboard.vue");
const InterfaceList = () => import("@/views/interface/InterfaceList.vue");
const ParamTemplate = () => import("@/views/interface/ParamTemplate.vue");
const QueryExecute = () => import("@/views/query/QueryExecute.vue");
const QueryHistory = () => import("@/views/query/QueryHistory.vue");

const routes: RouteRecordRaw[] = [
  { path: "/login", name: "login", component: Login },
  {
    path: "/",
    component: MainLayout,
    children: [
      { path: "", name: "dashboard", component: Dashboard },
      { path: "interfaces", name: "interfaces", component: InterfaceList },
      { path: "interfaces/:id/params", name: "interface-params", component: ParamTemplate, props: true },
      { path: "query/execute", name: "query-execute", component: QueryExecute },
      { path: "query/history", name: "query-history", component: QueryHistory }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore();
  if (to.name !== "login" && !auth.isAuthenticated) {
    next({ name: "login" });
  } else if (to.name === "login" && auth.isAuthenticated) {
    next({ name: "dashboard" });
  } else {
    next();
  }
});

export default router;

