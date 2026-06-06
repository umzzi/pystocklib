#!/bin/sh

curdate=`date +%Y%m%d`
basedir=/Users/umzzi/dev/PycharmProjects/pystocklib/examples/S-RIM/
venvdir=/Users/umzzi/dev/PycharmProjects/pystocklib/venv


echo $curdate

source $venvdir/bin/activate

cd $basedir

cmd1="$venvdir/bin/python $basedir/getFnGuide.py TRUE TRUE FALSE"
$cmd1

cmd2="$venvdir/bin/python $basedir/SrimDbUpdater.py"
$cmd2

# 결과 CSV를 구글 드라이브(gdrive:S-RIM)에 자동 업로드 (rclone)
rclone=/opt/homebrew/bin/rclone
$rclone copy "$basedir/srim_my_daily/srim_hh_${curdate}.csv" gdrive:srim/ -v
if [ -f "$basedir/srim_my_daily/srim_hh_${curdate}_dividend.csv" ]; then
    $rclone copy "$basedir/srim_my_daily/srim_hh_${curdate}_dividend.csv" gdrive:srim/ -v
fi
