# Transcend 搬移中斷記錄（台北時間）

**整批搬移與解壓縮未完成，內接硬碟原始資料保留。**

目標硬碟：Transcend StoreJet，2 TB，NTFS，磁碟型號 `ST2000LM007-1R8174`，序號 `WDZ37X9B`，裝置 `/dev/sda1`。

## 實際發現

- 15:50:30：核心記錄 `usb 2-7: reset SuperSpeed USB device number 3 using xhci_hcd`。
- 15:52:43：核心回報 writeback 工作堵塞超過 120 秒。
- 15:53:03：寫入命令等待 180 秒後逾時；`I/O error, dev sda, sector 1344467392`，並出現 `lost async page write`。
- UDisks SMART：`SmartNumBadSectors=32`、`current-pending-sector=32`、`offline-uncorrectable=32`、`reallocated-sector-count=0`；整體 `SmartFailing=false`。這代表不能僅憑整體 SMART 判定為正常；本次已有實際寫入錯誤。待處理與離線不可校正計數可能指向相同磁區，不能相加成 64。
- SMART 溫度約 29°C。USB 拓撲為直接連到 5 Gbps USB 埠，未經集線器。

SMART 欄位依 [UDisks 官方文件](https://storaged.org/doc/udisks2-api/latest/gdbus-org.freedesktop.UDisks2.Drive.Ata.html) 讀取。

## 已做處置

- 停止搬移服務與對外接硬碟的檢視器讀取，要求正常卸載；未執行強制卸載、格式化或修復寫入。
- 原始三個壓縮檔仍在 `/home/imlab/Desktop/Bill/bones-seed`：
  - `soma_uniform.tar.gz`：45,188,088,297 bytes。
  - `soma_proportional.tar.gz`：45,468,083,856 bytes。
  - `g1.tar.gz`：23,499,973,647 bytes。
- 未刪除來源、未將來源目錄改成符號連結。
- 外接硬碟已寫入的片段尚未完成整體校驗，不能當作可靠完整副本。
- 新增 `HARDWARE_HOLD`，防止誤啟動搬移；需先確認硬碟或連線恢復正常後再解除。
- 檢視器已另備 32 個本機 SOMA 示範動作及完整文字標註，不依賴外接硬碟即可觀看。位置 `/home/imlab/Desktop/Bill/bones-preview`；網址 http://127.0.0.1:8666/ 。

## 接續工作

先換用另一顆健康硬碟，或換 USB 線／連接埠檢查原硬碟，重新確認 SMART 與讀寫狀況。本次失敗後重新解壓縮時，未完成校驗的套件會重寫全部動作檔，不依檔案大小跳過舊檔，以避免保留曾經寫入失敗的內容。

原 Transcend 上還有既有資料；在確認其狀態與備份前，不應直接格式化或執行會改動資料的修復操作。
