import { chromium, expect } from '../../frontend/node_modules/@playwright/test/index.mjs';
import { readFile, writeFile } from 'node:fs/promises';

const samples = JSON.parse(await readFile('/home/imlab/Desktop/Bill/bones-example/vrm-library-samples.json', 'utf8'));
samples.push({name: 'inside_door_knob_left_side_open_R_002__A512_M', category: 'mirrored_motion', frames: 577});
const browser = await chromium.connectOverCDP('http://127.0.0.1:9334');
const page = browser.contexts()[0].pages().find(p => p.url().includes('127.0.0.1:8666')) ?? await browser.contexts()[0].newPage();
const client = await page.context().newCDPSession(page);
await client.send('Network.enable');
await client.send('Network.setCacheDisabled', {cacheDisabled: true});
const errors = [];
page.on('pageerror', e => errors.push(e.message));
page.on('dialog', async d => { errors.push(d.message()); await d.dismiss(); });
await page.goto('http://127.0.0.1:8666/?vrm=all');
await page.bringToFront();
await page.waitForFunction(() => window.g?.MODEL3D?.anim?.frameCount > 1, null, {timeout: 60000});
if (await page.evaluate(() => window.g.CURRENT_MODEL) !== 'vrm') throw new Error('VRoid is not the default');
await expect(page.locator('#tab-total-moves')).toContainText(/142,?220/);

async function select(name, frames) {
    const response = await page.request.get(`http://127.0.0.1:8666/api/storage_local/metadata/?query=${encodeURIComponent(name)}`);
    const match = (await response.json()).result.find(row => row.Filename === name);
    if (!match) throw new Error(`Motion missing from library: ${name}`);
    await page.locator('#tab-search-input').fill(name);
    await page.locator('#tab-search-input').press('Enter');
    const escaped = match['Move name'].replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const row = page.locator('#browser-table tr[name="datarow"]').filter({hasText: new RegExp(`^\\s*${escaped}\\s*$`)});
    await expect(row).toHaveCount(1, {timeout: 30000});
    await row.click();
    await page.waitForFunction(({name, frames}) => window.g.FILENAME === name && window.g.MODEL3D.anim.frameCount === frames, {name, frames}, {timeout: 90000});
}

const results = [];
for (const sample of samples) {
    const started = Date.now();
    await select(sample.name, sample.frames);
    await page.evaluate(() => { window.g.PLAYING = false; });
    const poses = [];
    for (const frame of [0, Math.floor((sample.frames - 1) / 2), sample.frames - 1]) {
        await page.evaluate(f => { window.g.FRAME = f; }, frame);
        await page.waitForTimeout(150);
        const pose = await page.evaluate(() => {
            const model = window.g.MODEL3D;
            return {
                positions: Object.values(model.vrm.humanoid.normalizedHumanBones).flatMap(b => b.node.getWorldPosition(new window.THREE.Vector3()).toArray()),
                rotations: Object.values(model.vrm.humanoid.normalizedHumanBones).flatMap(b => b.node.quaternion.toArray()),
                ...model.retargetInfo,
            };
        });
        if (pose.mappedBones !== 54 || ![...pose.positions, ...pose.rotations].every(Number.isFinite)) throw new Error(`Invalid pose: ${sample.name}, frame ${frame}`);
        poses.push(pose);
    }
    const changed = poses[0].rotations.some((v, i) => Math.abs(v - poses[1].rotations[i]) > 1e-5);
    if (!changed) throw new Error(`Motion is frozen: ${sample.name}`);
    const result = {...sample, mappedBones: 54, checkedFrames: [0, Math.floor((sample.frames - 1) / 2), sample.frames - 1], finite: true, animated: true, loadAndCheckMs: Date.now() - started};
    results.push(result);
    console.log(JSON.stringify(result));
}

const kimodoSamples = JSON.parse(await readFile('/home/imlab/Desktop/Bill/bones-example/vrm-kimodo-samples.json', 'utf8'));
const kimodoResults = [];
for (const sample of kimodoSamples) {
    await page.locator('#motion-file').setInputFiles(sample.path);
    await expect(page.locator('#motion-import-status')).toContainText(`${sample.frames} 幀`, {timeout: 30000});
    await page.evaluate(f => { window.g.PLAYING = false; window.g.FRAME = Math.floor(f / 2); }, sample.frames);
    await page.waitForTimeout(150);
    const pose = await page.evaluate(() => ({model: window.g.CURRENT_MODEL, frames: window.g.MODEL3D.anim.frameCount, mappedBones: window.g.MODEL3D.retargetInfo.mappedBones, finite: Object.values(window.g.MODEL3D.vrm.humanoid.normalizedHumanBones).every(b => b.node.quaternion.toArray().every(Number.isFinite))}));
    if (pose.model !== 'vrm' || pose.frames !== sample.frames || pose.mappedBones !== 54 || !pose.finite) throw new Error(`Kimodo sample failed: ${sample.name}`);
    kimodoResults.push({...sample, ...pose});
    console.log('KIMODO', sample.name, sample.frames);
}

// Leave the full library visible and play a short dance on the user's VRoid.
await select('moonwalk_R_001__A533', 867);
await page.locator('#tab-search-input').fill('');
await page.locator('#tab-search-input').press('Enter');
await expect(page.locator('#tab-total-moves')).toContainText(/142,?220/);
await page.evaluate(() => { window.g.PLAYING = true; window.g.FRAME = 120; });
await page.waitForTimeout(350);
const final = await page.evaluate(() => ({model: window.g.CURRENT_MODEL, name: window.g.FILENAME, playing: window.g.PLAYING, frame: window.g.FRAME, badge: document.querySelector('#migration-status').textContent}));
if (errors.length || final.model !== 'vrm' || !final.playing) throw new Error(JSON.stringify({final, errors}));
await page.screenshot({path: '/home/imlab/Desktop/Bill/bones-example/vrm-full-library.png', fullPage: true});
await writeFile('/home/imlab/Desktop/Bill/bones-example/vrm-library-verification.json', JSON.stringify({defaultModel: 'vrm', libraryTotal: 142220, coverage: '20 categories, longest motion, mirrored motion; first/middle/last frame', samples: results, kimodoSamples: kimodoResults, final, errors}, null, 2));
console.log('PASS', JSON.stringify(final));
process.exit(0);
