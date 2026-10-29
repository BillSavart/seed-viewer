import { g } from './globals.ts';
import * as THREE from 'three';
import { BVH, BVHLoader } from 'three/addons/loaders/BVHLoader.js';
import { setAnimToDownload } from './download_anim.ts';
import { fillTwoColumnMetadata } from './metadata_viewer.ts';
import calibration from '../../../shared/soma-calibration.json';


////////////////////////////////////////////////////////////////////////////////////////////////////////////////

export class Animation {
	frameCount: number;
	fps: number;
	root: THREE.Bone;
	anim: BVH;
	maxFrame: number;
	name: string;
	fromBrowser = true;
	private originalSomaClip?: THREE.AnimationClip;

	// The existing SOMA FBX rig uses BONES-SEED axes. Keep the imported clip
	// unchanged for VRM, and cache an axes-corrected copy for this FBX rig.
	getOriginalSomaClip(): THREE.AnimationClip {
		const spine = this.anim.skeleton.getBoneByName('Spine1');
		if (!spine || Math.abs(spine.position.x) >= Math.abs(spine.position.y)) return this.anim.clip;
		if (this.originalSomaClip) return this.originalSomaClip;
		const clip = this.anim.clip.clone();
		const tracks = new Map(clip.tracks.map(t => [t.name, t]));
		const offsets = calibration.globalOffsets.map(q => new THREE.Quaternion().fromArray(q));
		const global = calibration.names.map(() => new THREE.Quaternion());
		const original = calibration.names.map(() => new THREE.Quaternion());
		const local = new THREE.Quaternion();
		for (let f = 0; f < this.frameCount; f++) {
			for (let j = 0; j < calibration.names.length; j++) {
				const track = tracks.get(`${calibration.names[j]}.quaternion`);
				if (!track) throw new Error('需要完整 SOMA 77 關節 BVH。');
				const p = calibration.parents[j];
				local.fromArray(track.values, f * 4);
				global[j].copy(p < 0 ? new THREE.Quaternion() : global[p]).multiply(local);
				original[j].copy(global[j]).multiply(offsets[j]);
				local.copy(original[j]);
				if (p >= 0) local.premultiply(original[p].clone().invert());
				local.toArray(track.values, f * 4);
			}
		}
		this.originalSomaClip = clip;
		return clip;
	}

	constructor(anim: BVH, name :string) {
		this.frameCount = anim.clip.tracks[0].times.length;
		const times = anim.clip.tracks[0].times;
		this.fps = times.length > 1 ? 1 / (times[1] - times[0]) : 30;
		// Six-decimal BVH headers commonly round 1/120 or 1/30.
		if (Math.abs(this.fps - Math.round(this.fps)) < 0.01) this.fps = Math.round(this.fps);
		this.root = this.__findRoot(anim);
		this.anim = anim;
		this.maxFrame = this.frameCount - 1;
		this.name = name;
	}
	

	__findRoot(anim: BVH) : THREE.Bone {
		const root = anim.skeleton.bones.find(bone => bone.parent === null);
		if (!root) {
			console.error("Root bone not found")
		}
		return root as THREE.Bone;
	}


}



////////////////////////////////////////////////////////////////////////////////////////////////////////////////


/**
 * @param {string} bvhUrl 
 */
 export async function loadBVHUrl(bvhUrl:string, name = "no_name", fromBrowser = true, metadata: { [key: string]: string } | null = null) {

	name = name.replace(".bvh", "");
	const bvh = await new BVHLoader().loadAsync(bvhUrl);
	const anim = new Animation(bvh, name);
	if (anim.frameCount < 1 || !Number.isFinite(anim.fps) || anim.fps <= 0 ||
		bvh.clip.tracks.some(track => !track.values.every(Number.isFinite))) {
		throw new Error('BVH 的影格或關節數值無效。');
	}
	anim.fromBrowser = fromBrowser;
	g.MODEL3D.anim = anim;
	 

	if (metadata) fillTwoColumnMetadata(metadata, fromBrowser);
	if (!metadata && fromBrowser) {
		g.SPINNER.show("Fetching metadata");
		// fetch at backend /metadata GET request to get metadata.
		fetch(`${g.BACKEND_URL}/metadata/${name}`)
		.then((res) => {
			if (!res.ok) {
				console.log("Failed to fetch metadata");
				return null;
			}
			return res.json();
		})
		.then((data) => {
				if (g.FILENAME !== name) return;
				if (data) {
				fillTwoColumnMetadata(data);
			}else{
					fillTwoColumnMetadata({ "Name": name, "Frames": anim.maxFrame.toString(), "FPS": anim.fps.toString()}, false)
				}
			})
			.catch(err => {
				console.log(err);
				return null;
			}).finally(() => {
				g.SPINNER.hide("Fetching metadata");
			});
	}
	if (!metadata && !fromBrowser) fillTwoColumnMetadata({ Name: name, Frames: String(anim.frameCount), FPS: String(anim.fps) }, false);


	g.FRAME = 0;
	g.FILENAME = name;
	g.LOOP_START = 0;
	g.LOOP_END = anim.maxFrame;
	const importStatus = document.getElementById('motion-import-status');
	if (fromBrowser && importStatus) importStatus.textContent = `資料庫動作 · ${anim.frameCount} 幀`;
	

	setAnimToDownload(bvhUrl, name)

}

/**
 * @param {string} bvhString 
 */
export async function loadBVHString(bvhString:string, name = "no_name", fromBrowser = true, metadata: { [key: string]: string } | null = null) {
	const bvhURL = URL.createObjectURL(new Blob([bvhString], { type: 'text/plain' }));
	try {
		await loadBVHUrl(bvhURL, name, fromBrowser, metadata);
	} catch (error) {
		URL.revokeObjectURL(bvhURL);
		throw error;
	}
}




////////////////////////////////////////////////////////////////////////////////////////////////////////////////
