#!/bin/bash

delay=5

device="WS7in"

hostname="FramyZero"
wififile=$PWD"/wifi"
blfile=$wififile"/static"

if [ "$USER" != "root" ]
then
    echo "Please run this as root or with sudo"
    exit 2
fi

echo "127.0.0.1	$hostname" | sudo tee -a /etc/hosts
mkdir bluetooth
mkdir wifi
mkdir next

loading(){
    pid=$!
    spin='-\|/'
    i=0
    while kill -0 $pid 2>/dev/null
    do
    i=$(( (i+1) %4 ))
    printf "This might take a while! \r${spin:$i:1}"
    sleep .1
    done
    echo ""
}

echo "Installing dependencies"
apt-get update
apt-get upgrade -y --fix-missing
apt-get install cron -y
apt-get install cmake -y
apt-get install libopencv-dev -y
apt-get install python3-pip -y
apt-get install python3-pil -y
apt-get install samba screen python3 python3-pip -y
apt-get install libbluetooth3 python3-dev libdbus-1-dev libc6 libwrap0 pulseaudio-module-bluetooth libglib2.0-dev libcairo2-dev libgirepository1.0-dev -y
apt-get install libopenobex2 obexpushd -y
if [ $? -eq 0 ];
    then echo "Obex installed sucessfully!";
    else
        apt-get install libopenobex2 -y
        arch=$(dpkg --print-architecture)
        echo "Trying manuall installation!"
        wget "http://ports.ubuntu.com/pool/universe/o/obexpushd/obexpushd_0.11.2-1.1build2_$arch.deb"
        dpkg -i "obexpushd_0.11.2-1.1build2_$arch.deb"
        rm "obexpushd_0.11.2-1.1build2_$arch.deb";
fi
apt-get install --fix-broken -y

echo "Installing watchdog"
pip3 install watchdog
echo "Installing dbus-python"
pip3 install dbus-python
echo "Installing PyGObject"
pip3 install PyGObject
pip3 install RPi.GPIO
pip3 install spidev 
pip3 install filetype
pip3 install git+https://www.github.com/hbldh/hitherdither
pip3 install inky

echo "Creating network shared folder"
mkdir -m 2777 $wififile
mkdir -m 2777 "$wififile/static"
touch $PWD/.update_static

if [ ! -z $(grep "pi-share" "/etc/samba/smb.conf") ];
    then echo "Already created samba config";
    else
	line=$(cat $PWD/samba_config.txt)
        ESCAPED_PATH=$(printf '%s\n' "$wififile" | sed -e 's/[\/&]/\\&/g')
        line=$(echo "$line" | sed "s/WIFIFILE/$ESCAPED_PATH/g")
        echo "$line" | tee -a /etc/samba/smb.conf;
fi

echo "Setting Bluetooth device name"
cp $PWD/main.conf /etc/bluetooth/main.conf

if grep -q ' -C' "/etc/systemd/system/dbus-org.bluez.service";
    then echo "Already in compat mode";
    else
        echo "Set bluetoothd to compat mode"
        execnum=$(sed -n "/Exec/=" /etc/systemd/system/dbus-org.bluez.service)
        sed "$execnum s/.*/& -C/" /etc/systemd/system/dbus-org.bluez.service
        sed -i "$execnum s/.*/& -C/" /etc/systemd/system/dbus-org.bluez.service;
fi

if grep -q ' -C' "/etc/systemd/system/bluetooth.target.wants/bluetooth.service";
    then echo "Already in compat mode";
    else
        echo "Set bluetoothd to compat mode"
        execnum=$(sed -n "/Exec/=" /etc/systemd/system/bluetooth.target.wants/bluetooth.service)
        sed "$execnum s/.*/& -C/" /etc/systemd/system/bluetooth.target.wants/bluetooth.service
        sed -i "$execnum s/.*/& -C/" /etc/systemd/system/bluetooth.target.wants/bluetooth.service;
fi

if grep -q ' -C' "/lib/systemd/system/bluetooth.service";
    then echo "Already in compat mode";
    else
        echo "Set bluetoothd to compat mode"
        execnum=$(sed -n "/Exec/=" /lib/systemd/system/bluetooth.service)
        sed "$execnum s/.*/& -C/" /lib/systemd/system/bluetooth.service
        sed -i "$execnum s/.*/& -C/" /lib/systemd/system/bluetooth.service;
fi
echo "Adding startup commands"

delsym="d"
exitnum=$(echo "$(sed -n "/exit 0/=" /etc/rc.local)" | tail -n1)
sed -i "$exitnum$delsym" /etc/rc.local

ESCAPED_PATH=$(printf '%s\n' "$PWD" | sed -e 's/[\/&]/\\&/g')
line=$(sed "s/PWD/$ESCAPED_PATH/g" $PWD/boot_config.txt)
line=$(echo "$line" | sed "s/DEL/$delay/g")
ESCAPED_PATH=$(printf '%s\n' "$wififile" | sed -e 's/[\/&]/\\&/g')
line=$(echo "$line" | sed "s/WFILE/$ESCAPED_PATH/g")
ESCAPED_PATH=$(printf '%s\n' "$blfile" | sed -e 's/[\/&]/\\&/g')
line=$(echo "$line" | sed "s/BLFILE/$ESCAPED_PATH/g")

touch $PWD/boot.sh
if [ ! $? -eq 0 ];
    then
        rm $PWD/boot.sh
        touch $PWD/boot.sh;
fi
echo "$line" | sudo tee ./boot.sh

chmod +x $PWD/boot.sh
cp $PWD/boot.sh /usr/local/bin/framy.sh
chmod +x /usr/local/bin/framy.sh
cp $PWD/framy.service /etc/systemd/system/framy.service
chmod 640 /etc/systemd/system/framy.service
systemctl enable framy.service

bluetoothctl system-alias $hostname
hostnamectl set-hostname $hostname
hciconfig hci0 class 100100

#write out current crontab
crontab -l > mycron
#echo new cron into cron file
echo "@reboot touch $PWD/.update_static" >> mycron
echo "*/5 * * * * sh $PWD/update.sh" >> mycron
#install new cron file
crontab mycron
rm mycron

echo "#!/bin/bash" > update.sh
echo "python3 $PWD/FrameUpdater.py -f $wififile -d $device -s 0.5" >> update.sh
