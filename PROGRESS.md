# BONES-SEED Viewer fork：目前進度

更新日期：2026-10-29（台北時間）。BONES-SEED 的程式修改位於此 repository；原始資料集仍放在同層 `bones-seed/`。

## 來源與分支

- 上游：`bones-studio/seed-viewer`，本次修改起點 `d9963c21bee413e7eb63c1b88ae01cdcb2cf3601`。
- 個人 fork 目標：`BillSavart/seed-viewer`。
- 開發分支：`work/ssd-vrm-viewer`；`main` 保留上游版本。
- `upstream` 指向官方 repo，`origin` 指向個人 fork；預設 push 選擇 `origin`。

## 已完成

- rapidgzip + SQLite 索引直接讀取 SOMA Uniform／G1 的 tar.gz，無須展開完整資料集。
- 索引進度 API 與提示、索引未完成期間的可播放清單、原 SOMA／G1 支援。
- VRM 1.0 載入與 SOMA 重定向；目前 avatar 對應 54 個骨骼，保留 MToon 材質及 Spring Bone。
- 依身高調整根位移與基本腳底穿地補正。
- BVH／Kimodo-SOMA 30／77 關節 NPZ 匯入、FPS 選擇與格式檢查。
- SOMA／VRoid 切換保留動作與影格；預設 VRoid；改善 metadata 跳脫與 Blob URL 回收。
- Kimodo 專用 `kimodo-preview.html`，供 `BillSavart/kimodo` 的 `work/vrm-preview` 分支內嵌。

## 工具與資料

原先在 repository 外的索引、啟動及驗證工具，另有一份受版本控制的原始碼位於 `tools/local/`；原工作區工具保持原樣。metadata 分析程式及彙總結果位於 `analysis/bones-seed/`。

完整資料集、metadata 主檔、avatar、下載模型、套件環境、SQLite／gzip 索引及執行中狀態不加入此 fork。小型原始動作與標註範例仍只保留在原工作區；操作文件與選定驗證結果見 `docs/local/`。

## 本機環境與限制

- Viewer：`http://127.0.0.1:8666/`；Kimodo：`http://127.0.0.1:7860/`。
- Viewer Python 3.11；前端 Node 20.10.0；額外 Python 依賴見 `backend/requirements-ssd.txt`。
- `backend/src/dist` 是指向 `../../frontend/public/dist` 的連結；前端需自行 build。
- `archive_storage.py`、`local_migration.py`、`globals.py`、啟動及驗證工具仍有 `/home/imlab/Desktop/Bill` 的本機路徑。
- avatar API 目前讀取 repo 同層的 `AvatarSample_M.vrm`；新機器需自行提供 VRM 1.0 模型。
- 沒有完整腳鎖定／道具接觸 IK、表情／嘴型生成或 `.vrma` 匯出。
- `tools/local/migrate.py` 是歷史搬移工具；`HARDWARE_HOLD` 保留。日常使用 SSD 索引，不需要執行搬移。

## 驗證與待辦

2026-10-29 已通過原環境 NPZ 轉換測試 3/3、搬移 fixture 測試 3/3 與 production build。build 尚有既有 Browserslist／bundle 大小／重複 import 提示，未阻止產出。

先前另有全庫索引覆蓋、22 筆代表性動作、8 個 Kimodo 範例及 VRoid 互動驗證。這些是歷史紀錄，未宣稱逐筆播放全庫，也未在此次重新執行瀏覽器或 GPU 測試。

待辦：將固定路徑改成環境設定、整理新機器安裝步驟、獨立運行的瀏覽器測試、改善腳滑與接觸。

## 日常管理

```bash
git status
git add <changed-files>
git commit -m "describe the change"
git push -u origin work/ssd-vrm-viewer
```

上游更新先執行 `git fetch upstream` 並檢視差異；兩個 fork 的進度分支配對使用。
