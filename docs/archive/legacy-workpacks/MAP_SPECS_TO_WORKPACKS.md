# MAP_SPECS_TO_WORKPACKS（母体 Spec → 工作包映射）

**目标**：让 `docs/specs/*` 与审计报告在多 Agent 工作包体系下可被快速引用。母体项目的 Spec 主要作为"参考实现与风险提示"，新项目 GridWorkflow 以 `docs/` 与 `docs/WORKPACKS/gridworkflow/*` 为主。

---

## 1. 直接可复用为 GridWorkflow 的知识点

- `SPEC-005_KEY_COST_MGMT.md` → WP-GW-90_RISK_REGISTER（成本/配额/限流/并发控制）
- `SPEC-ARCH-02_LLM_ABSTRACTION.md` → WP-GW-02_BACKEND_PROXY（上游封装边界与抽象策略参考）
- `SPEC-ARCH-01_MODULAR_VIDEO_ARCH.md` → WP-GW-03_VIDEO_SORA2（provider 封装与任务形态参考）
- `SPEC-ARCH-04_IMAGE_PROVIDER.md` → WP-GW-02_BACKEND_PROXY（图像 provider 抽象参考）

---

## 2. 主要用于母体项目（Grid-Cine Director）的 Spec

- `SPEC-UI-01_TIMELINE_VIEW.md`：偏母体 UI 能力，不作为 GridWorkflow 当前交付范围
- `SPEC-007_DEEP_EDIT.md`：母体编辑能力参考，不作为 GridWorkflow 当前交付范围
- `SPEC-001/002/003/004`：历史归档

---

## 3. 审计报告引用

- `AUDIT_REPORT.md` 与 `FULL_PROJECT_CODE_AUDIT_REPORT*.md`：
  - 作为风险清单与“不要再犯”的参考，关键结论应被固化到 WP-GW-90_RISK_REGISTER 与 `PRECHECK-SEC_ARCH_AGENT.md`。

