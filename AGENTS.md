# AGENTS.md

請以繁體中文溝通。

開發規範：

- 優先小步、可測、可回滾的變更。
- 不新增不必要依賴。
- 不改公開介面，除非同步更新測試與文件。
- 所有 LLM 產生式輸出必須支援 streaming。
- 所有上傳或匯入功能必須先 preview，再 apply。
- 所有縮放 UI 必須維持原始寬高比。
- Fallback 不得繞過安全、權限、隱私、審計與人工審核。
- Gateway 是外部能力的統一邊界；runtime 不應直接呼叫模型、工具、記憶、代理或外部副作用。
- Rule Engine 只產生 `HarnessDecision`；Execution Governor 是唯一能改變流程控制的模組。
- PowerShell 讀寫文字檔時必須顯式指定 `-Encoding UTF8`，除非已確認需要保留其他編碼。
