#!/bin/bash -xe

TWITCH_KEY=$(aws secretsmanager get-secret-value --secret-id twitch/i80unofficial | jq -r .SecretString)

exec ffmpeg -re \
-i https://0xcafe.tech/api/cooltrans/proxy/caltrans/D3/80_crystal_springs.stream/playlist.m3u8 \
-i https://0xcafe.tech/api/cooltrans/proxy/caltrans/D3/80_Whitmore_Grade_PLA80_WB.stream/playlist.m3u8 \
-i https://0xcafe.tech/api/cooltrans/proxy/caltrans/D3/80_Kingvale_PLA80_EB.stream/playlist.m3u8 \
-i https://0xcafe.tech/api/cooltrans/proxy/caltrans/D3/80_Kingvale_PLA80_WB.stream/playlist.m3u8 \
-i https://0xcafe.tech/api/cooltrans/proxy/caltrans/D3/80_Soda_Springs_NEV80_EB.stream/playlist.m3u8 \
-i https://0xcafe.tech/api/cooltrans/proxy/caltrans/D3/80_Donner_Summit_JWO_NEV80_EB.stream/playlist.m3u8 \
-i https://0xcafe.tech/api/cooltrans/proxy/caltrans/D3/80_Donner_Lake_Rd_JEO_NEV80_WB.stream/playlist.m3u8 \
-i https://0xcafe.tech/api/cooltrans/proxy/caltrans/D3/80_AG_Station_NEV80_EB.stream/playlist.m3u8 \
-i https://0xcafe.tech/api/cooltrans/proxy/caltrans/D3/80_JCT89S_NEV80_EB.stream/playlist.m3u8 \
-filter_complex "\
[0:v]scale=640:360[v0]; \
[1:v]scale=640:360[v1]; \
[2:v]scale=640:360[v2]; \
[3:v]scale=640:360[v3]; \
[4:v]scale=640:360[v4]; \
[5:v]scale=640:360[v5]; \
[6:v]scale=640:360[v6]; \
[7:v]scale=640:360[v7]; \
[8:v]scale=640:360[v8]; \
[v0][v1][v2][v3][v4][v5][v6][v7][v8]xstack=inputs=9:layout=0_0|640_0|1280_0|0_360|640_360|1280_360|0_720|640_720|1280_720:fill=black[out]" \
-map "[out]" \
-c:v libx264 -preset ultrafast -an \
-b:v 3000k -minrate 3000k -maxrate 3000k -bufsize 6000k -g 30 \
-f flv "rtmp://sea.contribute.live-video.net/app/${TWITCH_KEY}"
