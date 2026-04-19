# US-018 维多利亚哥特风 UI 精致化 (T3.1 → T3.2 → T3.3 → T3.4)

**执行日期**: 2026-04-17

---

## T3.1 全局煤气灯光晕效果

### 改动文件
- `frontend/src/index.css` - 新增动画定义和应用

### 具体改动

**新增动画**:
1. `@keyframes gaslight-flicker` - 柔和的全局光晕闪烁（8秒循环）
2. `@keyframes gaslight-flicker-slow` - 错位闪烁（7-9秒循环）
3. `@keyframes button-glow` - 按钮光晕动画
4. `@keyframes title-glow` - 标题光晕动画

**应用效果**:
- `:root` 全局光晕动画
- `.start-page__title` 标题光晕
- `.start-page__start-button` 按钮光晕
- `.header-title` 页面标题光晕
- `.modal-button` 弹窗按钮光晕
- `.footer-button--next` 下一步按钮光晕

**新增壁灯装饰**:
- `.gaslight-wall-lamp` - 壁灯容器
- `.gaslight-wall-lamp--left` / `--right` - 左右壁灯位置
- 使用 CSS 伪元素创建发光灯泡效果

**StartPage.tsx 改动**:
```tsx
<div className="start-page">
  {/* 壁灯装饰 */}
  <div className="gaslight-wall-lamp gaslight-wall-lamp--left" />
  <div className="gaslight-wall-lamp gaslight-wall-lamp--right" />

  <div className="start-page__content">
```

---

## T3.2 木质纹理 / 羊皮纸纹理背景

### 改动文件
- `frontend/src/index.css` - 新增纹理类和应用

### 具体改动

**新增纹理类**:
1. `.wood-texture` - 深褐色木质纹理
   - 使用重复渐变模拟木纹
   - 叠加多个方向渐变
   - 内阴影增强质感

2. `.parchment-texture` - 米黄色羊皮纸纹理
   - 细密的水平/垂直线模拟纸张纹理
   - 径向渐变模拟中心泛黄
   - 颜色: #3d2e20

**应用到的元素**:
- `.observation-panel` - 观察笔记面板（木纹）
- `.difficulty-option` - 难度选项卡片（木纹）
- `.clue-item` - 线索卡片（羊皮纸）
- `.observation-item` - 观察记录（羊皮纸）
- `.observation-card` - 推理页面观察卡片（羊皮纸）
- `.inference-card` - 推理卡片（羊皮纸）
- `.hypothesis-card` - 假设卡片（羊皮纸）
- `.suspect-card` - 嫌疑人卡片（木纹）
- `.reveal-section` - 案件揭露区域（羊皮纸）
- `.deduction-board__sidebar` - 推理板侧边栏（木纹）
- `.inferences-section` - 推理区域（木纹）
- `.hypotheses-section` - 假设区域（木纹）

---

## T3.3 文本措辞 19 世纪化润色

### 改动文件
- `frontend/src/pages/StartPage.tsx`
- `frontend/src/pages/InvestigationPage.tsx`

### StartPage.tsx 文案改动

| 原文案 | 新文案 |
|---------|---------|
| 伦敦，1895年。迷雾笼罩的城市中，一桩谋杀案 awaits... | 伦敦，1895年。迷雾笼罩的都市中，一桩离奇命案正待阁下侦破... |
| 案件加载中... | 案件档案调取中... |
| 死者: | 罹难者: |
| 选择难度 | 选择探案难度 |
| 准备中... | 档案整理中...... |
| 开始新案件 | 着手探案 |

### InvestigationPage.tsx 文案改动

