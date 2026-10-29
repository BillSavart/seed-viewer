# BONES-SEED 本機 metadata 整理

本報告直接讀取本機 `seed_metadata_v004.parquet` 與完整 `seed_metadata_v002_temporal_labels.jsonl`。統計以本機檔案為準；秒數依本機 README 的 120 fps 換算，未逐一讀取動作檔確認幀率。

## 資料總覽

- 動作：142,220 筆；欄位：51 個。
- 原始動作：71,132 筆；鏡像動作：71,088 筆。
- 含鏡像總時長：288.32 小時；原始動作總時長：144.22 小時。
- 平均時長：7.30 秒；中位數：5.70 秒；範圍：0.575–180.14 秒。
- 50% 的動作時長介於 4.00–8.36 秒。
- 演員：522 位；拍攝日期：124 個，範圍 2021-05-31–2024-09-18。

## 八大分類（含鏡像）

| 分類 | 筆數 | 占比 |
|---|---:|---:|
| Locomotion | 74,488 | 52.38% |
| Communication | 21,493 | 15.11% |
| Interactions | 14,643 | 10.30% |
| Dances | 11,006 | 7.74% |
| Gaming | 8,700 | 6.12% |
| Everyday | 5,816 | 4.09% |
| Sport | 3,993 | 2.81% |
| Other | 2,081 | 1.46% |

## 二十個細分類（含鏡像）

| 分類 | 筆數 |
|---|---:|
| Basic Locomotion Neutral | 33,430 |
| Baseline | 22,878 |
| Gestures | 17,590 |
| Object Manipulation | 11,620 |
| Dancing | 11,006 |
| Object Interaction | 10,817 |
| Basic Locomotion Styles | 10,746 |
| Advanced Locomotion | 6,036 |
| Sports | 3,973 |
| Communication | 3,723 |
| Unusual Locomotion | 3,242 |
| Other | 2,081 |
| Consuming | 1,388 |
| Household | 1,318 |
| Stunts | 858 |
| Environments | 614 |
| Complex Actions | 540 |
| Looking and Pointing | 180 |
| Magic | 160 |
| Martial Arts | 20 |

## 51 個欄位

所有路徑欄位均相對於 `/home/imlab/Desktop/Bill/bones-seed/`。

### 動作識別與分類

| 欄位 | 本機型別 | 說明 |
|---|---|---|
| `move_name` | object | 唯一動作名稱 |
| `filename` | object | 不含副檔名的檔名；用來對應時間標註 |
| `move_duration_frames` | int64 | 影格數；依 README 以 120 fps 換算秒數 |
| `package` | object | 頂層動作分類 |
| `category` | object | 細項動作分類 |
| `is_neutral` | float64 | 是否為中性表演風格 |
| `is_mirror` | bool | 是否為左右鏡像版本 |
### 動作與身形檔案路徑

| 欄位 | 本機型別 | 說明 |
|---|---|---|
| `move_soma_uniform_path` | object | 標準身形 SOMA BVH 相對路徑 |
| `move_soma_uniform_shape_path` | object | 標準身形參數 NPZ 相對路徑 |
| `move_soma_proportional_path` | object | 演員身形比例 SOMA BVH 相對路徑 |
| `move_soma_proportional_shape_path` | object | 演員身形參數 NPZ 相對路徑 |
| `move_g1_path` | object | Unitree G1 動作 CSV 相對路徑 |
### 拍攝資訊

| 欄位 | 本機型別 | 說明 |
|---|---|---|
| `take_name` | object | 拍攝 take 名稱 |
| `take_actor` | object | 拍攝演員編號 |
| `take_org_name` | object | 原始 take 名稱 |
| `take_date` | int64 | 拍攝日期，YYMMDD |
| `take_day_part` | object | 拍攝日內分段 |
### 內容與文字標註

