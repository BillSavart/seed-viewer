import { g } from './globals.ts';
import { loadBVHString } from './animation.ts';
import { fetchTemporalLabels } from './temporal_labels.ts';
import { lg } from './browser/__localGlobals.ts';

export function initMotionImport() {
    const panel = document.createElement('div');
    panel.id = 'motion-import';
    panel.style.cssText = 'padding:8px 12px;border-top:1px solid #ddd;display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px';
    panel.innerHTML = `<label style="cursor:pointer;border:1px solid #ccc;border-radius:6px;padding:5px 8px">
        載入動作 <input id="motion-file" type="file" accept=".bvh,.npz" style="display:none">
        </label><label title="Kimodo NPZ 沒有固定的 FPS 欄位，請填生成時的幀率">NPZ FPS
        <input id="motion-fps" type="number" min="1" max="240" value="30" style="width:42px;border:1px solid #ccc;border-radius:4px"></label>
        <span id="motion-import-status" role="status">SOMA BVH / Kimodo NPZ</span>`;
    document.getElementById('browser')!.appendChild(panel);
    const input = panel.querySelector<HTMLInputElement>('#motion-file')!;
    const status = panel.querySelector<HTMLElement>('#motion-import-status')!;
    input.addEventListener('change', async () => {
        const file = input.files?.[0];
        if (!file) return;
        if (g.CURRENT_MODEL === 'g1') { status.textContent = '請先切換 VRoid 或 SOMA。'; input.value = ''; return; }
        const fps = Number(panel.querySelector<HTMLInputElement>('#motion-fps')!.value);
        if (!Number.isFinite(fps) || fps < 1 || fps > 240) { status.textContent = 'FPS 需介於 1–240。'; input.value = ''; return; }
        g.SPINNER.show('Loading motion');
        status.textContent = '載入中…';
        const previousPlaying = g.PLAYING;
        g.PLAYING = false;
        try {
            lg.CONTROLLER?.abort();
            let text: string;
            if (file.name.toLowerCase().endsWith('.npz')) {
                const body = new FormData(); body.append('file', file);
                const response = await fetch(`${g.BACKEND_URL}/motion/import-npz?fps=${fps}`, { method: 'POST', body });
                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'NPZ 載入失敗。');
                text = data.tree;
            } else if (file.name.toLowerCase().endsWith('.bvh')) text = await file.text();
            else throw new Error('請選擇 SOMA BVH 或 Kimodo-SOMA NPZ。');
            await loadBVHString(text, file.name.replace(/\.(npz|bvh)$/i, ''), false);
            await fetchTemporalLabels('');
            status.textContent = `${file.name} · ${g.MODEL3D.anim.frameCount} 幀`;
            g.PLAYING = true;
            const play = document.getElementById('playButton'), pause = document.getElementById('pauseButton');
            if (play && pause) { play.style.display = 'none'; pause.style.display = 'block'; }
        } catch (error) {
            status.textContent = error instanceof Error ? error.message : String(error);
            g.PLAYING = previousPlaying;
        } finally { input.value = ''; g.SPINNER.hide('Loading motion'); }
    });
}
