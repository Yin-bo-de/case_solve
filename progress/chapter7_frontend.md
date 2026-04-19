# 章节 7 前端改造实施记录

**日期**: 2026-04-19
**分支**: ralph/sherlock-holmes-detective-game

## 完成事项

### 7.1 类型与 API 客户端
- `frontend/src/types/game.ts`：新增 `SceneObject`, `Scene`, `SceneSearchResponse`, `ReasoningRecord`, `WatsonTip`；扩展 `Clue`（+`userLabel/sourceType/sourceRef/userGenerated`）、`Case`（+`scenes`）、`Inference`（+`clueIds/verificationResult/oracleExplanation/userMarkedImportant`）
- `frontend/src/services/api.ts`：新增 `sceneSearch`, `addClue`, `submitReasoning`, `extractClueFromInterrogation`, `getInterrogationTips`；改造 `makeAccusation` 接受 `reasoningRecordIds`

### 7.2 勘查页面重构
- `frontend/src/App.tsx`：新增路由 `/investigation/:gameId/scene/:sceneId`
- `frontend/src/pages/ScenePage.tsx`（新建）：三列布局（对象列表 / 氛围图 / NPC对话）
- `frontend/src/components/ScenePanel/SceneChat.tsx`（新建）：场景 NPC 对话，候选线索 → AddClueModal
- `frontend/src/components/ScenePanel/SceneObjectCard.tsx`（新建）
- `frontend/src/components/ScenePanel/AddClueModal.tsx`（新建）
- `frontend/src/pages/InvestigationPage.tsx`：替换热区点图为场景列表卡片，已添加线索面板
- `frontend/src/store/cluesStore.ts`：新增 `addClueFromBackend` 方法

### 7.3 推理板重构
- `frontend/src/store/deductionStore.ts`：新增 `reasoningRecords`, `selectedClueIds`, `filter`；新增 `submitReasoning/toggleClue/setFilter/markImportant/deleteRecord/accuse`；保留旧版兼容 actions
- `frontend/src/pages/DeductionBoard.tsx`：完全重写，双栏布局（线索选择 / 推理记录），Oracle 验证显示，`AccusationModal` FAB
- `frontend/src/components/ReasoningRecordCard.tsx`（新建）：verdict 徽章、关联线索 chip、裁决官反馈
- `frontend/src/components/CombineReasoningModal.tsx`（新建）
- `frontend/src/components/AccusationModal.tsx`（新建）：1-3 条推理记录 + 嫌疑人选择

### 7.4 审讯页面增强
- `frontend/src/components/SelectableMessage.tsx`（新建）：鼠标选中文本 → 浮动"📎 生成线索"按钮
- `frontend/src/components/ExtractClueModal.tsx`（新建）
- `frontend/src/components/WatsonTipsPanel.tsx`（新建）：展示 suggestion/contradiction 两种 tip
- `frontend/src/store/interrogationStore.ts`：新增 `watsonTips/watsonTipsLoading/extractedClues`；新增 `fetchTips/extractClue/clearWatsonTips`
- `frontend/src/pages/InterrogationPage.tsx`：嫌疑人消息渲染换为 `SelectableMessage`，每轮问答后触发 `fetchTips`，右侧 `WatsonTipsPanel`，`ExtractClueModal`

### 样式
- `frontend/src/index.css`：新增推理板暗色金边样式、场景页三列样式、通用 Modal、SelectableMessage tooltip 等约 300 行

## 验收结果
- `npm run typecheck`：✅ 全绿（0 错误）
- `npm run lint`：ESLint 配置缺失为预存问题，非本次引入
