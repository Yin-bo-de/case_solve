# 线索边栏统一与 Footer 对齐改造

## Context（背景与动机）

当前游戏 5 个核心页面在「线索可视性」与「底部导航位置」上不一致：

- **InvestigationPage**：底部用 `discovered-clues-panel` 简陋展示线索清单，与 DeductionBoard 左侧线索面板割裂。
- **ScenePage / InterrogationPage**：玩家在场景探查或审讯过程中无法快速浏览已发现的线索，不得不来回跳到推理板查阅，打断侦探心流。
- **Footer-button**：InvestigationPage 已有规范（`.investigation-footer` + `.footer-button` + `.investigation-footer__actions`），InterrogationPage 用了内联 style 偏离规范，结构虽相近但不一致。

**目标**：
1. 在 investigation / scene / interrogation 三个页面的左侧引入与 deduction 同源视觉的「只读线索列表」，点击预览详情；移除 InvestigationPage 旧的底部线索面板。
2. 把 InterrogationPage 的 footer 结构与 InvestigationPage 完全对齐。

**非目标**：
- 不改 BriefingPage / ConclusionPage 的 footer（用户明确仅对齐三页）。
- 不为 ScenePage 新增 footer（其 header 已有返回链接）。
- 不在新线索面板上引入「勾选 + 组合推理」交互（那是推理板独有动作）。

---

## 实施方案

### Step 1：抽出共享组件 `CluesSidebar`

**新建文件**：`frontend/src/components/CluesSidebar.tsx`

**职责**：
- 从 `useCluesStore` 读取 `clues`
- 渲染线索列表（视觉风格复用 `.clue-list--deduction` + `.clue-item--deduction` 现有 CSS class，避免重复造样式）
- 点击线索条目 → 打开 `CluePreviewModal`（组件已存在于 `frontend/src/components/CluePreviewModal.tsx`）
- 内部维护 `previewedClueId` 状态
- 标题、空态文案、容器宽度可通过 props 微调

**Props 设计（最小化）**：
```ts
interface CluesSidebarProps {
  title?: string         // 默认 "📋 线索列表"
  emptyHint?: string     // 默认 "尚无线索，请先在场景中探查或审讯嫌疑人。"
  className?: string     // 透传外层容器 class，便于各页布局接入
}
```

**关键实现要点**：
- 不接收 `selectedClueIds` / `onToggle` 等推理板专属 props（保持只读语义）。
- 列表条目渲染保留：标签（`userLabel || description.substring(0,30)`）、来源 emoji（📍🗣📋）、验证状态徽章 (`verified ✓ / refuted ✗ / unverified ⚠️`)。
- 不渲染推理板底部的「已选 X 条 + ✨组合推理」按钮。
- 点击 item 行整体触发预览（无独立 checkbox 区域）。

**可选**：DeductionBoard.tsx 第 112-158 行的内联线索列表暂不重构（避免本次改动外溢）。后续可独立 PR 抽离。

### Step 2：扩展 `MobileDrawer` 支持 `'left'` 方向

**修改文件**：
- `frontend/src/components/MobileDrawer.tsx`：把 `position?: 'bottom' | 'right'` 扩展为 `'bottom' | 'right' | 'left'`
- `frontend/src/components/MobileDrawer.css`：补充 `.mobile-drawer--left { left: 0; top: 0; height: 100vh; width: min(80vw, 360px); }` 及对应进出动画

**为何走这条路**：ScenePage 桌面端布局已经 3 列且中间列承载场景图，再加常驻列会挤压主视觉；改用左侧浮动抽屉可在不动现有 grid 的前提下提供线索浏览能力。

### Step 3：InvestigationPage —— 单列改 2 列 + 移除旧面板

**修改文件**：
- `frontend/src/pages/InvestigationPage.tsx`
- `frontend/src/index.css`（或对应样式段）

**具体动作**：

1. **删除**第 112-127 行 `discovered-clues-panel` 整段。
2. **重构**根布局，把 `.investigation-page` 内部结构调整为：
   ```
   <div className="investigation-page">
     <header className="investigation-header">…</header>
     <div className="investigation-page__body">
       <CluesSidebar className="investigation-page__sidebar" />
       <main className="investigation-main">…原有 case-summary + scene-list…</main>
     </div>
     <footer className="investigation-footer">…</footer>
   </div>
   ```
3. **CSS**：
   - 新增 `.investigation-page__body { display: grid; grid-template-columns: 280px 1fr; flex: 1; min-height: 0; }`
   - `.investigation-page__sidebar { border-right: 1px solid rgba(201,160,92,0.2); background: rgba(0,0,0,0.2); overflow-y: auto; }`
   - 移除 `.discovered-clues-panel` 相关样式（废弃后清理，避免死代码）。
   - 移动端断点（`@media (max-width: 768px)`）：把 sidebar 改为隐藏 + 增加一个右下角浮动按钮触发 `MobileDrawer position="left"` 抽屉。复用 DeductionBoard 已有的 `useIsMobile` hook 与 `MobileDrawer` 组件。

### Step 4：ScenePage —— 增加左侧浮动按钮 + Drawer

**修改文件**：
- `frontend/src/pages/ScenePage.tsx`
- `frontend/src/index.css`

**具体动作**：

