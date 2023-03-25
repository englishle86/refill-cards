#!/bin/bash

#cat upc_2021.txt | xargs -i -n 1 zint -b 34 --scale=1 --output=zint_out/{}.svg -d {}
#ls zint_out | xargs -i -n 1 --verbose inkscape -z zint_out/{} -e barcode_png_out/{}.png

for CODE in $(cat upc_2021.txt); do
  echo "Fetching $CODE"
  curl -s "http://www.barcode-generator.org/zint/api.php?bc_number=34&bc_data=$CODE" \
    -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:92.0) Gecko/20100101 Firefox/92.0' \
    -H 'Accept: image/avif,image/webp,*/*' -H 'Accept-Language: en-US,en;q=0.5' --compressed \
    -H 'Connection: keep-alive' -H 'Referer: http://www.barcode-generator.org/' -H 'Sec-GPC: 1' \
    -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' -o new_barcodes/$CODE.png
  WAIT=$((1 + $RANDOM % 8))
  echo "Sleeping $WAIT seconds"
  sleep $WAIT
done
