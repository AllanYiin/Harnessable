# DEVNOTE — Harnessable

> 累加式開發筆記，取代 `/compact`。
> **檔頂 SNAPSHOT**：當前最新狀態（覆寫式，想知道「現在」就看這裡）。
> **檔尾 HISTORY**：時間順序的歷史區塊（累加式，想知道「為什麼」就往下讀）。

---

## 📌 SNAPSHOT — 當前狀態
<!-- 這一整段每次 /devnote 會被覆寫，只反映「到目前為止的最新狀態」 -->

**最後更新**：2026-05-23 23:31

### 需求狀態
- [x] Stage 0：專案骨架、`pyproject.toml`、README、AGENTS/CLAUDE 規範、`.env.example`、import smoke test。
- [x] Stage 1：核心資料契約、enum、`to_dict/from_dict`、validation、priority ordering tests。
- [x] Stage 2：本機 Project/State/Artifact Store、DIRTY/SAVED 狀態、import preview/apply、artifact versioning/redaction。
- [x] Stage 3：EventBus、RuleRegistry、rule lifecycle、ConditionEngine、YAML rule loader。
- [x] Stage 4：Detector interface/registry、AlwaysAllow/Regex/RequiredField、fake streaming inferential detector、RuleEngine、DecisionAggregator。
- [x] Stage 5：ExecutionGovernor、RuntimeCommand、Gateway base lifecycle、Model/Tool/Memory/Resource/Agent/Action gateways。
- [x] Stage 6：CapabilityRegistry、selector、permission default deny、health monitor、CircuitBreaker、gateway health gate。
- [x] Stage 7：FailureSignal、FallbackPolicyRegistry、FallbackGraphPlanner、FallbackManager、DegradationBudget、unsafe fallback block、disclosure support。
- [x] Stage 8：Approval lifecycle、InterruptionStore、ResumeController、SideEffectTracker、side-effect unknown no-retry。
- [x] Stage 9：Chat/Agent/Multi-agent reference adapters、streaming model path、examples。
- [x] Stage 10：TraceRecorder、AuditLogger、MetricsCollector、EvalRunner、ReplayEngine、ReplayReport diff。
- [x] Stage 11：CLI command set、local Console static UI、preview/apply flow、trace/replay/fallback commands、aspect-ratio graph contract。
- [x] Stage 12：built-in sample rules/fallback/evals、example projects、examples docs。
- [x] Stage 13：integration、regression、security、resilience、UI contract、perf、streaming tests。
- [x] Stage 14：完整文件、known limitations、release checklist、CHANGELOG、stage completion matrix。
- [x] 全量驗證：`python -m pytest` = `37 passed`；`python -m compileall src` 通過；Console TCP smoke = `console_tcp=True`。

### 未解問題
- Browser MCP 無法連到 Windows localhost，`http://127.0.0.1:8766` 在 Browser tool 端回 `ERR_CONNECTION_REFUSED`；PowerShell `Test-NetConnection` 可通，判斷為工具網路命名空間隔離，不是 Console server 本身不可用。
- 目前沒有真實 LLM provider、遠端 DB、企業 IAM 或完整 SaaS Console；這是已文件化限制，不是測試失敗。

### 關鍵技術決策（當前有效）
> 歷史上做過的、目前仍然成立的決策摘要。被推翻的決策不列。
- **Provider-neutral Python `src/` package**：以 Python SDK/CLI/本機 Console 落地，但保持模組邊界可移植到其他語言（詳見 HISTORY `[2026-05-23 23:31]`）。
- **Kernel 控制面與 Runtime Adapter 分離**：chat、agent、multi-agent 只透過 adapter 轉成 `HarnessEvent`，規則不寫進 adapter（詳見 HISTORY `[2026-05-23 23:31]`）。
- **Rule Engine 只產生 decision**：流程控制由 `ExecutionGovernor` 將 `HarnessDecision` 轉成 `RuntimeCommand`，避免 rule 直接改 runtime（詳見 HISTORY `[2026-05-23 23:31]`）。
- **所有外部能力走 Gateway**：model/tool/memory/resource/agent/action 使用同一 lifecycle：before event -> rule decision -> governor -> execute -> after/failed event（詳見 HISTORY `[2026-05-23 23:31]`）。
- **Fallback 不可繞過安全邊界**：fallback policy 可以 retry/route/degrade，但不得放寬 permission/data policy；side-effect unknown 強制人工審核（詳見 HISTORY `[2026-05-23 23:31]`）。
- **Console 採本機靜態管理面**：Stage 11 不做雲端 SaaS，只交付淺色、task-first、responsive、含 aspect-ratio graph contract 的 local Console（詳見 HISTORY `[2026-05-23 23:31]`）。

### 已知地雷（仍需注意）
> 踩過且未來仍可能重踩的坑的一句話提醒。已徹底不可能重現的不列。
- **PowerShell 編碼**：讀寫文字檔必須顯式 `-Encoding UTF8`，避免中文規格或文件亂碼（詳見 HISTORY `[2026-05-23 23:31]`）。
- **Package import 環境**：未安裝 editable package 時，直接 `python -c "import harnessable"` 可能找不到 module；pytest 透過 `pyproject.toml` 的 `pythonpath = ["src"]` 可正常跑（詳見 HISTORY `[2026-05-23 23:31]`）。
- **Circular import**：detectors 不應透過 package `__init__` 反向載入 rules package，內部 import 要指向具體模組（詳見 HISTORY `[2026-05-23 23:31]`）。
- **Start-Process 引號**：PowerShell `Start-Process -ArgumentList` 傳 `python -c` 程式碼時容易被拆壞；需要用陣列安全傳參或改用 `python -m http.server` smoke（詳見 HISTORY `[2026-05-23 23:31]`）。
- **Browser localhost 隔離**：Browser MCP 可能無法連 Windows localhost；必要時以 PowerShell `Test-NetConnection` 與靜態/UI contract tests 作為替代證據（詳見 HISTORY `[2026-05-23 23:31]`）。