| 欄位 | 本機型別 | 說明 |
|---|---|---|
| `content_name` | object | 語意動作名稱 |
| `content_natural_desc_1` | object | 自然語言描述 1 |
| `content_natural_desc_2` | object | 自然語言描述 2 |
| `content_natural_desc_3` | object | 自然語言描述 3 |
| `content_natural_desc_4` | object | 自然語言描述 4 |
| `content_technical_description` | object | 技術性動作描述 |
| `content_short_description` | object | 簡短描述 1 |
| `content_short_description_2` | object | 簡短描述 2 |
| `content_all_rigplay_styles` | object | 表演風格標籤集合 |
| `content_uniform_style` | object | 統一表演風格標籤 |
| `content_type_of_movement` | object | 動作類型；部分值為複合標籤 |
| `content_body_position` | object | 身體姿勢 |
| `content_horizontal_move` | int64 | 是否含水平位移 |
| `content_vertical_move` | int64 | 是否含垂直位移 |
| `content_props` | object | 道具描述或 0 |
| `content_complex_action` | int64 | 是否為複合動作 |
| `content_repeated_action` | int64 | 是否包含重複動作 |
### 演員與身體尺寸

| 欄位 | 本機型別 | 說明 |
|---|---|---|
| `actor_uid` | object | 演員唯一編號 |
| `actor_height` | object | 身高分組標籤，非公分值 |
| `actor_height_cm` | int64 | 身高（cm） |
| `actor_foot_cm` | int64 | 腳長（cm） |
| `actor_collarbone_height_cm` | int64 | 鎖骨高度（cm） |
| `actor_collarbone_span_cm` | int64 | 鎖骨跨度（cm） |
| `actor_elbow_span_cm` | int64 | 手肘跨度（cm） |
| `actor_wrist_span_cm` | int64 | 手腕跨度（cm） |
| `actor_shoulder_span_cm` | int64 | README 標示 shoulder span（cm）；具體量測定義需另確認 |
| `actor_hips_height_cm` | int64 | 髖部高度（cm） |
| `actor_hips_bones_span_cm` | int64 | 髖骨跨度（cm） |
| `actor_knee_height_cm` | int64 | 膝蓋高度（cm） |
| `actor_ankle_height_cm` | int64 | 腳踝高度（cm） |
| `actor_weight_kg` | int64 | 體重（kg） |
| `actor_age_yr` | int64 | 年齡（歲） |
| `actor_gender` | object | 性別標籤 F／M |
| `actor_profession` | object | 職業／背景標籤 |

## 演員資料（依 actor_uid 去重）

- 性別標籤：M 269 位、F 253 位。
- 年齡（歲）：17–71，平均 29.92。
- 身高（cm）：145–199，平均 174.81。
- 體重（kg）：38–145，平均 71.86。
- 背景：actor 380 位、general 64 位、professional 43 位、dancer 24 位、stuntman 11 位。

## 實際動作範例

| 檔名 | 大分類／細分類 | 時長（秒） | 原始簡短描述 |
|---|---|---:|---|
| `body_check_001__A548` | Locomotion／Baseline | 31.41 | checking whole body |
| `drinking_bottle_idle_to_idle_R_001__A548` | Everyday／Consuming | 12.62 | from drinking while standing to standing |
| `extreme_repentance_R_001__A548` | Communication／Gestures | 13.84 | character is expressing extreme repentance |
| `grab_walk_ff_180_001__A548` | Interactions／Object Manipulation | 8.61 | character walks forward while grabbing something |
| `macarena_001__A545` | Dances／Dancing | 27.52 | macarena dance |
| `neutral_button press_001__A543` | Gaming／Object Interaction | 2.70 | pressing a button |
| `play_tennis_R_002__A533` | Sport／Sports | 12.95 | playing ground tennis |
| `clearing_ear_R_rubbing_hands_lasso_catch_pulling_R_001__A472` | Other／Other | 12.91 | clears ear using finger then rubs hands and throws lasso pull |

第一筆動作的完整 metadata：

