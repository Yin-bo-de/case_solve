# 前端移动端响应式改造计划

## Context

当前 `frontend/` 是为桌面端设计的 React + Vite + TypeScript 单页应用，使用纯 CSS（无 UI 库 / Tailwind / CSS-in-JS），主样式 `src/index.css` 共 3283 行，但仅有 2 个媒体查询断点（1024px 和 560px），**手机端（< 768px）几乎零适配**。

主要问题：
- 大量固定像素：侧边栏 280–380px、Modal 380–520px、header `max-width: 1400px`
- 三栏布局（推理板、审讯页）在手机上不可用
- WatsonChatDialog 用 `useDrag` 自定义拖拽 + `position: fixed` + `width: 360px`，移动端遮挡严重
- 输入框无 `font-size: 16px`，Safari 会触发自动缩放
- 大量 hover 交互无移动端替代
- InterrogationPage.tsx 高达 2365 行，含大量内联 `<style>{...}` styled-jsx，重构风险高

目标：让玩家能在 iPhone（≥ 375px）、iPad（≥ 768px）上完整体验全部 8 个页面，桌面端体验保持不变。

---

## 决策摘要（已与用户确认）

| 维度 | 选择 |
|---|---|
| 改造范围 | 全量 8 个页面 + Watson 浮窗 + 全部 Modal |
| 三栏布局移动端形态 | **Tab 切换 + 底部抽屉** |
| iPad（768–1024px）布局 | **双栏精简版**（侧栏收窄至 240px，辅助面板抽屉化） |
| WatsonChatDialog | **底部抽屉 + 圆形 FAB**（移动端禁用拖拽） |
| 技术方案 | 纯 CSS @media + 新增 `useMediaQuery` hook + 新增 `MobileDrawer` 组件 |
| 断点 | `--bp-mobile: 768px` / `--bp-tablet: 1024px` |
| InterrogationPage 内联 styled-jsx | **原地追加 @media 块**，不迁出（降低风险） |

---

## 改造分层

### P0 全局基础（约 0.5 天）

**关键文件**：
- `frontend/src/index.css`（顶部新增变量节）
- `frontend/index.html`（已正确，无需改）

**改动要点**：

1. **新增 CSS 变量**（写入 `index.css` 第 1–30 行附近）：
   ```css
   :root {
     --bp-mobile: 768px;
     --bp-tablet: 1024px;
     --safe-top: env(safe-area-inset-top);
     --safe-bottom: env(safe-area-inset-bottom);
     --safe-left: env(safe-area-inset-left);
     --safe-right: env(safe-area-inset-right);
     --z-modal: 1000;
     --z-drawer: 900;
     --z-fab: 800;
     --z-watson: 850;
   }
   ```

2. **全局基线**：
   - `body { overflow-x: hidden; -webkit-tap-highlight-color: transparent; -webkit-text-size-adjust: 100%; }`
   - `input, textarea, select { font-size: 16px; }` 防 Safari 缩放
   - 触摸目标基线：`button, .clue-item, .actor-tab { min-height: 44px; }`
   - `@media (hover: none) { *:hover { /* 移除关键 hover 增强 */ } }`

3. **容器宽度**：
   - `.app-shell-content`、`.header-content`（约 505/539 行）等 `max-width: 1400px` 改为 `max-width: min(1400px, 100%); padding-inline: clamp(12px, 2vw, 24px);`

4. **Modal 通用全屏规则**（新增节）：
   ```css
   @media (max-width: 768px) {
     .modal, .clue-selector-modal, .clue-preview-modal, .accusation-modal, .extraction-modal {
       width: 100vw; max-width: 100vw;
       height: 100dvh; max-height: 100dvh;
       border-radius: 0; inset: 0; margin: 0;
     }
     .modal-footer {
       position: sticky; bottom: 0;
       padding-bottom: max(12px, env(safe-area-inset-bottom));
     }
   }
   ```

**风险**：`100dvh` 在旧 Safari 不支持，需双声明 `height: 100vh; height: 100dvh;`。

---

### P1 新增基础工具（约 0.5 天）

**新增文件**：

1. **`frontend/src/hooks/useMediaQuery.ts`**
   - 接收 query 字符串，返回 `boolean`
   - 内部用 `window.matchMedia` + `addEventListener('change')`
   - SSR 安全：`typeof window === 'undefined'` 时返回 `false`
   - 配套导出常量 `useIsMobile = () => useMediaQuery('(max-width: 768px)')`、`useIsTablet`

2. **`frontend/src/components/MobileDrawer.tsx`**
   - props：`open`, `onClose`, `position?: 'bottom' | 'right'`, `height?: string`, `children`
   - 底部抽屉默认 `height: 70dvh`，含 backdrop（点击关闭）+ 顶部拖把手
   - 简单实现：CSS transform translateY 动画，无需引入 framer-motion
   - 点击 backdrop / ESC / 下滑超过阈值关闭

