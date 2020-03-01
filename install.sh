#!/bin/bash
set -eo pipefail

INSTALL_DIR=/opt/rf2mqtt

# Parse args
while [[ $# -gt 0 ]] ; do
    opt="$1";
    shift;
    case "$opt" in
        "-v" )
            set -x ;;
        "-f" )
            clean_start=1 ;;
        *)
            echo "Usage $0 [-v] (verbose) [-f] (fresh start)";;
    esac
done

#Useful variables
working_dir=$(dirname $(readlink -f $0))
venv_dir=$INSTALL_DIR/venv

# Helper functions
function check_dep () {
    if ! which $1; then
        echo "You need $1 to use this tool"
        return 1
    fi
}

function cleanup () {
    if [[ $(docker ps -a -q -f name=mosq |wc -l) == 1 ]] ; then 
        docker kill mosq || true
        docker rm mosq
    fi
    rm -rf $venv_dir/*
}

function install_venv () {
    sudo mkdir -p $venv_dir
    current_user=$UID
    sudo chown $UID $venv_dir
    virtualenv -p python3 $venv_dir
    $venv_dir/bin/pip install -r $working_dir/requirements.txt
}

for dep in docker python3 virtualenv systemctl; do
    check_dep $dep
done

[[ $clean_start == 1 ]] && cleanup
[[ -d venv ]] || install_venv

docker run -d --restart=always --name mosq -p 1883:1883 -p 9001:9001 -v $working_dir/mosquitto.conf:/mosquitto/config/mosquitto.conf eclipse-mosquitto
sudo systemctl stop rf2mqtt.service || true
sudo cp rf2mqtt.service /etc/systemd/system/
sudo ln -s $working_dir/rf2mqtt.py /usr/local/bin/rf2mqtt
sudo systemctl enable rf2mqtt.service
sudo systemctl daemon-reload
sudo systemctl start rf2mqtt.service

echo "install script is done. Checking status of the service:"
systemctl status rf2mqtt.service

echo "to test that it works, you can run $workdir/mqtt_echo.py and press your remote control buttons"