```json
{
  "move_name": "body_check_001__A548",
  "filename": "body_check_001__A548",
  "move_duration_frames": 3769,
  "package": "Locomotion",
  "category": "Baseline",
  "is_neutral": 1.0,
  "is_mirror": false,
  "move_soma_uniform_path": "soma_uniform/bvh/240918/body_check_001__A548.bvh",
  "move_soma_uniform_shape_path": "soma_shapes/soma_base_fit_mhr_params.npz",
  "move_soma_proportional_path": "soma_proportional/bvh/240918/body_check_001__A548.bvh",
  "move_soma_proportional_shape_path": "soma_shapes/soma_proportion_fit_mhr_params/A548.npz",
  "move_g1_path": "g1/csv/240918/body_check_001__A548.csv",
  "take_name": "body_check_001",
  "take_actor": "A548",
  "take_org_name": "body_check_001",
  "take_date": 240918,
  "take_day_part": "_1",
  "content_name": "body_check",
  "content_natural_desc_1": "person touches and checks their whole body systematically from head to toes",
  "content_natural_desc_2": "person self-checks their body, touching from head to toe",
  "content_natural_desc_3": "individual examines themselves, touching body parts from head to toe",
  "content_natural_desc_4": "A person initially standing with both hands stretched sideways touches both their hands, chest, torso, and hips. Then they lean forward to touch the legs and straighten up again to stand in their initial posture.",
  "content_technical_description": "body self-marking, hands touching body parts from head to toes: fingers, hands, forearms, arms, head, chest, belly, hips, thighs, calves, toes, heel",
  "content_short_description": "checking whole body",
  "content_short_description_2": "body check",
  "content_all_rigplay_styles": "neutral",
  "content_uniform_style": "neutral",
  "content_type_of_movement": "standing",
  "content_body_position": "standing",
  "content_horizontal_move": 0,
  "content_vertical_move": 0,
  "content_props": "0",
  "content_complex_action": 0,
  "content_repeated_action": 0,
  "actor_uid": "A548",
  "actor_height": "M",
  "actor_height_cm": 171,
  "actor_foot_cm": 28,
  "actor_collarbone_height_cm": 138,
  "actor_collarbone_span_cm": 29,
  "actor_elbow_span_cm": 93,
  "actor_wrist_span_cm": 132,
  "actor_shoulder_span_cm": 175,
  "actor_hips_height_cm": 98,
  "actor_hips_bones_span_cm": 27,
  "actor_knee_height_cm": 50,
  "actor_ankle_height_cm": 12,
  "actor_weight_kg": 62,
  "actor_age_yr": 29,
  "actor_gender": "F",
  "actor_profession": "actor"
}
```

## 時間分段標註

- 142,220 筆 JSONL 紀錄，對應 142,220 個唯一 filename。
- 與主 metadata 的 filename 完全對應，涵蓋原始與鏡像動作。
- 共 352,703 個區段；平均每筆 2.48 個，範圍 1–78 個。
- `num_events` 與實際 events 數量不符：0 筆。
- `start_time`、`end_time` 單位為秒；`description` 描述該時間區段的動作。

實際第一筆標註：

```json
{
  "filename": "inside_door_knob_left_side_open_R_002__A512",
  "num_events": 3,
  "events": [
    {
      "start_time": 0.0,
      "end_time": 1.88,
      "description": "A person rotates the door knob with their right hand."
    },
    {
      "start_time": 1.88,
      "end_time": 3.53,
      "description": "A person opens the door outward from the inside, holding the knob and then lowers their hand."
    },
    {
      "start_time": 3.53,
      "end_time": 4.83,
      "description": "A person is standing idle and slightly moving their right hand."
    }
  ]
}
```

## 使用時要注意

- 原始與鏡像是高度相關的資料；若用來切分訓練／驗證／測試集，宜讓同一原始動作與鏡像落在同一集合。
- 51 個欄位未發現 null／NaN 或空字串；這不代表所有標註語意均正確。
- `content_type_of_movement` 有 1,637 筆帶有前後空白，例如 `standing `；統計或篩選前可先 `.str.strip()`。身體姿勢也有 `standing, croaching` 等拼字變體。
- 文字描述會重複出現在多個動作，不能當成唯一識別碼。
- 本機 README 混用 v002／v003 與舊欄位名；實際主表是 v004，G1 路徑欄位為 `move_g1_path`。
- 本機有 `soma_uniform.tar.gz`、`soma_proportional.tar.gz`、`g1.tar.gz`；對應動作資料夾尚未出現在根目錄，第一筆三種動作路徑亦不存在。進一步檢查發現，既有 Viewer 已有 SOMA Uniform／G1 的壓縮檔索引，可以直接讀取指定動作，無須解壓整套資料。單筆 BVH 取出與播放範例見 `bones-example/README.md`。
- `actor_shoulder_span_cm` 的第一筆數值為 175；不要直接假設它代表一般解剖學肩寬，應先確認量測定義。
