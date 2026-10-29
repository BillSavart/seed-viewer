
export function fillTwoColumnMetadata(dict: { [key: string]: string }, preprocess: boolean = true) {
    const escape = (value: unknown) => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
    const table = document.getElementById("metadata-viewer-table")!;
    
    const keys = Object.keys(dict);
    if (preprocess){

        // put keys starting with move_ first, then take_ then others
        keys.sort((a, b) => {
            if (a.startsWith("move_") && !b.startsWith("move_")) return -1;
            if (!a.startsWith("move_") && b.startsWith("move_")) return 1;
            return 0;
        });
        
        // // put keys starting with take_ first, then others
        // keys.sort((a, b) => {
        //     if (a.startsWith("take_") && !b.startsWith("take_")) return -1;
        //     if (!a.startsWith("take_") && b.startsWith("take_")) return 1;
        //     return 0;
        // });
       
        const second = [
            "filename",
            "move_name",
            "content_natural_desc_1",
            "content_natural_desc_2",
            "content_natural_desc_3",
            "content_natural_desc_4",
            "content_technical_description",
            "content_short_description",
            "content_short_description_2"
        ]
        keys.sort((a, b) => {
            if (second.includes(a) && !second.includes(b)) return -1;
            if (!second.includes(a) && second.includes(b)) return 1;
            return 0;
        });

    }
        
        table.innerHTML = /*html*/`
        <colgroup>
            <col span="1" style="width: 40%">
            <col span="1" style="width: 60%;">
        </colgroup>
        <tbody>
            ${
                keys.map((key) => /*html*/`
                <tr class="border-b border-gray-100 hover:bg-gray-50 break-words text-left text-sm">
                    <td class="px-2 py-1 bg-gray-50 text-gray-600 break-all align-top font-semibold">${escape(key)}</td>
                    <td class="px-2 py-1 align-top">${escape(dict[key])}</td>
                </tr>
                `).join("")
            }
        </tbody>

    `;

    // const movename = document.getElementById("metadata-viewer-movename")!;
    // movename
}

export function clearMetadataViewer(){
    const table = document.getElementById("metadata-viewer-table")!;
    table.innerHTML = `<div class="m-1 p-1">No metadata to show.</div>`
}

export function initMetadataViewer(){
    const div = document.getElementById("metadata-viewer")!;
    div.className += " h-full w-full flex flex-col"
    div.innerHTML = /*html*/`
    <div class="px-3 py-2 border-b border-gray-200 bg-white flex-none">
        <span class="text-sm font-semibold text-gray-700">Metadata</span>
    </div>
    <div class="flex-1 overflow-y-auto">
        <table id="metadata-viewer-table" class="w-full mb-2 table-fixed"></table>
    </div>
    `

    clearMetadataViewer()
}

// export function fillMetadataViewer(data:string){
//     const span = document.getElementById("metadata-viewer-data")!;
//     span.innerHTML = data
// }
