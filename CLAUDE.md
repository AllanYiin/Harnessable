# CLAUDE.md

請以繁體中文溝通。

本專案是 `harnessable`，一套 provider-neutral Harness Engineering framework。核心規則：

- 新增 runtime 只能透過 adapter，不改 Harness Kernel。
- 新增能力只能透過 `CapabilityProfile` 與 Gateway binding，不把外部呼叫散落在 runtime。
- 新增規則只能透過 `HarnessRule`、detector 或 rule loader，不把 policy 寫進 adapter。
- Rule Engine 只產生 `HarnessDecision`；Execution Governor 才能改變流程。
- 所有 LLM 產生式輸出必須 streaming。
- 匯入規則、能力、fallback、eval case 前必須 preview，再 apply。
- Fallback 不得降低安全、權限、隱私、審計、審核與 truthfulness/disclosure。
- 高風險副作用必須有 idempotency key、狀態追蹤與審核路徑。

測試要求：

- 公開 API 改動需同步更新 tests 與 docs。
- Gateway、fallback、approval、replay 的安全邊界必須有 regression/security tests。
- Console 圖表容器必須使用固定 aspect ratio。
