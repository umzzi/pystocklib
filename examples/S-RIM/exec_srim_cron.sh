#!/bin/sh
# crontab 등록용 래퍼: exec_srim.sh(크롤링→DB적재→드라이브 업로드)를 실행하고 로그를 남긴다.
# cron 예) 0 18 * * 1-5 /bin/sh /Users/umzzi/dev/PycharmProjects/pystocklib/examples/S-RIM/exec_srim_cron.sh

basedir=/Users/umzzi/dev/PycharmProjects/pystocklib/examples/S-RIM
logdir=$basedir/logs
curdate=`date +%Y%m%d`

mkdir -p "$logdir"
sh "$basedir/exec_srim.sh" >> "$logdir/srim_$curdate.log" 2>&1