3. **`frontend/src/hooks/useDrag.ts`**（修改现有）
   - 增加 `enabled?: boolean` 参数；`enabled === false` 时不注册任何监听器
   - 用于 WatsonChatDialog 在移动端禁用拖拽

---

### P2 关键页面布局重构（约 2.5 天）

#### P2.1 DeductionBoard（推理板）

**关键文件**：
- `frontend/src/pages/DeductionBoard.tsx`
- `frontend/src/index.css` 第 1407–1903、2679–2920 行（推理板样式）

**布局变化**：
- 桌面（> 1024px）：保持现状（左 300px 线索栏 + 右网格）
- 平板（768–1024px）：左栏 240px + 右网格，提示/统计区折叠
- 手机（< 768px）：单栏；header 增加「线索 / 推理」Tab 切换；线索栏改为底部 `MobileDrawer` 弹出；FAB 抬高避开安全区

**改动**：
- TSX：`useIsMobile()` 控制是否渲染 Tab + Drawer 包裹
- CSS：
  ```css
  @media (max-width: 1024px) {
    .deduction-board__content { grid-template-columns: 240px 1fr; }
  }
  @media (max-width: 768px) {
    .deduction-board__content { grid-template-columns: 1fr; }
    .deduction-board__sidebar { display: none; } /* 由 Drawer 接管 */
    .deduction-board__accuse-fab {
      bottom: calc(16px + env(safe-area-inset-bottom));
      right: 16px;
    }
  }
  ```

#### P2.2 InterrogationPage（审讯页）

**关键文件**：
- `frontend/src/pages/InterrogationPage.tsx` 第 1368 行起的内联 `<style>{...}` 块
- 配套：mention 菜单组件、tips panel 组件

**布局变化**：
- 桌面（> 1024px）：保持三栏（角色 280px / 聊天 / 提示）
- 平板（768–1024px）：双栏（角色 240px / 聊天），提示面板由 FAB 触发抽屉
- 手机（< 768px）：
  - 顶部横向滚动的「角色 Tab」固定为 sticky
  - 中间为占满屏幕的聊天区
  - 提示面板（WatsonTipsPanel）由顶部按钮触发底部抽屉
  - mention 菜单从「跟随光标 absolute」切换为「fixed 居底全宽」

**改动**：
- 在内联 `<style>` 末尾追加：
  ```css
  @media (max-width: 1024px) {
    .interrogation-layout { grid-template-columns: 1fr !important; }
    .actors-panel {
      width: 100% !important;
      flex-direction: row;
      overflow-x: auto;
      position: sticky; top: 0; z-index: 5;
    }
    .actor-tab { flex: 0 0 auto; min-width: 120px; }
    .tips-panel { display: none; }
  }
  @media (max-width: 768px) {
    .conversation-area {
      min-height: calc(100dvh - 240px) !important;
      max-height: none !important;
    }
    .message-content { max-width: 85% !important; }
    .question-input--textarea { font-size: 16px !important; }
    .mention-menu {
      position: fixed !important;
      left: 8px; right: 8px; bottom: 80px;
      width: auto; max-height: 40dvh;
    }
  }
  ```
- TSX：用 `useIsMobile()` 控制 `WatsonTipsPanel` 是否包在 `MobileDrawer` 中、mention 菜单的定位策略
- 输入框聚焦时调用 `scrollIntoView({ block: 'center' })` 防止键盘遮挡

**风险**：
- 内联 styled-jsx 类名作用域可能需 `!important` 才能覆盖
- 横屏键盘弹起会压扁 `100dvh`，需 `visualViewport` API 或 `interactionmedia` 兜底

#### P2.3 InvestigationPage（勘查页）

**关键文件**：
- `frontend/src/pages/InvestigationPage.tsx`
- `frontend/src/index.css` 第 461–1018 行

**改动**：
- 场景卡片 grid `minmax(280px, 1fr)` 在 `< 768px` 改为 `minmax(140px, 1fr)`，`gap: 12px`
- 底部 3 按钮 flex 在 `< 560px` 改为 `flex-direction: column`，sticky 底部 + 安全区
- 案件摘要横幅在小屏改为可折叠

#### P2.4 ScenePage

- 画布容器加 `aspect-ratio: 16/9; max-width: 100%`
- 聊天框在小屏 `< 768px` 改为底部抽屉

#### P2.5 BriefingPage

- 已有 560px 断点，仅补 `font-size: 16px`、按钮 `min-height: 44px`、容器 padding 用 clamp

#### P2.6 StartPage / LoginPage / ConclusionPage

- 较简单，主要补容器宽度（clamp）+ 按钮触摸目标 + Modal 全屏规则

---

### P3 浮窗与交互（约 0.5 天）

**WatsonChatDialog**

