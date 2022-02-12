#!/bin/bash

while IFS= read -r line; do

    ## test line contenst and parse as required
    [[ "$line" =~ Address ]] && mac=${line##*ss: }
    [[ "$line" =~ \(Channel ]] && { chn=${line##*nel }; chn=${chn:0:$((${#chn}-1))}; }
    [[ "$line" =~ Frequen ]] && { frq=${line##*ncy:}; frq=${frq%% *}; }
    [[ "$line" =~ Quality ]] && { 
        qual=${line##*ity=}
        qual=${qual%% *}
        lvl=${line##*evel=}
        lvl=${lvl%% *}
    }
    [[ "$line" =~ Encrypt ]] && enc=${line##*key:}
    [[ "$line" =~ ESSID ]] && {
        essid=${line##*ID:}

#essid="${essid#\"}"
essid=$(echo "$essid" | tr -d '"')

essid=$(echo "$essid" | sed -e 's/\\x00//g')
essid=$(echo "$essid" | sed -e 's/\\xe2\\x80\\x99/'\''/g')
essid=$(echo "$essid" | sed -e 's/\\xE2\\x80\\x99/'\''/g')

if [ -z "${essid}" ]; then

essid="hidden"

fi

essid=$(echo "$essid" | sed -e 's/ /\\ /g')

curl_message="${curl_message}scan,mac=$mac,essid=$essid,frq=$frq,channel=$chn level=$lvl
"  # output after ESSID
    }

done

curl -i -XPOST "http://influxdb01.tylephony.com:8086/write?db=wifiscan" --data-binary "${curl_message}"
