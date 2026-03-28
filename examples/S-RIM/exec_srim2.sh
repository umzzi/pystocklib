#!/bin/sh

curdate=`date +%Y%m%d`
echo $curdate

# 스크립트 위치 기준으로 basedir 자동 설정
basedir="$(cd "$(dirname "$0")" && pwd)"
cd "$basedir"

python getFnguide2.py TRUE TRUE FALSE

