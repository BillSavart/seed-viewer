#!/bin/bash
set -e
if [ ! -f /home/imlab/Desktop/Bill/bones-seed/metadata/seed_metadata_v004.parquet ]; then
    zenity --error --text='找不到內接 SSD 上的 BONES-SEED metadata。'
    exit 1
fi
systemctl --user restart bones-seed-viewer.service
for attempt in {1..30}; do
    if curl --silent --fail http://127.0.0.1:8666/ > /dev/null; then
        exec xdg-open http://127.0.0.1:8666/
    fi
    sleep 1
done
zenity --error --text='檢視器啟動失敗，請檢查 systemctl --user status bones-seed-viewer。'
