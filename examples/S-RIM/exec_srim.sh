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
