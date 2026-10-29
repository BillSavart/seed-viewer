import { chromium, expect } from '../../frontend/node_modules/@playwright/test/index.mjs';
import { writeFile } from 'node:fs/promises';

const browser = await chromium.connectOverCDP('http://127.0.0.1:9334');
const page = browser.contexts()[0].pages().find(p => p.url().startsWith('http://127.0.0.1:8666/')) ?? await browser.contexts()[0].newPage();
const errors = [];
const client = await page.context().newCDPSession(page);
await client.send('Network.enable');
await client.send('Network.setCacheDisabled', {cacheDisabled: true});
page.on('pageerror', error => errors.push(error.message));
page.on('dialog', async d => { errors.push(d.message()); await d.dismiss(); });
for (let attempt = 0; attempt < 30; attempt++) {
    try { if ((await fetch('http://127.0.0.1:8666/')).ok) break; } catch {}
    if (attempt === 29) throw new Error('Viewer server did not start');
    await new Promise(resolve => setTimeout(resolve, 500));
}
await page.goto('http://127.0.0.1:8666/?vrm=1');
await page.bringToFront();
await page.waitForFunction(() => window.g?.MODEL3D?.anim?.frameCount > 1, {timeout: 60000});
const name = 'inside_door_knob_left_side_open_R_002__A512';
await page.locator('#tab-search-input').fill(name);
await page.locator('#tab-search-input').press('Enter');
await expect(page.locator('#browser-table tr[name="datarow"]')).toHaveCount(2);
await page.locator('#browser-table tr[name="datarow"]').first().click();
await page.waitForFunction(n => window.g.FILENAME === n && window.g.MODEL3D.anim.frameCount === 577, name);
await page.locator('[data-model="vrm"]').click();
await page.waitForFunction(() => window.g.CURRENT_MODEL === 'vrm' && window.g.MODEL3D?.retargetInfo?.mappedBones === 54 && window.g.MODEL3D?.anim?.frameCount === 577, {timeout: 60000});
await page.evaluate(() => { window.g.PLAYING = false; window.g.FRAME = 120; });
await page.waitForTimeout(300);
const before = await page.evaluate(() => [...window.g.MODEL3D.skeletonHelper.geometry.attributes.position.array]);
await page.evaluate(() => { window.g.FRAME = 300; });
await page.waitForTimeout(300);
const after = await page.evaluate(() => [...window.g.MODEL3D.skeletonHelper.geometry.attributes.position.array]);
if (!after.every(Number.isFinite) || !before.some((v, i) => Math.abs(v - after[i]) > 1e-4)) throw new Error('VRM skeleton did not animate correctly');
await page.screenshot({path: '/home/imlab/Desktop/Bill/bones-example/vrm-bones-seed.png', fullPage: true});
console.log('BONES-SEED', await page.evaluate(() => ({...window.g.MODEL3D.retargetInfo, frame: window.g.FRAME, hips: window.g.MODEL3D.hips.position.toArray()})));

// Exercise the actual file picker and the NPZ conversion API.
const sample = '/home/imlab/Desktop/Bill/kimodo/kimodo/assets/demo/examples/kimodo-soma-rp/01_single_text_prompt/motion.npz';
await page.locator('#motion-file').setInputFiles(sample);
await expect(page.locator('#motion-import-status')).toContainText('150 幀');
await page.waitForFunction(() => window.g.MODEL3D.anim.frameCount === 150 && window.g.MODEL3D.anim.fromBrowser === false);
await page.evaluate(() => { window.g.PLAYING = false; window.g.FRAME = 45; });
await page.waitForTimeout(300);
await page.screenshot({path: '/home/imlab/Desktop/Bill/bones-example/vrm-kimodo.png', fullPage: true});
const poses = await page.evaluate(() => {
    const model = window.g.MODEL3D;
    return Object.fromEntries(Object.entries(model.vrm.humanoid.normalizedHumanBones).map(([name, b]) => [name, b.node.getWorldQuaternion(new window.THREE.Quaternion()).toArray()]));
});
await writeFile('/home/imlab/Desktop/Bill/bones-example/vrm-kimodo-pose.json', JSON.stringify(poses, null, 2));
console.log('KIMODO', await page.evaluate(() => ({...window.g.MODEL3D.retargetInfo, frames: window.g.MODEL3D.anim.frameCount, fps: window.g.MODEL3D.anim.fps})));

