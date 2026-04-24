<template>
  <div class="page-container space-y-6 pb-8">
    <section class="page-shell hero-grid rounded-[2rem] px-6 py-8 sm:px-8 sm:py-10 xl:grid xl:grid-cols-[1.2fr_0.95fr] xl:gap-8">
      <div class="relative z-10 flex flex-col justify-center">
        <span class="section-kicker">Tailwind UI Refresh</span>
        <h1 class="mt-5 max-w-3xl text-4xl font-black leading-tight tracking-tight text-slate-950 sm:text-5xl">
          让邮箱管理页
          <span class="bg-gradient-to-r from-teal-700 via-cyan-700 to-emerald-600 bg-clip-text text-transparent">
            更清晰、更高级、更有秩序
          </span>
        </h1>
        <p class="mt-5 max-w-2xl text-base leading-8 text-slate-600 sm:text-lg">
          花火邮箱助手将多账号管理、批量收信和实时状态聚合到一个更轻盈的工作台里，让操作更顺手，信息层级也更容易扫一眼就看懂。
        </p>

        <div class="mt-8 flex flex-col gap-3 sm:flex-row">
          <el-button
            type="primary"
            size="large"
            class="!h-12 !rounded-full !border-0 !bg-slate-950 !px-7 !text-[15px] !font-semibold !shadow-[0_22px_40px_-24px_rgba(15,23,42,0.8)]"
            @click="navigateToEmails"
          >
            立即进入工作台
          </el-button>
          <el-button
            size="large"
            class="!ml-0 !h-12 !rounded-full !border-slate-300 !bg-white/85 !px-7 !text-[15px] !font-semibold !text-slate-700 sm:!ml-3"
            @click="scrollToFeatures"
          >
            查看核心能力
          </el-button>
        </div>

        <div class="mt-8 grid gap-3 sm:grid-cols-3">
          <div
            v-for="stat in stats"
            :key="stat.description"
            class="rounded-3xl border border-white/70 bg-white/70 px-5 py-4 shadow-[0_24px_60px_-34px_rgba(15,23,42,0.35)] backdrop-blur"
          >
            <div class="text-3xl font-black text-slate-950">{{ stat.value }}</div>
            <div class="mt-1 text-sm text-slate-500">{{ stat.description }}</div>
          </div>
        </div>
      </div>

      <div class="relative mt-8 xl:mt-0">
        <div class="absolute -left-4 top-12 h-28 w-28 rounded-full bg-cyan-300/40 blur-2xl"></div>
        <div class="absolute bottom-10 right-0 h-32 w-32 rounded-full bg-emerald-300/35 blur-2xl"></div>

        <div class="relative overflow-hidden rounded-[2rem] border border-white/75 bg-slate-950 px-5 py-5 text-white shadow-[0_34px_100px_-38px_rgba(15,23,42,0.7)]">
          <div class="flex items-center justify-between rounded-3xl border border-white/10 bg-white/5 px-4 py-3">
            <div>
              <p class="text-xs uppercase tracking-[0.28em] text-cyan-200/70">Live Monitor</p>
              <h2 class="mt-1 text-lg font-semibold">邮箱总览面板</h2>
            </div>
            <div class="flex items-center gap-2 rounded-full bg-emerald-400/15 px-3 py-1 text-sm text-emerald-200">
              <span class="h-2.5 w-2.5 rounded-full bg-emerald-300"></span>
              实时在线
            </div>
          </div>

          <div class="mt-5 grid gap-4 sm:grid-cols-2">
            <div class="rounded-3xl border border-white/10 bg-white/6 p-5">
              <p class="text-sm text-slate-300">批量操作效率</p>
              <div class="mt-4 flex items-end justify-between">
                <div class="text-4xl font-black">93%</div>
                <div class="text-xs uppercase tracking-[0.22em] text-emerald-200">Optimized</div>
              </div>
              <div class="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
                <div class="progress-glow h-full w-[93%] rounded-full bg-gradient-to-r from-cyan-300 via-teal-300 to-emerald-300"></div>
              </div>
            </div>

            <div class="rounded-3xl border border-white/10 bg-gradient-to-br from-cyan-400/16 to-emerald-400/10 p-5">
              <p class="text-sm text-slate-300">多账户并行</p>
              <div class="mt-3 flex items-center gap-3">
                <div class="flex -space-x-3">
                  <span class="grid h-10 w-10 place-items-center rounded-full border border-slate-900/40 bg-cyan-200 text-slate-950 font-bold">A</span>
                  <span class="grid h-10 w-10 place-items-center rounded-full border border-slate-900/40 bg-emerald-200 text-slate-950 font-bold">B</span>
                  <span class="grid h-10 w-10 place-items-center rounded-full border border-slate-900/40 bg-sky-200 text-slate-950 font-bold">C</span>
                </div>
                <div class="text-sm leading-6 text-slate-200">统一查看状态、配置与邮件流转，不用在多个页面来回切换。</div>
              </div>
            </div>
          </div>

          <div class="mt-5 space-y-3">
            <div
              v-for="item in dashboardHighlights"
              :key="item.title"
              class="flex items-start gap-4 rounded-3xl border border-white/10 bg-white/6 px-4 py-4"
            >
              <div class="grid h-11 w-11 place-items-center rounded-2xl bg-white/10 text-cyan-200">
                <el-icon size="20"><component :is="item.icon" /></el-icon>
              </div>
              <div>
                <div class="font-semibold text-white">{{ item.title }}</div>
                <div class="mt-1 text-sm leading-6 text-slate-300">{{ item.description }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section ref="featuresSection" class="space-y-5">
      <div class="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <span class="section-kicker">Feature System</span>
          <h2 class="mt-4 text-3xl font-black tracking-tight text-slate-950">把复杂邮箱流程拆成更易读的模块</h2>
        </div>
        <p class="max-w-xl text-sm leading-7 text-slate-500 sm:text-right">
          用更统一的卡片、标签和数据层级组织关键操作，让用户不需要思考太久就能找到入口。
        </p>
      </div>

      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="feature in features"
          :key="feature.title"
          class="page-shell rounded-[1.75rem] p-6 transition duration-300 hover:-translate-y-1 hover:shadow-[0_30px_70px_-34px_rgba(15,23,42,0.38)]"
        >
          <div :class="feature.iconClass" class="flex h-14 w-14 items-center justify-center rounded-2xl text-white shadow-lg shadow-slate-900/10">
            <el-icon size="24"><component :is="feature.icon" /></el-icon>
          </div>
          <h3 class="mt-5 text-xl font-bold text-slate-900">{{ feature.title }}</h3>
          <p class="mt-3 text-sm leading-7 text-slate-600">{{ feature.description }}</p>
          <div class="mt-6 h-px w-full bg-gradient-to-r from-slate-200 to-transparent"></div>
          <p class="mt-4 text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">{{ feature.caption }}</p>
        </article>
      </div>
    </section>

    <section class="grid gap-4 xl:grid-cols-[0.95fr_1.15fr]">
      <div class="page-shell rounded-[1.75rem] p-6 sm:p-7">
        <span class="section-kicker">Quick Start</span>
        <h2 class="mt-4 text-3xl font-black tracking-tight text-slate-950">上手流程更像一条连续工作流</h2>
        <p class="mt-4 max-w-lg text-sm leading-7 text-slate-600">
          从添加账号到查看邮件，我们把每一步整理成清晰的节奏，避免页面看起来像很多功能拼在一起。
        </p>

        <div class="mt-8 space-y-4">
          <div
            v-for="(step, index) in steps"
            :key="step.title"
            class="flex items-start gap-4 rounded-[1.4rem] border border-white/70 bg-white/72 px-4 py-4 shadow-[0_24px_60px_-38px_rgba(15,23,42,0.3)]"
          >
            <div class="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-slate-950 text-sm font-black text-white">
              {{ index + 1 }}
            </div>
            <div>
              <h3 class="text-base font-bold text-slate-900">{{ step.title }}</h3>
              <p class="mt-1 text-sm leading-7 text-slate-600">{{ step.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="page-shell relative overflow-hidden rounded-[1.75rem] p-6 sm:p-7">
        <div class="absolute right-0 top-0 h-36 w-36 rounded-full bg-cyan-300/25 blur-3xl"></div>
        <div class="absolute bottom-0 left-10 h-32 w-32 rounded-full bg-emerald-300/20 blur-3xl"></div>

        <div class="relative">
          <span class="section-kicker">Why It Feels Better</span>
          <h2 class="mt-4 text-3xl font-black tracking-tight text-slate-950">新的首页更像产品入口，而不是功能列表</h2>

          <div class="mt-8 grid gap-4 sm:grid-cols-2">
            <div class="rounded-[1.5rem] bg-slate-950 p-5 text-white">
              <p class="text-sm uppercase tracking-[0.2em] text-cyan-200/80">视觉结构</p>
              <p class="mt-3 text-sm leading-7 text-slate-300">
                通过深浅对比、卡片堆叠和更强的留白，把重要入口、统计信息和功能说明明确区分开。
              </p>
            </div>
            <div class="rounded-[1.5rem] border border-slate-200 bg-white/78 p-5">
              <p class="text-sm uppercase tracking-[0.2em] text-slate-500">交互体验</p>
              <p class="mt-3 text-sm leading-7 text-slate-600">
                CTA、概览卡片与功能卡都统一成更圆润、更轻盈的语言，整体会比原来更有产品感。
              </p>
            </div>
          </div>

          <div class="mt-6 rounded-[1.5rem] border border-white/70 bg-white/75 p-5 shadow-[0_30px_70px_-40px_rgba(15,23,42,0.34)]">
            <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 class="text-2xl font-black tracking-tight text-slate-950">现在就进入邮箱管理页</h3>
                <p class="mt-2 text-sm leading-7 text-slate-600">新的布局已经把视觉基调铺好，后续继续扩展页面也更容易统一风格。</p>
              </div>
              <el-button
                type="primary"
                size="large"
                class="!h-12 !rounded-full !border-0 !bg-gradient-to-r !from-teal-700 !to-cyan-700 !px-7 !text-[15px] !font-semibold"
                @click="navigateToEmails"
              >
                打开邮箱工作台
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Briefcase,
  Connection,
  Cpu,
  Document,
  Management,
  Search
} from '@element-plus/icons-vue'

const router = useRouter()
const featuresSection = ref(null)

const features = [
  {
    icon: Briefcase,
    title: '邮箱管理',
    description: '集中维护多个邮箱账号，统一展示账号信息、状态与配置，让后台操作更容易梳理。',
    caption: 'Account Center',
    iconClass: 'bg-gradient-to-br from-slate-900 to-slate-700'
  },
  {
    icon: Management,
    title: '批量操作',
    description: '支持多选、批量删除、批量收信等高频动作，减少重复点按，让管理效率明显提升。',
    caption: 'Batch Actions',
    iconClass: 'bg-gradient-to-br from-teal-700 to-cyan-600'
  },
  {
    icon: Connection,
    title: '实时反馈',
    description: '通过 WebSocket 接收进度与结果通知，关键状态一目了然，不需要反复手动刷新。',
    caption: 'Live Status',
    iconClass: 'bg-gradient-to-br from-sky-700 to-cyan-500'
  },
  {
    icon: Cpu,
    title: '并行处理',
    description: '将多账号收信与处理流程并行化，减少等待时间，在任务量较大时也能保持流畅。',
    caption: 'Parallel Flow',
    iconClass: 'bg-gradient-to-br from-emerald-700 to-teal-500'
  },
  {
    icon: Search,
    title: '快速搜索',
    description: '对主题、正文和发件信息做统一检索，帮助用户快速定位重要邮件与历史记录。',
    caption: 'Find Faster',
    iconClass: 'bg-gradient-to-br from-orange-500 to-amber-500'
  },
  {
    icon: Document,
    title: '内容浏览',
    description: '用更清晰的内容视图查看 HTML、附件与邮件结构，让长邮件和复杂内容也更易读。',
    caption: 'Readable Content',
    iconClass: 'bg-gradient-to-br from-violet-600 to-fuchsia-600'
  }
]

const stats = [
  { value: '100+', description: '并行邮箱处理能力' },
  { value: '10x', description: '更快的批量收信节奏' },
  { value: '24/7', description: '实时状态通知反馈' }
]

const steps = [
  {
    title: '添加邮箱账号',
    description: '先把需要管理的邮箱导入系统，支持单个添加，也可以批量导入。'
  },
  {
    title: '整理与筛选账户',
    description: '在统一列表中查看账号类型、配置与状态，并快速选中需要操作的账户。'
  },
  {
    title: '执行批量收信',
    description: '通过批量操作入口统一发起任务，并在页面内实时查看处理中的进度反馈。'
  },
  {
    title: '查看邮件内容',
    description: '进入详情后可继续浏览正文、附件与结构化内容，定位信息会更轻松。'
  }
]

const dashboardHighlights = [
  {
    icon: Connection,
    title: '状态反馈更直接',
    description: '连接状态、批量执行和页面入口被放进同一视觉系统里，减少信息散乱感。'
  },
  {
    icon: Search,
    title: '查找路径更顺滑',
    description: '用户可以从首页直接理解后续能做什么，而不是先面对一大块密集按钮。'
  }
]

const navigateToEmails = () => {
  router.push('/emails')
}

const scrollToFeatures = () => {
  featuresSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<style scoped>
.hero-grid {
  position: relative;
  overflow: hidden;
}

.hero-grid::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at top left, rgba(34, 211, 238, 0.16), transparent 28%),
    radial-gradient(circle at bottom right, rgba(16, 185, 129, 0.14), transparent 30%);
  pointer-events: none;
}

.progress-glow {
  box-shadow: 0 0 24px rgba(103, 232, 249, 0.4);
}
</style>
