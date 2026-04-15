# Zustand 状态管理使用文档

## 概述

项目使用 Zustand 作为全局状态管理库，所有状态都位于 `frontend/src/store/` 目录下。

## 已配置的中间件

### 1. DevTools 中间件
已集成 Zustand DevTools，可以在浏览器开发者工具中调试状态：
- 安装 [Redux DevTools 扩展](https://chrome.google.com/webstore/detail/redux-devtools/)
- 打开 DevTools 面板，可以看到所有 Store 的状态变化

### 2. Persist 中间件
状态自动持久化到 localStorage：
- 游戏状态、线索、推理链条等会自动保存
- 刷新页面后状态会自动恢复

## Store 列表

### 1. useGameStore
管理游戏核心状态：
```typescript
import { useGameStore } from '@/store'

const {
  gameState,      // 游戏状态
  isLoading,      // 加载状态
  error,          // 错误信息
  setGameState,    // 设置游戏状态
  setCase,        // 设置案件
  setDifficulty,   // 设置难度
  setPhase,        // 设置游戏阶段
  addInterviewedSuspect,  // 添加已审讯嫌疑人
  incrementMistakes,       // 增加错误次数
  setLoading,             // 设置加载状态
  setError,               // 设置错误
  resetGame,             // 重置游戏
} = useGameStore()
```

### 2. useCluesStore
管理线索和观察记录：
```typescript
import { useCluesStore } from '@/store'

const {
  clues,                 // 线索列表
  observations,           // 观察记录
  selectedClueIds,       // 选中的线索ID
  setClues,              // 设置线索
  setObservations,        // 设置观察记录
  addObservation,         // 添加观察
  removeObservation,      // 删除观察
  toggleClueSelection,    // 切换线索选择
  clearClueSelection,     // 清除线索选择
  markClueDiscovered,     // 标记线索已发现
  resetClues,            // 重置线索
} = useCluesStore()
```

### 3. useDeductionStore
管理推理链条：
```typescript
import { useDeductionStore } from '@/store'

const {
  deductionChain,         // 推理链条
  selectedObservationIds,  // 选中的观察ID
  selectedInferenceIds,    // 选中的推理ID
  expandedHypothesisId,    // 展开的假设ID
  setDeductionChain,        // 设置推理链条
  addInference,             // 添加推理
  updateInference,           // 更新推理
  removeInference,           // 删除推理
  addHypothesis,            // 添加假设
  updateHypothesis,          // 更新假设
  removeHypothesis,          // 删除假设
  toggleObservationSelection,  // 切换观察选择
  clearObservationSelection,   // 清除观察选择
  toggleInferenceSelection,    // 切换推理选择
  clearInferenceSelection,     // 清除推理选择
  setExpandedHypothesis,       // 设置展开的假设
  setConclusion,              // 设置结论
  setFinalAccusation,         // 设置最终指认
  resetDeduction,             // 重置推理
} = useDeductionStore()
```

### 4. useWatsonChatStore
管理华生对话：
```typescript
import { useWatsonChatStore } from '@/store'

const {
  messages,          // 对话消息
  isLoading,          // 加载状态
  error,              // 错误信息
  sendMessage,         // 发送消息
  fetchHistory,        // 获取历史
  clearMessages,        // 清空消息
  setLoading,          // 设置加载状态
  setError,            // 设置错误
  addWatsonMessage,    // 添加华生主动提示
  requestObservationComment,  // 请求观察评论
  requestIdleHint,           // 请求空闲提示
} = useWatsonChatStore()
```

**注意：** 对话框的开关和展开状态已移至 `useUIStore`，避免重复。

### 5. useUIStore
管理全局UI状态：
```typescript
import { useUIStore } from '@/store'

const {
  // 全局 UI 状态
  viewMode,                        // 当前视图模式
  isLoading,                        // 加载状态

  // 华生对话框
  watsonDialogOpen,                 // 对话框是否打开
  watsonDialogExpanded,             // 对话框是否展开
  watsonDialogPosition,             // 对话框位置
  setWatsonDialogOpen,             // 设置对话框开关
  toggleWatsonDialog,              // 切换对话框
  setWatsonDialogExpanded,          // 设置对话框展开状态
  setWatsonDialogPosition,          // 设置对话框位置

  // 勘查页面 UI
  selectedAreaId,                  // 选中的区域ID
  showAreaDetails,                 // 是否显示区域详情
  investigationSidebarTab,           // 勘查侧边栏标签
  setSelectedAreaId,                // 设置选中区域
  setShowAreaDetails,                // 设置显示区域详情
  setInvestigationSidebarTab,        // 设置侧边栏标签

  // 审讯页面 UI
  interrogationMode,                // 审讯模式
  selectedSuspectId,                // 选中的嫌疑人ID
  showSuspectSelector,              // 是否显示嫌疑人选择器
  setInterrogationMode,             // 设置审际模式
  setSelectedSuspectId,             // 设置选中嫌疑人
  setShowSuspectSelector,            // 设置显示嫌疑人选择器

  // 推理板 UI
  showInferenceForm,                // 是否显示推理表单
  showHypothesisForm,               // 是否显示假设表单
  showWatsonFeedback,               // 是否显示华生反馈
  setShowInferenceForm,             // 设置显示推理表单
  setShowHypothesisForm,              // 设置显示假设表单
  setShowWatsonFeedback,             // 设置显示华生反馈

  // 模态框
  showModal,                        // 是否显示模态框
  modalContent,                     // 模态框内容
  openModal,                        // 打开模态框
  closeModal,                        // 关闭模态框

  // 重置
  resetUI,                          // 重置UI状态
} = useUIStore()
```

## 状态管理器 (StoreManager)

提供高级状态管理功能：

```typescript
import { StoreManager } from '@/store'

// 重置所有状态
StoreManager.resetAll({
  keepGameState: false,      // 是否保留游戏状态
  keepWatsonChat: false,     // 是否保留华生对话
  keepDialogPosition: true,    // 是否保留对话框位置
})

// 创建状态快照
const snapshot = StoreManager.createSnapshot({
  includeWatsonChat: true,   // 是否包含对话消息
  includeUI: false,           // 是否包含UI状态
})

// 恢复状态快照
StoreManager.restoreSnapshot(snapshot)

// 保存快照到 localStorage
StoreManager.saveSnapshotToStorage('my-snapshot', {
  includeWatsonChat: true,
  includeUI: false,
})

// 从 localStorage 加载快照
const snapshot = StoreManager.loadSnapshotFromStorage('my-snapshot')

// 删除 localStorage 中的快照
StoreManager.deleteSnapshotFromStorage('my-snapshot')

// 列出所有快照
const snapshots = StoreManager.listSnapshots()

// 调试：打印所有状态
StoreManager.debugPrintAll()
```

## 使用示例

### 在组件中使用

```typescript
import { useGameStore, useUIStore } from '@/store'

function MyComponent() {
  // 订阅整个 store
  const gameStore = useGameStore()
  const { gameState, setPhase } = gameStore

  // 订阅特定字段（性能优化）
  const phase = useGameStore((state) => state.gameState?.phase)

  // 更新状态
  setPhase('investigation')
}
```

### 跨组件共享状态

```typescript
// 组件 A：设置华生对话框位置
function ComponentA() {
  const { setWatsonDialogPosition } = useUIStore()

  const handleDragEnd = (x: number, y: number) => {
    setWatsonDialogPosition({ x, y })
  }
}

// 组件 B：读取华生对话框位置
function ComponentB() {
  const { watsonDialogPosition } = useUIStore()
  console.log(watsonDialogPosition) // 位置跨组件共享
}
```

## 注意事项

1. **避免状态重复**：对话框开关等状态只在 `useUIStore` 中管理
2. **持久化配置**：每个 Store 通过 `partialize` 配置了需要持久化的字段
3. **DevTools 调试**：使用 Redux DevTools 可以实时查看和修改状态
4. **性能优化**：使用选择器函数订阅特定字段，避免不必要的重渲染
5. **类型安全**：所有 Store 都有完整的 TypeScript 类型定义

## 常见问题

### Q: 为什么切换页面后华生对话框位置会重置？
A: 现在不会了！位置已存储在 `useUIStore.watsonDialogPosition` 中，并持久化到 localStorage。

### Q: 如何调试状态变化？
A: 
1. 安装 Redux DevTools 扩展
2. 打开 DevTools 面板
3. 可以看到所有 Store 的状态变化历史
4. 或使用 `StoreManager.debugPrintAll()` 打印当前状态

### Q: 如何保存和恢复游戏进度？
A:
```typescript
// 保存
StoreManager.saveSnapshotToStorage('my-progress')

// 恢复
const snapshot = StoreManager.loadSnapshotFromStorage('my-progress')
if (snapshot) {
  StoreManager.restoreSnapshot(snapshot)
}
```