// Preserve an imported motion and its frame when switching humanoid models.
await page.locator('[data-model="soma"]').click();
await page.waitForFunction(() => window.g.CURRENT_MODEL === 'soma' && window.g.MODEL3D.anim?.frameCount === 150);
await page.locator('[data-model="vrm"]').click();
await page.waitForFunction(() => window.g.CURRENT_MODEL === 'vrm' && window.g.MODEL3D.anim?.frameCount === 150);
if (await page.evaluate(() => window.g.FRAME) !== 45) throw new Error('Model switch lost imported motion frame');

// A standard T-pose BVH should produce neutral normalized VRM rotations.
await page.locator('#motion-file').setInputFiles('/home/imlab/Desktop/Bill/kimodo/kimodo/assets/skeletons/somaskel77/somaskel77_standard_tpose.bvh');
await expect(page.locator('#motion-import-status')).toContainText('somaskel77_standard_tpose.bvh');
await page.evaluate(() => { window.g.PLAYING = false; window.g.FRAME = 0; });
await page.waitForTimeout(300);
const neutralError = await page.evaluate(() => Math.max(...Object.values(window.g.MODEL3D.vrm.humanoid.normalizedHumanBones).map(b => 1 - Math.abs(b.node.quaternion.w))));
if (neutralError > 1e-6) throw new Error(`Neutral pose failed: ${neutralError}`);
await page.locator('[data-model="soma"]').click();
await page.waitForFunction(() => window.g.CURRENT_MODEL === 'soma' && window.g.MODEL3D.anim?.name === 'somaskel77_standard_tpose');
if (!await page.evaluate(() => window.g.MODEL3D.anim.getOriginalSomaClip().tracks.every(t => [...t.values].every(Number.isFinite)))) throw new Error('Standard T-pose did not convert for SOMA');
await page.locator('[data-model="vrm"]').click();
await page.waitForFunction(() => window.g.CURRENT_MODEL === 'vrm' && window.g.MODEL3D.anim?.name === 'somaskel77_standard_tpose');

const previousName = await page.evaluate(() => window.g.FILENAME);
await page.locator('#motion-file').setInputFiles({name: 'invalid.npz', mimeType: 'application/octet-stream', buffer: Buffer.from('invalid npz')});
await expect(page.locator('#motion-import-status')).toContainText('File is not a zip file');
if (await page.evaluate(() => window.g.FILENAME) !== previousName) throw new Error('Invalid import replaced the previous motion');

// Restore the chosen SEED motion and keep the desktop viewer playing.
await page.locator('#browser-table tr[name="datarow"]').first().click();
await page.waitForFunction(n => window.g.FILENAME === n && window.g.MODEL3D.anim.frameCount === 577, name);
await page.evaluate(() => { window.g.FRAME = 0; window.g.PLAYING = true; });
await page.waitForTimeout(350);
const result = await page.evaluate(() => ({model: window.g.CURRENT_MODEL, name: window.g.FILENAME, playing: window.g.PLAYING, frame: window.g.FRAME, frames: window.g.MODEL3D.anim.frameCount, ...window.g.MODEL3D.retargetInfo}));
if (!result.playing || result.frame <= 0 || errors.length) throw new Error(JSON.stringify({result, errors}));
await writeFile('/home/imlab/Desktop/Bill/bones-example/vrm-verification.json', JSON.stringify({...result, bonesSeedAnimated: true, kimodoNpzImported: true, importedMotionSurvivesSwitch: true, standardTposeError: neutralError, invalidImportPreservesMotion: true, errors}, null, 2));
console.log('PASS', result);
process.exit(0);