---

# 📜 HISTORY

---

## [2026-05-23 23:31] 從 MVP 補齊到 15 階段可落地版本並建立 DEVNOTE

### 本次做了什麼（增量）
依 `harnessable規格.txt` 由 Stage 0 逐階段稽核並補齊到 Stage 14。最終交付包含 Python `harnessable` package、SDK/CLI、本機 Console 靜態 UI、核心資料契約、Rule Engine、Decision Algebra、Gateway lifecycle、Capability/Fallback/Approval/Observability/Eval/Replay/Adapter 模組、built-in rules/fallback/evals、example projects、完整文件與測試矩陣。全量驗證結果為 `37 passed`，`python -m compileall src` 通過，Console TCP smoke 通過。

### 本次重大技術決策
- **把 MVP 調整為逐 Stage 收尾**
  - 內容：使用者指出「我要的不是 MVP」，因此改為從 Stage 0 到 Stage 14 逐項檢查缺口並補齊。
  - 理由：原本 MVP 只覆蓋核心架構，無法滿足完整規格要求；逐階段收尾可避免跳過 Console、builtins、integration/security/regression tests、文件化等後段工作。
  - 影響：新增 `docs/stage-completion.md` 作為完成矩陣，並將測試擴充到 37 個。

- **維持本機可落地而非雲端 SaaS**
  - 內容：Console 以 `src/harnessable/console/static/*` + `harnessable console` 本機 server 交付，沒有引入前端框架或雲端部署。
  - 理由：規格明確本版不做完整多租戶 SaaS；本機 Console 足以支援 project/rules/fallback/trace/approval 的管理入口。
  - 影響：UI 測試以靜態 contract、CSS `aspect-ratio` 與 TCP smoke 為主。

- **Fake streaming inferential detector 作為介面佔位**
  - 內容：`FakeStreamingInferentialDetector` 模擬 streaming detector，不接真實 LLM provider。
  - 理由：規格要求 LLM 類輸出必須 streaming，但本版不綁定任何供應商。
  - 影響：未來接真實 provider 時要保留 streaming contract，不可改成一次性 blocking response。

- **Fallback safety 先做硬邊界**
  - 內容：`FallbackManager` 會阻擋 unsafe selector，例如 `same_or_stricter_permission_boundary: false`；side-effect unknown 直接 `REQUIRE_APPROVAL`。
  - 理由：規格明確 fallback 不得繞過安全、權限、隱私、審計與人工審核。
  - 影響：未來新增 fallback node plugin 時必須通過相同安全檢查。

### 本次失敗經驗與填坑
- **Detector / RuleEngine circular import**
  - 試過無效：`rule_engine.py` 從 `harnessable.detectors` package import `DetectionOutcome, DetectorRegistry`，而 `detectors.__init__` 又載入 computational detector，間接拉到 rules package。
  - 最終解法：改成從 `harnessable.detectors.registry` 與 `harnessable.detectors.results` 直接 import；computational detector 自帶 `_lookup`，不依賴 `ConditionEngine`。
  - 根因：package `__init__` 聚合匯出很容易形成初始化迴圈，核心模組內部應盡量使用具體模組 import。

- **CLI/Console smoke 使用 `C:\tmp` 失敗**
  - 試過無效：在 `C:\tmp` 建立 smoke project，出現 `PermissionError: [WinError 5] 存取被拒。`
  - 最終解法：改用 workspace 內 `.tmp_cli_smoke`，並在 `.gitignore` 排除暫存產物。
  - 根因：sandbox 允許的 writable root 與實際 Windows 權限可能不一致；測試應優先寫入專案 workspace 或 pytest `tmp_path`。

- **PowerShell `Start-Process -ArgumentList` 傳 `python -c` 程式碼被拆壞**
  - 試過無效：`Start-Process python -ArgumentList '-c','from harnessable.console.server import run; run(port=8765)'` 造成 `SyntaxError: from`。
  - 最終解法：Console server factory 用單元測試驗證；runtime smoke 改用 `python -m http.server` 啟動靜態目錄並用 `Test-NetConnection` 檢查 TCP。
  - 根因：PowerShell 對 `Start-Process -ArgumentList` 的字串合成與引號處理容易破壞 Python inline code。

- **Browser MCP 無法連 Windows localhost**
  - 試過無效：Browser tool navigate `http://127.0.0.1:8765` / `8766`，均回 `ERR_CONNECTION_REFUSED`；`file://` 也被 Browser tool 擋。
  - 最終解法：PowerShell 端用 `Test-NetConnection` 確認 Console static server 可 listen，並補 `tests/ui/test_console_layout_contract.py` 與 `tests/test_cli_console.py` 驗證 UI contract。
  - 根因：Browser MCP 與 Windows shell 可能不在同一網路命名空間或 localhost 視角，不能把 Browser refusal 直接等同於 server 不可用。

### 備註
- 本次依使用者要求建立 `DEVNOTE.md`，採「檔頂 snapshot 覆寫、檔尾 history 累加」格式。首次建立時歷史區塊記錄整個初始開發與收尾脈絡。
- 外部校準只用來確認筆記/變更紀錄應精簡、可追溯、避免 commit dump；實作仍以本地規格與 repo 狀態為準。
