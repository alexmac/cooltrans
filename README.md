# cooltrans

The backends for the caltrans cctv streams are flaky - some are slow and at least one IP in their loadbalancer returns spurious 403s - this proxy returns a response from the first of their IPs to provide valid data and also returns info about the locations.

Try these curls to see which gives you a 200 vs a 403:

curl -v --resolve wzmedia.dot.ca.gov:443:149.136.36.35 \
https://wzmedia.dot.ca.gov/D3/5_Pocket_Rd_OC_SAC5_SB.stream/playlist.m3u8

curl -v --resolve wzmedia.dot.ca.gov:443:149.136.20.16 \
https://wzmedia.dot.ca.gov/D3/5_Pocket_Rd_OC_SAC5_SB.stream/playlist.m3u8

curl -v --resolve wzmedia.dot.ca.gov:443:149.136.20.13 \
https://wzmedia.dot.ca.gov/D3/5_Pocket_Rd_OC_SAC5_SB.stream/playlist.m3u8

curl -v --resolve wzmedia.dot.ca.gov:443:149.136.36.37 \
https://wzmedia.dot.ca.gov/D3/5_Pocket_Rd_OC_SAC5_SB.stream/playlist.m3u8
