while true; do
iwlist wlan0 scan | ./parse.sh
  sleep 5
done
