
const lg = {
    BVH_URL: null as string | null,
    BVH_NAME: null as string | null,
}

export function initDownloadAnimButton() {
    const button = document.getElementById("download-anim") as HTMLDivElement;
    button.className += " myicon"
    button.innerHTML = /*html*/ `
    <button class="">
    <span class="material-symbols-outlined">download</span>
    </button>
    `;
    button.querySelector("button")!.addEventListener("click", () => {
        if (!lg.BVH_URL || !lg.BVH_NAME) {
            return;
        }
        const a = document.createElement("a");
        a.href = lg.BVH_URL;
        a.download = lg.BVH_NAME + ".bvh";
        a.click();
        a.remove();
    });

}

export function setAnimToDownload(bvhUrl:string, bvhName:string){
    if (lg.BVH_URL?.startsWith('blob:') && lg.BVH_URL !== bvhUrl) URL.revokeObjectURL(lg.BVH_URL);
    lg.BVH_URL = bvhUrl;
    lg.BVH_NAME = bvhName;
}
