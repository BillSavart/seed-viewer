"""Reproduce BONES-SEED v004 clip-level statistics and figures."""
from pathlib import Path
import hashlib
import os
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('BONES_WORKSPACE_ROOT', str(OUT.parents[2])))
SOURCE = ROOT / 'bones-seed/metadata/seed_metadata_v004.parquet'
FPS = 120
df = pd.read_parquet(SOURCE)
assert df.is_mirror.notna().all() and df.is_mirror.isin([True, False]).all()
assert df.move_name.is_unique
assert df[['move_duration_frames', 'category', 'package']].notna().all().all()
assert (df.move_duration_frames > 0).all()
df['seconds'] = df.move_duration_frames / FPS
original = df.loc[~df.is_mirror].copy()
mirror = df.loc[df.is_mirror].copy()

def aggregate(column):
    all_rows = df.groupby(column).agg(total_count=('move_name', 'size'), total_seconds=('seconds', 'sum'))
    originals = original.groupby(column).agg(
        original_count=('move_name', 'size'), original_seconds=('seconds', 'sum'),
        actors=('actor_uid', 'nunique'), content_names=('content_name', 'nunique'),
        median_seconds=('seconds', 'median'))
    result = all_rows.join(originals)
    result['total_hours'] = result.pop('total_seconds') / 3600
    result['original_hours'] = result.pop('original_seconds') / 3600
    result['original_time_percent'] = result.original_hours / (original.seconds.sum()/3600) * 100
    result = result.sort_values('original_hours', ascending=False)
    result.to_csv(OUT / f'{column}_statistics.csv')
    return result

packages = aggregate('package')
categories = aggregate('category')
bins = [0, 2, 5, 10, 20, 30, 60, 120, np.inf]
labels = ['<2', '2–<5', '5–<10', '10–<20', '20–<30', '30–<60', '60–<120', '≥120']

def duration_bins(rows):
    groups = rows.groupby(pd.cut(rows.seconds, bins, right=False, labels=labels), observed=False)
    result = groups.seconds.agg(count='size', seconds='sum')
    result['count_percent'] = result['count'] / len(rows) * 100
    result['hours'] = result.pop('seconds') / 3600
    result['time_percent'] = result.hours / (rows.seconds.sum()/3600) * 100
    return result