**关键文件**：
- `frontend/src/components/WatsonChatDialog.tsx`
- `frontend/src/index.css` 第 1033–1148 行（`.watson-dialog` 等）
- `frontend/src/hooks/useDrag.ts`

**改动**：
- 顶部 `const isMobile = useIsMobile();`
- `useDrag({ enabled: !isMobile, ... })`
- 渲染分支：
  - 桌面：保留 `position: fixed; bottom/right; width: 360px` + 拖拽
  - 移动端：折叠态为右下角 56×56 圆形 FAB（`bottom: calc(16px + env(safe-area-inset-bottom))`）；展开态用 `MobileDrawer` 包裹，占屏 70dvh
- z-index 协调：FAB `--z-watson: 850`，Drawer `--z-drawer: 900`

---

### P4 细节打磨（约 0.5 天）

- 全局所有可点击 `min-height: 44px; min-width: 44px`
- `@media (hover: none)` 内移除 `:hover` 视觉反馈，关键状态改 `:active` / `:focus-visible`
- 字号阶梯：标题 `clamp(1.1rem, 2.6vw, 1.4rem)`，正文 `clamp(0.9rem, 2vw, 1rem)`
- 所有 sticky / fixed 底部加 `padding-bottom: env(safe-area-inset-bottom)`

---

## 关键文件清单（修改 + 新增）

**修改**：
- `frontend/src/index.css`（顶部变量 + 各页面 @media 节）
- `frontend/src/pages/DeductionBoard.tsx`
- `frontend/src/pages/InterrogationPage.tsx`（内联 `<style>` 追加 @media）
- `frontend/src/pages/InvestigationPage.tsx`
- `frontend/src/pages/ScenePage.tsx`
- `frontend/src/pages/BriefingPage.css`
- `frontend/src/pages/StartPage.tsx` / `LoginPage.tsx` / `ConclusionPage.tsx`
- `frontend/src/components/WatsonChatDialog.tsx`
- `frontend/src/hooks/useDrag.ts`（新增 `enabled` 参数）

**新增**：
- `frontend/src/hooks/useMediaQuery.ts`
- `frontend/src/components/MobileDrawer.tsx`
- `frontend/src/components/MobileDrawer.css`（或写入 index.css）

---

## 验证方法

### 启动开发服务器
```bash
cd /Users/yinbo/AI_Project/case_solve/frontend
npm install
npm run dev
```

### 类型检查与 Lint
```bash
npm run typecheck
npm run lint
```

### 真机/模拟器测试矩阵

| 设备 | 视口 | 验收重点 |
|---|---|---|
| iPhone SE（第 3 代） | 375×667 | 最窄手机：Modal 全屏、键盘弹起、Watson FAB 不被 home bar 遮挡 |
| iPhone 14 Pro | 393×852（含刘海/灵动岛） | safe-area-inset 正确、FAB 不被遮 |
| iPad mini 竖屏 | 744×1133 | 1024 断点边界、双栏精简、Tab 切换 |
| iPad Pro 11 横屏 | 1194×834 | 桌面三栏正常 |
| Pixel 7 (Android Chrome) | 412×915 | `100dvh` / `env()` 兼容 |
| 桌面 Chrome | 1920×1080 | 回归桌面布局，确保未破坏 |

### 关键回归点
1. **横竖屏旋转**：DeductionBoard 的 Drawer 状态保留，Modal 不破版
2. **键盘弹起**：审讯页输入框可见，`100dvh` 不溢出
3. **Watson FAB ↔ DeductionBoard 指认 FAB** 不重叠（z-index + 位置错位）
4. **mention 菜单**：在移动端定位正确，不被键盘遮挡
5. **拖拽禁用**：移动端 Watson 浮窗不响应触摸拖拽
6. **桌面端无回归**：所有 > 1024px 视口下布局像素级保持原样
7. **触摸目标**：所有可点击元素 ≥ 44×44

### 测试方法
- 浏览器 DevTools 设备模拟（Chrome / Safari Responsive Design Mode）
- 真机测试：用 `npm run dev -- --host` 暴露局域网地址，手机/平板浏览器访问
- 可借助 `/browse` gstack 技能截图比对关键页面

---

## 工作量预估

| 阶段 | 预估 |
|---|---|
| P0 全局基础 | 0.5 天 |
| P1 新增工具 | 0.5 天 |
| P2 页面布局重构 | 2.5 天 |
| P3 浮窗与交互 | 0.5 天 |
| P4 细节打磨 | 0.5 天 |
| 测试与回归 | 0.5 天 |
| **合计** | **~5 天** |

---

## 关键判断

**必须做**：P0 + P1 + P2.1/2.2/2.3 + P3。否则核心三个交互页面（推理板、审讯、勘查）在手机上不可用。

**可选**：P4 细节打磨、`@media (hover: none)` 全量梳理、InterrogationPage styled-jsx 长期迁出。这些是体验/可维护性优化，不阻塞「能用」。
