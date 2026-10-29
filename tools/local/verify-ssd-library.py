import hashlib,json,re,sqlite3,time,urllib.request
from pathlib import Path
import pandas as pd
base=Path('/home/imlab/Desktop/Bill')
metadata=pd.read_parquet(base/'bones-seed/metadata/seed_metadata_v004.parquet').set_index('filename')
report={'samples':[]}
for attempt in range(30):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8666/api/migration-status',timeout=2) as r:
            status=json.load(r)
        break
    except OSError:
        time.sleep(0.3)
assert status['mode']=='internal_ssd' and status['soma_ready'] and status['g1_ready'],status
with urllib.request.urlopen('http://127.0.0.1:8666/api/storage_local/metadata/?page=1&perpage=1') as r:
    listing=json.load(r)
assert listing['total']==142220,listing
for archive,endpoint,param,field in [('soma_uniform','somabvh','bvhpath','tree'),('g1','g1csv','csvpath','csv')]:
    with sqlite3.connect(base/'bones-tools/archive-index'/(archive+'.sqlite')) as db:
        files=list(db.execute('SELECT path,size FROM files ORDER BY offset'))
    assert len(files)==142220
    for index in [0,len(files)//3,2*len(files)//3,len(files)-1]:
        path,size=files[index]
        name=Path(path).stem
        start=time.monotonic()
        with urllib.request.urlopen(f'http://127.0.0.1:8666/api/storage_local/{endpoint}/?{param}={name}',timeout=60) as response:
            motion=json.load(response)
        content=motion[field]
        assert len(content.encode())==size,(name,size,len(content.encode()))
        if field=='tree':
            assert content.startswith('HIERARCHY')
            frames=int(re.search(r'Frames:\s+(\d+)',content).group(1))
            assert frames==int(metadata.loc[name,'move_duration_frames']),(name,frames)
        else:
            assert content.startswith('Frame,') and 'root_translateX' in content.splitlines()[0],content[:150]
        report['samples'].append({'archive':archive,'name':name,'bytes':size,'seconds':round(time.monotonic()-start,3)})
# Compare independent stdlib gzip/tar previews to the new indexed decoder.
for path in list((base/'bones-preview/soma_uniform').rglob('*.bvh'))[::8]:
    name=path.stem
    with urllib.request.urlopen(f'http://127.0.0.1:8666/api/storage_local/somabvh/?bvhpath={name}',timeout=30) as response:
        actual=json.load(response)['tree'].encode()
    assert actual==path.read_bytes(),name
report.update(result='PASS',catalog_total=listing['total'],independent_preview_matches=4)
(base/'bones-tools/ssd-library-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report),flush=True)