1. 在 `<div className="scene-page">` 内新增浮动按钮（左侧固定定位）：
   ```tsx
   <button className="scene-page__clues-btn" onClick={() => setShowCluesDrawer(true)}>
     📋 线索 ({clues.length})
   </button>
   ```
2. 渲染 `<MobileDrawer position="left" open={showCluesDrawer} onClose={...} title="📋 线索列表"><CluesSidebar /></MobileDrawer>`
3. 不动 `scene-page__body` 的 3 列 grid，**不加 footer**（按用户决策）。
4. CSS：`.scene-page__clues-btn` 用 `position: fixed; left: 1rem; top: 50%;` 之类，确保不挡住可查物列表的滚动。

### Step 5：InterrogationPage —— 2 列改 3 列 + footer 规范化

**修改文件**：
- `frontend/src/pages/InterrogationPage.tsx`

**具体动作**：

1. 在 `.interrogation-main` 最左侧插入 `<aside className="interrogation-clues-sidebar"><CluesSidebar /></aside>`，置于现有 `.actors-panel` 之前。
2. 调整 `.interrogation-main` 内联样式（文件中是 `<style>` 标签）：
   - 原 grid/flex（actors-panel 280px + interrogation-room 1fr）改为 3 列：`280px 280px 1fr`
   - 移动端：左侧线索栏隐藏，复用 MobileDrawer 触发，与 InvestigationPage 移动端策略一致
3. **Footer 规范化**：第 1328-1347 行 `<footer className="interrogation-footer">` 中的内联 `<div style={{display:'flex', gap:'10px'}}>` 改为 `<div className="investigation-footer__actions">`，并把 `.interrogation-footer` 内联样式与 `.investigation-footer` 完全对齐（同 padding / 同 border-top / 同 background / 同 button class）。可考虑直接把 className 改为 `investigation-footer`（最干净），或保留 class 但样式与 investigation-footer 1:1 同步。**推荐：直接复用 `.investigation-footer` class**，避免后续再次漂移。

### Step 6：验证

**手动端到端测试**（`cd frontend && npm run dev`）：

1. **Investigation 页**：
   - 桌面端：左侧线索栏常驻；初始状态空态文案出现。
   - 收集一条线索后回到该页：线索出现在边栏；点击 → CluePreviewModal 正常打开。
   - 移动端（DevTools 切换至 375px 宽）：边栏隐藏，浮动按钮出现，点击展开 left drawer。
   - 旧的 `discovered-clues-panel` 完全消失。
   - footer 三个 Link 按钮位置不变。

2. **Scene 页**：
   - 桌面端：左侧浮动按钮可见，3 列原布局未改变。
   - 点击按钮 → drawer 从左滑入，显示线索列表，点击线索打开 CluePreviewModal。
   - drawer 关闭后场景操作正常。

3. **Interrogation 页**：
   - 桌面端：3 列布局（线索 / 角色 tab / 审讯室），各栏滚动独立。
   - 移动端：线索栏隐藏，复用浮动按钮 + drawer。
   - footer 视觉与 Investigation 完全一致（按钮间距、padding、border、字体）。

4. **跨页一致性检查**：在 3 个页面间互相跳转，验证线索数据共享一致（来自 `useCluesStore`）。

5. **类型检查**：`cd frontend && npm run typecheck && npm run lint` 通过。

---

## 关键文件清单

**新增**：
- `frontend/src/components/CluesSidebar.tsx`

**修改**：
- `frontend/src/components/MobileDrawer.tsx`（扩展 position 支持 left）
- `frontend/src/components/MobileDrawer.css`（新增 left 方向样式）
- `frontend/src/pages/InvestigationPage.tsx`（删除旧面板 + 引入 sidebar + 重构布局）
- `frontend/src/pages/ScenePage.tsx`（引入 drawer 触发按钮）
- `frontend/src/pages/InterrogationPage.tsx`（3 列布局 + footer 规范化）
- `frontend/src/index.css`（投查页 body grid、sidebar、scene 浮动按钮、interrogation 3 列、移动端断点；清理 `.discovered-clues-panel` 废弃样式）

**复用（无需修改）**：
- `frontend/src/components/CluePreviewModal.tsx`（点击线索弹出的详情）
- `frontend/src/store/cluesStore.ts`（数据源）
- 现有 `.clue-list--deduction` / `.clue-item--deduction` CSS（视觉复用）
- DeductionBoard 中 `useIsMobile` hook 模式（可抽到 hooks 目录复用，或保留各页内联）

---

## 风险与边界

1. **三列布局在窄桌面（1280px 以下）的可用性**：interrogation 页变 3 列后中间审讯室可压缩。需在 `@media (max-width: 1024px)` 提前切到 drawer 模式，避免拥挤。
2. **CSS 命名**：暂不引入新的 BEM 块名 `clues-sidebar`，沿用 `.clue-list--deduction` 视觉 class 复用现成样式；如未来需要差异化（如读模式去掉左侧金色边线），再独立命名。
3. **数据一致性**：三个页面共用 `useCluesStore`，已实现单一数据源，无需额外同步逻辑。
4. **回归风险**：DeductionBoard 第 112-158 行内联线索列表本次不动；只通过共享 CSS class 间接受影响。如要重构 DeductionBoard 复用 `<CluesSidebar />`，留作后续独立 PR。
