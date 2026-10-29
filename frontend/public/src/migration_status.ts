import { g, MODEL_CONFIGS } from './globals.ts';

export function initMigrationStatus() {
    const badge = document.createElement('div');
    badge.id = 'migration-status';
    Object.assign(badge.style, {
        position: 'absolute', left: '16px', top: '14px', zIndex: '30',
        maxWidth: '60%', padding: '8px 12px', borderRadius: '10px',
        background: 'rgba(255,255,255,.9)', color: '#334155', fontSize: '12px',
        pointerEvents: 'none', display: 'none'
    });
    document.getElementById('right-pane-up')!.appendChild(badge);
    let fullLibrary = false;
    async function refresh() {
        try {
            const response = await fetch('/api/migration-status');
            if (!response.ok) return;
            const status = await response.json();
            if (status.mode === 'internal_ssd') {
                badge.style.display = 'block';
                if (status.soma_ready) {
                    const updateBadge = () => {
                        badge.textContent = `${Number(status.total).toLocaleString()} 個動作 · ${MODEL_CONFIGS[g.CURRENT_MODEL].name}`;
                    };
                    updateBadge();
                    g.UPDATE_LOOP['libraryModelBadge'] = updateBadge;
                    if (!fullLibrary && document.getElementById('browser-table')) {
                        const {getTablePage} = await import('./browser/__getMetadataPage');
                        void getTablePage();
                    }
                    fullLibrary = true;
                } else {
                    badge.textContent = `內接 SSD · 正在準備完整動作庫：${Number(status.files).toLocaleString()} / ${Number(status.total).toLocaleString()}；可先播放 32 個預覽動作。`;
                }
                return;
            }
            if (status.stage === 'complete' || status.stage === 'unavailable') {
                badge.style.display = 'none';
                return;
            }
            badge.style.display = 'block';
            const name = (status.archive || '').replace('.tar.gz', '');
            const files = Number(status.extracted_files || 0).toLocaleString();
            if (status.stage === 'failed') {
                badge.textContent = (status.local_preview ? '本機預覽模式（32 個 SOMA 動作）。' : '') + '資料搬移已停止：' + status.error;
            } else if (status.stage === 'copying_metadata' || status.stage === 'starting') {
                badge.textContent = '正在準備外接硬碟資料；可先播放已完成的 SOMA 動作。';
            } else if (status.stage === 'verifying_destination') {
                badge.textContent = `${name} 解壓縮完成，正在校驗外接硬碟檔案。`;
            } else {
                badge.textContent = `${name} 搬移及解壓縮中：${files} / 142,220 個動作。可先播放已完成的 SOMA 動作；重新整理可更新清單。`;
            }
        } catch { /* Keep the viewer usable if status is temporarily unavailable. */ }
    }
    void refresh();
    window.setInterval(refresh, 10000);
}
