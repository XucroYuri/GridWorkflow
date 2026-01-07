# SPEC-AI-01: 分析流程 Prompt 强韧化 (Prompt Robustness)

> **原 ID**: SPEC-002
> **优先级**: P0

## 1. 问题背景
*   **原问题**: 剧本分析依赖 `indexOf` 精确匹配。LLM 产生的微小幻觉（如标点变化、虚词增减）会导致定位失败，切片错乱。
*   **解决思路**: 放弃在代码层做复杂的模糊匹配（治标），转而在 Prompt 层强制 LLM 输出机器可读的锚点（治本）。

## 2. 解决方案：结构化约束 (Structured Constraint)

### 2.1 策略 A: 引用完整性协议 (Quote Integrity Protocol)
在 L1 和 L3 的 System Instruction 中加入最高优先级的指令：

```markdown
[STRICT CONSTRAINT]
The fields `start_text` and `end_text` MUST be EXACT SUBSTRINGS copied from the input script.
- Do not normalize punctuation.
- Do not trim whitespace.
- Do not paraphrase.
If the model cannot find an exact match, it must widen the selection until it matches.
```

### 2.2 策略 B: 引入"锚点哈希" (Anchor Hashing) - 备选
如果策略 A 仍有误差，要求 LLM 返回"行号"而非文本。
1.  **预处理**: 在发送给 API 前，给每行剧本加前缀 `[L:001]`, `[L:002]`。
2.  **Schema**: 要求返回 `start_line_index` (int) 和 `end_line_index` (int)。
3.  **代码适配**: `geminiService.ts` 直接根据行号截取文本，完全绕过字符串匹配。

## 3. 实施计划 (Prompt Engineering)

### Step 1: 升级 `L1_SCANNER_PROMPT`
*   增加 `Strict Extraction Mode` 提示词块。
*   在 `responseSchema` 中为 `start_text` 字段增加 `description: "Exact substring copy from source"`。

### Step 2: 升级 `L3_ATOMIZER_PROMPT`
*   同样增加严格引用约束。
*   增加 `Fallback Mechanism`: 指示模型如果找不到明确的结束点，应以"动作结束"为界，而不是"对话结束"。

## 4. 验收标准
1.  使用一段包含复杂标点（如"……"、"！！！"）的中文剧本测试。
2.  L2 阶段的切片成功率达到 100%。
3.  控制台日志中不再出现 "Script slice fallback triggered" 的警告。

