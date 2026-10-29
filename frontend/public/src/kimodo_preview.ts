import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { BVHLoader } from 'three/addons/loaders/BVHLoader.js';
import { Animation } from './animation.ts';
import { VRMModel } from './vrm_model.ts';
import { g } from './globals.ts';

const referrer = new URL(document.referrer || 'http://127.0.0.1:7860/');
const origin = referrer.origin;
const allowed = new Set(['127.0.0.1', 'localhost'].includes(referrer.hostname) ? [origin] : []);
const status = document.getElementById('status')!;
const canvas = document.getElementById('preview') as HTMLCanvasElement;
const renderer = new THREE.WebGLRenderer({canvas, antialias: true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xeef0f3);
scene.add(new THREE.HemisphereLight(0xffffff, 0xaab3c0, 2));
const light = new THREE.DirectionalLight(0xffffff, 2); light.position.set(3, 5, 4); scene.add(light);
scene.add(new THREE.GridHelper(30, 60, 0xb0b8c4, 0xd3d9e0));
const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 100);
camera.position.set(2.5, 1.7, 3.5);
const controls = new OrbitControls(camera, canvas);
controls.target.set(0, 0.8, 0); controls.enableDamping = true;
g.SCENE = scene; g.CURRENT_MODEL = 'vrm';
const models = new Map<string, VRMModel>();
let frame = 0;
let revision = 0;
let work = Promise.resolve();
const clock = new THREE.Clock();
const state = (window as any).kimodoPreview = {ready: false, frame: 0, models: 0, motions: [] as string[], errors: [] as string[]};
(state as any).inspect = () => [...models.entries()].map(([id, model]) => ({
    id, frames: model.anim?.frameCount, fps: model.anim?.fps, mappedBones: model.retargetInfo.mappedBones,
    rotations: Object.values(model.vrm.humanoid.normalizedHumanBones).flatMap(b => b.node.quaternion.toArray()),
}));

function clear() {
    revision++;
    for (const model of models.values()) {
        scene.remove(model.object, model.skeletonHelper);
        model.skeletonHelper.dispose();
        model.object.traverse((obj: any) => {
            obj.geometry?.dispose();
            const materials = Array.isArray(obj.material) ? obj.material : [obj.material];
            for (const material of materials) if (material) {
                for (const value of Object.values(material)) if ((value as any)?.isTexture) (value as THREE.Texture).dispose();
                material.dispose();
            }
        });
        model.dispose();
    }
    models.clear(); state.models = 0; state.motions = [];
}

async function motion(data: any, requestedRevision: number) {
    if (requestedRevision !== revision) return;
    let model = models.get(data.id);
    if (!model) {
        model = new VRMModel();
        await model.init('/api/avatar');
        if (requestedRevision !== revision) {
            scene.remove(model.skeletonHelper); model.skeletonHelper.dispose(); model.dispose(); return;
        }
        models.set(data.id, model); scene.add(model.object);
    }
    const animation = new Animation(new BVHLoader().parse(data.bvh), data.id);
    animation.fromBrowser = false; model.anim = animation;
    const ordered = [...models.values()];
    ordered.forEach((item, i) => { item.object.position.x = (i - (ordered.length - 1) / 2) * 1.3; });
    state.models = models.size; state.motions = [...models.keys()];
    status.textContent = `Kimodo · VRoid · ${models.size} 個樣本 · ${animation.frameCount} 幀`;
    if (models.size > 1) status.textContent += ' · 採用樣本前請取消 VRoid Preview，回原視圖點選';
}

window.addEventListener('message', event => {
    if (event.source !== parent || !allowed.has(event.origin) || event.data?.channel !== 'kimodo-vrm') return;
    const data = event.data;
    if (data.action === 'clear') clear();
    else if (data.action === 'frame') frame = Math.max(0, Number(data.frame) || 0);
    else if (data.action === 'motion') {
        const requestedRevision = revision;
        work = work.then(() => motion(data, requestedRevision)).catch(error => {
            state.errors.push(String(error)); status.textContent = `VRoid 載入失敗：${error.message}`;
        });
    }
});
function forwardKey(event: KeyboardEvent) {
    if (['Space', 'ArrowLeft', 'ArrowRight'].includes(event.code)) {
        event.preventDefault(); parent.postMessage({channel: 'kimodo-vrm', action: 'key', eventType: event.type, key: event.key, code: event.code}, origin);
    }
}
window.addEventListener('keydown', forwardKey);
window.addEventListener('keyup', forwardKey);
function render() {
    requestAnimationFrame(render);
    g.DELTA_TIME = Math.min(clock.getDelta(), 0.05);
    for (const model of models.values()) if (model.anim) model.setFrame(frame);
    state.frame = frame;
    const width = canvas.clientWidth, height = canvas.clientHeight;
    if (canvas.width !== Math.round(width * renderer.getPixelRatio()) || canvas.height !== Math.round(height * renderer.getPixelRatio())) {
        renderer.setSize(width, height, false); camera.aspect = width / Math.max(height, 1); camera.updateProjectionMatrix();
    }
    controls.update(); renderer.render(scene, camera);
}
render();
state.ready = true;
status.textContent = 'Kimodo · VRoid · 等待動作';
parent.postMessage({channel: 'kimodo-vrm', action: 'ready'}, origin);
