#!/bin/sh

curdate=`date +%Y%m%d`
basedir=/Users/user/PycharmProjects/pystocklib/examples/S-RIM/


exec_srim.sh

echo $curdate
#cd $basedir

ACTIVATE="cd /Users/user/PycharmProjects/pystocklib/venv/bin/activate"
source $ACTIVATE

cd $basedir

cmd1='/Users/user/PycharmProjects/pystocklib/venv/bin/python /Users/user/PycharmProjects/pystocklib/examples/S-RIM/getFnGuide.py TRUE TRUE FALSE'
$cmd1

cat $cmd1

cmd2='/Users/user/PycharmProjects/pystocklib/venv/bin/python /Users/user/PycharmProjects/pystocklib/examples/S-RIM/SrimDbUpdater.py'
$cmd2
