# Setup steps

# Using the bash installer

## 1: Install operationg system onto the device
### Raspberry Pi Zero
The Raspberry Pi OS images can be found under: 
https://www.raspberrypi.com/software/

### Banana Pi 
The Armbian images can be found under: 
https://armbian.tnahosting.net/archive/bananapim2zero/archive/

For installation of the operating systems we recommend the use of the rpi-imager.
Depending on the OS choosen different steps need to be taken to connect to the device. For Armbian specific steps refer to https://docs.armbian.com/User-Guide_Getting-Started/#how-to-boot.

## 2: Connect via ssh

Connect to the device via ssh by running `ssh pi@*hostname*` or `ssh pi@*IP*`. The hostname of the device is `raspberrypi.local` for Raspberry Pi OS, but can be changed using rpi-imager. The default login information for Raspberry Pi OS are user: `pi` and password: `raspberry` unless changed with rpi-imager.

## 3: Running the installer
For installation of the CatroPi software git is required. Before installing git it is recommended to keep the system up-to-date by running `sudo apt-get update`and `sudo apt-get upgrade`. Installing git can be done with `sudo apt-get install git`. 
After installing git the repository can be cloned with `git clone https://github.com/StofflR/CatroZero.git`. Change to the directory of the cloned repository `cd CatroZero`. 
Create a virtual python environment for the setup with `python3 -m venv .venv`. To install the software run `/path/to/venv/bin/python3 install.py`, the execution of the script will take a while as all the necessary dependencies need to be installed and the required storage will need to be allocated. 
Run `/path/to/venv/bin/python3 install.py --help` for possible configuration options, like the hostname to use, delay till replug, etc.. 

