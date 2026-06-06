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

# 결과 CSV를 구글 드라이브(gdrive:srim)에 구글 시트 문서로 변환 업로드 (rclone)
# --drive-import-formats csv : 업로드 시 CSV → Google Sheets 네이티브 문서로 변환
rclone=/opt/homebrew/bin/rclone
$rclone copy "$basedir/srim_my_daily/srim_hh_${curdate}.csv" gdrive:srim/ --drive-import-formats csv --drive-export-formats csv -v
if [ -f "$basedir/srim_my_daily/srim_hh_${curdate}_dividend.csv" ]; then
    $rclone copy "$basedir/srim_my_daily/srim_hh_${curdate}_dividend.csv" gdrive:srim/ --drive-import-formats csv --drive-export-formats csv -v
fi