distribution = duration_bins(original)
distribution.to_csv(OUT / 'duration_original.csv')
duration_bins(df).to_csv(OUT / 'duration_including_mirror.csv')
mirror['original_name'] = mirror.move_name.str.removesuffix('_M')
pairs = mirror.join(original.set_index('move_name')[['move_duration_frames', 'category', 'package']], on='original_name', rsuffix='_original')
assert pairs.move_duration_frames_original.notna().all()
assert pairs.category.eq(pairs.category_original).all()
assert pairs.package.eq(pairs.package_original).all()
frame_delta = pairs.move_duration_frames - pairs.move_duration_frames_original
summary = {
    'source': str(SOURCE), 'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'fps': FPS, 'total_count': len(df), 'original_count': len(original), 'mirror_count': len(mirror),
    'total_hours': df.seconds.sum()/3600, 'original_hours': original.seconds.sum()/3600,
    'mirror_hours': mirror.seconds.sum()/3600,
    'originals_without_mirror': int((~original.move_name.isin(mirror.original_name)).sum()),
    'mirror_frame_delta_counts': {str(int(k)):int(v) for k,v in frame_delta.value_counts().items()},
    'original_duration_seconds': original.seconds.describe(percentiles=[.01,.05,.1,.25,.5,.75,.9,.95,.99]).to_dict(),
    'original_unique_content_names': original.content_name.nunique(),
    'original_actors': original.actor_uid.nunique(),
}
(OUT / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n')

plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
fig, (ax, bx) = plt.subplots(1, 2, figsize=(15, 8), gridspec_kw={'width_ratios':[1.3,1]})
cat = categories.sort_values('original_hours')
colors = ['#d27a35' if v < 2 else '#4082a6' for v in cat.original_hours]
ax.barh(cat.index, cat.original_hours, color=colors)
for i, v in enumerate(cat.original_hours):
    ax.text(v+.25, i, f'{v:.3f}' if v<.1 else f'{v:.2f}', va='center', fontsize=9)
ax.set(xlabel='Hours (original clips only)', xlim=(0,39), title='Duration by category')
ax.grid(axis='x', alpha=.2); ax.set_axisbelow(True)
bx.bar(np.arange(len(distribution)), distribution.count_percent, color='#4082a6')
bx.set_xticks(np.arange(len(distribution)), labels, rotation=45, ha='right')
for i, v in enumerate(distribution.count_percent):
    bx.text(i, v+.7, f'{v:.2f}%', ha='center', fontsize=9)
bx.set(xlabel='Clip duration (seconds)', ylabel='Share of original clips (%)', ylim=(0,49), title='Clip length distribution')
bx.grid(axis='y', alpha=.2);bx.set_axisbelow(True)
bx.text(.97,.97, 'Median: 5.71 s\nMean: 7.30 s\n95th percentile: 15.77 s\n≥30 s: 725 clips (1.02%)',
    transform=bx.transAxes, ha='right', va='top', fontsize=10,
    bbox={'facecolor':'white','alpha':.9,'edgecolor':'#dddddd'})
fig.suptitle('BONES-SEED v004 · 71,132 original clips · 144.22 hours', fontsize=16)
fig.text(.5,.015,'Source: local v004 metadata | seconds = move_duration_frames / 120 | Mirrors excluded',ha='center',color='#555555')
fig.tight_layout(rect=[0,.035,1,.96])
fig.savefig(OUT/'overview.png',dpi=160)
fig.savefig(OUT/'overview.svg')
plt.close(fig)

def table(rows, kind):
    lines = [f'| {kind} | 含 Mirror 段數 | 含 Mirror 小時 | 原始段數 | 原始小時 | 表演者 | content_name 數 |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for name, r in rows.iterrows():
        lines.append(f'| {name} | {int(r.total_count):,} | {r.total_hours:.3f} | {int(r.original_count):,} | {r.original_hours:.3f} | {int(r.actors):,} | {int(r.content_names):,} |')
    return '\n'.join(lines)

report = f'''# BONES-SEED v004 動作統計

分析日期：2026-10-09（台北）。來源：`{SOURCE}`。SHA-256：`{summary['source_sha256']}`。

## 計算口徑

- 以 metadata 每一列為一段完整動作，秒數 = `move_duration_frames / 120`。120 fps 依本機 README 的 Metadata Schema。
- 原始動作依 `is_mirror == False` 篩選。三種骨架表示、同段多條文字描述不重複計數。
- package 與 category 為兩種分組，各自覆蓋全資料，兩表不可相加。
- 這是完整片段的分類與長度，未拆分 temporal labels；不等同逐秒細動作時長。
- 原始段數不等同互不相似的動作種類或獨立拍攝 session；同一內容可由多位演員、不同 take 重複。
- 本次直接統計 metadata，未讀取所有 BVH／G1 內容驗證實際幀數。

## 總量

| 資料 | 段數 | 小時 |
|---|---:|---:|
| 全部 | {len(df):,} | {df.seconds.sum()/3600:.6f} |
| 原始 | {len(original):,} | {original.seconds.sum()/3600:.6f} |
| Mirror | {len(mirror):,} | {mirror.seconds.sum()/3600:.6f} |

44 段原始動作沒有 Mirror；全部 Mirror 皆能以名稱移除 `_M` 配對原始動作。
7,653 對的 metadata 幀數相差 1 幀（7,645 對 Mirror 少 1 幀、8 對多 1 幀），因此總時長應逐筆加總，不能直接除以二。
原始資料共 522 位表演者、3,813 個不同 `content_name`；後者是命名欄位數量，不能視為語意去重後的動作類型數。

## 8 大分類

{table(packages, 'Package')}

## 20 個細分類

{table(categories, 'Category')}

## 稀缺類型與補充方向

以下為本資料內部的相對稀缺判讀，不是通用最低資料量標準；是否補充取決於模型任務。

- Martial Arts：10 段、43.64 秒、2 位表演者，若需武術能力應優先補充。
- Looking and Pointing：90 段、11.14 分鐘、21 位表演者。Magic：80 段、10.50 分鐘、25 位表演者；Magic 主要適用需要幻想／遊戲動作的任務。
- Stunts：429 段、40.69 分鐘、34 位表演者；需要特技能力時補充。
- 日常／機器人任務可優先考慮 Household（659 段、1.535 小時、14 人）、Environments（307 段、1.002 小時、14 人）、Complex Actions（270 段、1.612 小時、23 人），增加演員、物件／場景和動作串接的變化。
- Locomotion package 佔原始總時長 {packages.loc['Locomotion','original_time_percent']:.2f}%。Baseline 雖有 20.192 小時、11,440 段，但只有 13 個 `content_name`，時長多不代表內容種類多。分類沿用原始 metadata。
- Mirror 不會增加表演者與原始拍攝多樣性；補資料時應以未鏡像片段與多樣性評估。

## 原始動作長度

平均 7.299 秒、中位數 5.708 秒；中間 50% 位於 4.000–8.358 秒。
90／95／99 百分位為 12.617／15.767／30.217 秒；範圍 0.575–180.142 秒。

| 秒數區間（左含右不含） | 原始段數 | 段數占比 | 原始小時 | 時長占比 |
|---|---:|---:|---:|---:|
'''
for label, r in distribution.iterrows():
    report += f'| {label} | {int(r["count"]):,} | {r.count_percent:.3f}% | {r.hours:.3f} | {r.time_percent:.3f}% |\n'
report += '''
83.06% 的片段短於 10 秒。30 秒以上只有 725 段（1.02%），其中 60 秒以上 262 段，120 秒以上 24 段。
若目標是長時間連續動作，建議增加自然連續錄製的長片段及動作轉換；以反覆拼接短片段不等同新增長動作資料。

![統計圖](overview.png)

## 重現

執行 `python analysis/bones-seed/analyze.py`，可重建本報告、CSV、JSON 與 PNG／SVG 圖表。
'''
(OUT/'report.md').write_text(report)
print(json.dumps(summary, ensure_ascii=False, indent=2))
print('Saved report, CSV statistics, summary JSON and PNG/SVG charts to', OUT)
