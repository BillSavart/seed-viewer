import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin, type VRM, type VRMHumanBoneName } from '@pixiv/three-vrm';
import { Animation } from './animation.ts';
import calibration from '../../../shared/soma-calibration.json';
import { g } from './globals.ts';

// The VRM hierarchy has fewer spine/neck/finger nodes. Sampling global rotations
// and then making them relative to the mapped parent preserves skipped joints.
export const SOMA_TO_VRM: Record<string, string> = {
    hips: 'Hips', spine: 'Spine1', chest: 'Spine2', upperChest: 'Chest',
    neck: 'Neck2', head: 'Head',
};
for (const side of ['left', 'right']) {
    const s = side === 'left' ? 'Left' : 'Right';
    Object.assign(SOMA_TO_VRM, {
        [`${side}Shoulder`]: `${s}Shoulder`, [`${side}UpperArm`]: `${s}Arm`,
        [`${side}LowerArm`]: `${s}ForeArm`, [`${side}Hand`]: `${s}Hand`,
        [`${side}UpperLeg`]: `${s}Leg`, [`${side}LowerLeg`]: `${s}Shin`,
        [`${side}Foot`]: `${s}Foot`, [`${side}Toes`]: `${s}ToeBase`,
        [`${side}Eye`]: `${s}Eye`,
    });
    for (const [finger, source] of [['Index', 'Index'], ['Middle', 'Middle'], ['Ring', 'Ring'], ['Little', 'Pinky']]) {
        for (const [i, part] of ['Proximal', 'Intermediate', 'Distal'].entries()) {
            SOMA_TO_VRM[`${side}${finger}${part}`] = `${s}Hand${source}${i + 2}`;
        }
    }
    for (const [i, part] of ['Metacarpal', 'Proximal', 'Distal'].entries()) {
        SOMA_TO_VRM[`${side}Thumb${part}`] = `${s}HandThumb${i + 1}`;
    }
}

type Binding = { target: THREE.Object3D; source: number; parentSource: number };

class HumanoidHelper extends THREE.LineSegments {
    constructor(private pairs: [THREE.Object3D, THREE.Object3D][]) {
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pairs.length * 6), 3));
        super(geometry, new THREE.LineBasicMaterial({ color: 0x0088aa, depthTest: false, depthWrite: false, toneMapped: false }));
        this.frustumCulled = false;
        this.visible = false;
    }
    updateMatrixWorld(force?: boolean) {
        const positions = this.geometry.getAttribute('position');
        const v = new THREE.Vector3();
        this.pairs.forEach(([child, parent], i) => {
            child.getWorldPosition(v); positions.setXYZ(i * 2, v.x, v.y, v.z);
            parent.getWorldPosition(v); positions.setXYZ(i * 2 + 1, v.x, v.y, v.z);
        });
        positions.needsUpdate = true;
        super.updateMatrixWorld(force);
    }
    dispose() { this.geometry.dispose(); (this.material as THREE.Material).dispose(); }
}

export class VRMModel {
    object!: THREE.Group;
    vrm!: VRM;
    skeletonHelper!: HumanoidHelper;
    hips!: THREE.Object3D;
    private motion?: Animation;
    private globalFrames = new Float32Array();
    private rootFrames = new Float32Array();
    private bindings: Binding[] = [];
    private restHips = new THREE.Vector3();
    private restFootHeight = 0;
    private ratio = 1;
    readonly retargetInfo = { mappedBones: 0, sourceRestPose: '', heightScale: 1 };

    async init(url: string) {
        const loader = new GLTFLoader();
        loader.register(parser => new VRMLoaderPlugin(parser));
        const gltf = await loader.loadAsync(url);
        this.vrm = gltf.userData.vrm;
        if (!this.vrm || this.vrm.meta.metaVersion !== '1') throw new Error('請使用 VRM 1.0 模型。');
        this.object = this.vrm.scene;
        this.object.traverse((child: any) => {
            if (child.isMesh) { child.frustumCulled = false; child.castShadow = true; }
        });
        this.hips = this.vrm.humanoid.getNormalizedBoneNode('hips')!;
        this.restHips.copy(this.hips.position);
        this.object.updateMatrixWorld(true);
        this.restFootHeight = this.lowestFoot();
        const nodes = new Map<THREE.Object3D, number>();
        const pairs: [THREE.Object3D, THREE.Object3D][] = [];
        for (const [targetName, sourceName] of Object.entries(SOMA_TO_VRM)) {
            const target = this.vrm.humanoid.getNormalizedBoneNode(targetName as VRMHumanBoneName);
            if (target) nodes.set(target, calibration.names.indexOf(sourceName));
        }
        for (const [target, source] of nodes) {
            let p = target.parent;
            while (p && !nodes.has(p)) p = p.parent;
            this.bindings.push({ target, source, parentSource: p ? nodes.get(p)! : -1 });
            if (p) pairs.push([target, p]);
        }
        this.skeletonHelper = new HumanoidHelper(pairs);
        g.SCENE.add(this.skeletonHelper);
        this.retargetInfo.mappedBones = this.bindings.length;
        const sourceHeight = -Math.min(...calibration.standardPositions.map(p => p[1]));
        this.ratio = this.restHips.y / sourceHeight;
        this.retargetInfo.heightScale = this.ratio;
    }

