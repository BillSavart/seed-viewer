# 本機工具原始碼

這裡將原本位於 `/home/imlab/Desktop/Bill/bones-tools/` 的工具納入 fork 版本控制。原始位置、執行中服務與索引沒有搬移。

| 工具 | 用途 |
| --- | --- |
| `build-archive-index.py` | 為 SOMA Uniform／G1 壓縮檔建立 rapidgzip 與 SQLite 索引 |
| `run-viewer.py`、`open-viewer.sh` | 原工作區的 Viewer 與 systemd 啟動入口 |
| `verify-ssd-library.py` | SSD 壓縮資料播放抽查 |
| `verify-viewer.mjs`、`verify-vrm*.mjs` | 原本的瀏覽器與 VRM 抽查 |
| `verify-kimodo-vrm.mjs` | 在真正 Kimodo 介面生成並驗證 VRoid 預覽 |
| `migrate.py`、`test_migration.py` | 歷史外接硬碟搬移程式與臨時 fixture 測試 |
| `source-integrity.json` | 2026-10-09 原始壓縮檔雜湊核對結果 |

為配合新目錄，JavaScript 的 Playwright import 已改指向本 repo 的 `frontend/node_modules/`。其他本機路徑、CDP 連接埠與輸出位置保持原設定；在新機器執行前需調整。索引仍由後端讀取原工作區的 `bones-tools/archive-index/`，不會自動改用這個目錄。

`source-integrity.json` 是歷史紀錄，索引工具不會每次重算全檔 SHA-256；新副本應另外驗證。`HARDWARE_HOLD` 與硬碟事件紀錄保留，日常播放不需要執行搬移程式。

從 repo 根目錄驗證隔離搬移測試：

```bash
python3 -m unittest discover -s tools/local -p test_migration.py -v
```

完整資料集、標註主檔、gzip／SQLite 索引與 runtime 狀態不存入 Git。`docs/local/verification/` 是歷史驗證結果；`PROGRESS.md` 區分當前驗證與尚待處理的工作。