| 原文案 | 新文案 |
|---------|---------|
| 正在进入案发现场... | 正奔赴案发现场... |
| 出错了 | 出了岔子 |
| 无法加载游戏 | 无法调取档案 |
| 现场勘查 | 现场勘查 |
| 观察记录: | 勘查记录: |
| 观察笔记 | 勘查笔记 |
| 还没有记录任何观察，点击场景中的区域开始勘查吧。 | 阁下尚无勘查记录，点击场景中各处细查吧。 |
| 发现的线索 | 觅得之线索 |
| 这里暂时没有发现明显的线索。 | 此处尚无明显线索可寻。 |
| 继续勘查 | 继续细查 |
| 传唤嫌疑人 | 传唤嫌疑人的 |
| 指认凶手 | 指认真凶 |
| 审讯嫌疑人 | 传唤嫌疑人的 |
| 指认凶手 | 指认真凶 |

**华生欢迎消息改动**:
```
原: 老朋友，我们到了。这就是案发现场。仔细看看周围，任何细节都可能是重要的线索。
新: 老朋友，我们到了。这便是命案现场。细细察看周遭，任何细节皆可能至为关键。
```

---

## T3.4 字体引入

### 改动文件
- `frontend/index.html` - 引入 Google Fonts
- `frontend/src/index.css` - 定义字体变量和应用

### index.html 新增
```html
<!-- Google Fonts: 维多利亚风格字体 -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=IM+Fell+English:ital@0;1&family=Playfair+Display:wght@400;600&display=swap" rel="stylesheet" />
```

### index.css 新增字体变量
```css
:root {
  /* 字体家族 */
  --font-title: 'Cinzel', 'Playfair Display', 'Georgia', serif;
  --font-body: 'IM Fell English', 'Georgia', 'Times New Roman', serif;
  --font-ui: 'Georgia', 'Times New Roman', serif;

  font-family: var(--font-body);
  ...
}
```

### 字体应用
- `:root` 默认使用 `var(--font-body)`
- `.start-page__title` 使用 `font: 600 3rem var(--font-title)`
- `.header-title` 使用 `font: 600 1.75rem var(--font-title)`
- `.scene-description h2` 使用 `font: 600 1.25rem var(--font-title)`
- `.modal-header h2` 使用 `font: 600 1.5rem var(--font-title)`
- `.section-title` 使用 `font: 600 20px var(--font-title)`
- `.conclusion-title` 使用 `font: 600 32px var(--font-title)`
- 所有 `font-family: 'Georgia', ...` 替换为 `var(--font-ui)`

---

## 验收结果

### 前端类型检查
```bash
npm run typecheck
```

**警告**（非阻塞性）:
- `WatsonChatDialog.tsx(46,5)`: 'addWatsonMessage' 未使用
- `WatsonChatDialog.tsx(54,5)`: 'setWatsonDialogExpanded' 未使用
- `store/watsonChatStore.ts(49,88)`: 'messageType' 属性不存在

### 前端 Lint 检查
```bash
npm run lint
```

**状态**: 缺少 ESLint 配置文件

---

## 产出物清单

### 新增文件
- `frontend/public/textures/` (目录，预留扩展)

### 修改文件
1. `frontend/index.html` - 引入 Google Fonts
2. `frontend/src/index.css` - 动画、纹理、字体
3. `frontend/src/pages/StartPage.tsx` - 壁灯元素、文案润色
4. `frontend/src/pages/InvestigationPage.tsx` - 文案润色

---

## 视觉效果总结

1. **煤气灯光晕**: 柔和的黄色光晕配合规律闪烁，营造 19 世纪室内氛围
2. **壁灯装饰**: StartPage 左上角和右上角的壁灯元素增强场景感
3. **木质纹理**: 卡片、面板呈现深褐木纹，贴合维多利亚家具风格
4. **羊皮纸纹理**: 线索、笔记、推理等文档类元素使用羊皮纸质感
5. **时代字体**: Cinzel 标题 + IM Fell English 正文，强化时代感
6. **时代文案**: "阁下"、"细查"、"勘查记录" 等维多利亚用语

---

## 下一步建议

1. 运行 `npm run dev` 启动开发服务器
2. 浏览器访问 StartPage、InvestigationPage、DeductionPage 等页面
3. 视觉检查：光晕、纹理、字体、文案整体协调
4. 性能检查：动画是否流畅，无卡顿
5. 可读性检查：羊皮纸背景上的文字对比度良好
