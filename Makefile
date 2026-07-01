all:



VBoxManage hostonlyif create
VBoxManage hostonlyif ipconfig vboxnet0 --ip 192.168.56.1 --netmask 255.255.255.0

VBoxManage createvm --name "boot2root" --ostype Ubuntu_64 --register
VBoxManage modifyvm "boot2root" --memory 1024 --vram 16
VBoxManage modifyvm "boot2root" --boot1 dvd --boot2 none
VBoxManage storagectl "boot2root" --name "IDE" --add ide
VBoxManage storageattach "boot2root" \
  --storagectl "IDE" --port 0 --device 0 \
  --type dvddrive --medium "BornToSecHackMe-v1.1.iso"
VBoxManage modifyvm "boot2root" --nic1 hostonly --hostonlyadapter1 vboxnet0
VBoxManage startvm "boot2root" --type headless