    get anim(): Animation { return this.motion!; }
    set anim(motion: Animation) {
        // Validate/build before replacing the previous clip.
        const bones = motion.anim.skeleton.bones;
        const byName = new Map(bones.map(b => [b.name, b]));
        const spine = byName.get('Spine1');
        if (!spine || !byName.has('Hips') || calibration.names.some(n => !byName.has(n))) {
            throw new Error('需要 SOMA 77 關節的 BVH，或 Kimodo-SOMA NPZ。');
        }
        const standard = Math.abs(spine.position.y) > Math.abs(spine.position.x);
        const tracks = new Map(motion.anim.clip.tracks.map(t => [t.name, t]));
        const globalFrames = new Float32Array(motion.frameCount * calibration.names.length * 4);
        const rootFrames = new Float32Array(motion.frameCount * 3);
        const offsets = calibration.globalOffsets.map(q => new THREE.Quaternion().fromArray(q).invert());
        const originalGlobals = calibration.names.map(() => new THREE.Quaternion());
        const q = new THREE.Quaternion();
        const root = new THREE.Quaternion();
        const position = tracks.get('Hips.position')!;
        const rootPosition = tracks.get('Root.position');
        const hipsOffset = byName.get('Hips')!.position;
        for (let f = 0; f < motion.frameCount; f++) {
            const wrapper = tracks.get('Root.quaternion');
            root.identity();
            if (wrapper) root.fromArray(wrapper.values, f * 4);
            for (let j = 0; j < calibration.names.length; j++) {
                const track = tracks.get(`${calibration.names[j]}.quaternion`)!;
                q.fromArray(track.values, f * 4);
                const parent = calibration.parents[j];
                originalGlobals[j].copy(parent < 0 ? root : originalGlobals[parent]).multiply(q);
                q.copy(originalGlobals[j]);
                if (!standard) q.multiply(offsets[j]);
                q.normalize().toArray(globalFrames, (f * calibration.names.length + j) * 4);
            }
            const v = new THREE.Vector3().fromArray(position.values, f * 3).sub(hipsOffset).applyQuaternion(root);
            if (rootPosition) v.add(new THREE.Vector3().fromArray(rootPosition.values, f * 3));
            v.multiplyScalar(0.01 * this.ratio).toArray(rootFrames, f * 3);
        }
        // Center the starting point horizontally; retain all vertical motion.
        const startX = rootFrames[0], startZ = rootFrames[2];
        for (let f = 0; f < motion.frameCount; f++) { rootFrames[f * 3] -= startX; rootFrames[f * 3 + 2] -= startZ; }
        this.motion = motion;
        this.globalFrames = globalFrames;
        this.rootFrames = rootFrames;
        this.retargetInfo.sourceRestPose = standard ? 'standard T-pose' : 'BONES-SEED (calibrated)';
        this.vrm.humanoid.resetNormalizedPose();
        this.vrm.springBoneManager?.reset();
    }

    setFrame(frame: number) {
        if (!this.motion) return;
        const f = THREE.MathUtils.clamp(frame, 0, this.motion.maxFrame);
        const a = Math.floor(f), b = Math.min(a + 1, this.motion.maxFrame), t = f - a;
        const child = new THREE.Quaternion(), parent = new THREE.Quaternion(), next = new THREE.Quaternion();
        const sample = (j: number, out: THREE.Quaternion) => {
            out.fromArray(this.globalFrames, (a * calibration.names.length + j) * 4);
            next.fromArray(this.globalFrames, (b * calibration.names.length + j) * 4);
            return out.slerp(next, t);
        };
        for (const binding of this.bindings) {
            sample(binding.source, child);
            if (binding.parentSource >= 0) child.premultiply(sample(binding.parentSource, parent).invert());
            binding.target.quaternion.copy(child);
        }
        this.hips.position.fromArray(this.rootFrames, a * 3).lerp(new THREE.Vector3().fromArray(this.rootFrames, b * 3), t);
        this.vrm.humanoid.update();
        this.object.updateMatrixWorld(true);
        // Basic penetration correction. This does not lock feet or solve hand/object contacts.
        const penetration = this.restFootHeight - this.lowestFoot();
        if (penetration > 0) this.hips.position.y += penetration;
        this.vrm.update(Math.min(Math.max(g.DELTA_TIME, 0), 1 / 30));
    }

    private lowestFoot() {
        const positions = ['leftFoot', 'rightFoot', 'leftToes', 'rightToes'].map(name => {
            const bone = this.vrm.humanoid.getRawBoneNode(name as VRMHumanBoneName);
            return bone ? bone.getWorldPosition(new THREE.Vector3()).y : Infinity;
        });
        return Math.min(...positions);
    }

    getRootWorldPosition() { return this.hips.getWorldPosition(new THREE.Vector3()); }

    dispose() { this.vrm.springBoneManager?.reset(); }
}
