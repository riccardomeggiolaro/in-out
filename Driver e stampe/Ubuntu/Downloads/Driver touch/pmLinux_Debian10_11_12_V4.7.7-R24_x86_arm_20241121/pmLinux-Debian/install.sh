#!/bin/bash

filetime="$(date +%m%d%H%M%S)"
SUDO=`which sudo`
INSTALL=`which install`
ROOT_INSTALL=$INSTALL' -o root -g root'
SYSTEMDIR=/usr/sbin
INSTALLDIR=/usr/share/penmount
ARCH=`uname -m`

if [ "$SUDO_USER" != "" ]; then
SUDO_HOME=`sudo -u "$SUDO_USER" sh -c 'echo $HOME'`
fi

if [ -f /var/log/Xorg.0.log ]; then
	INPUTABI=`cat /var/log/Xorg.0.log | grep "X.Org XInput driver :" | awk -F ': ' '{print $2}'`
elif [ -f $HOME/.local/share/xorg/Xorg.0.log ]; then
	INPUTABI=`cat $HOME/.local/share/xorg/Xorg.0.log | grep "X.Org XInput driver :" | awk -F ': ' '{print $2}'`
elif [ -f $SUDO_HOME/.local/share/xorg/Xorg.0.log ]; then
	INPUTABI=`cat $SUDO_HOME/.local/share/xorg/Xorg.0.log | grep "X.Org XInput driver :" | awk -F ': ' '{print $2}'`
elif [ $UID == 0 ]; then
	# If run in root
	for USERHOME in /home/*; do
		if [ -f $USERHOME/.local/share/xorg/Xorg.0.log ]; then
			INPUTABI=`cat $USERHOME/.local/share/xorg/Xorg.0.log | grep "X.Org XInput driver :" | awk -F ': ' '{print $2}'`
		fi
	done
	if [ "$INPUTABI" == "" ]; then
		echo "* {WARNING} Please run installer in normal user mode !"
	fi
fi

if [ "$ARCH" == "x86_64" ]; then
	SRC="x86_64"
	LIB="lib64"
elif [ "$ARCH" == "mips64" ]; then
	SRC="mips64"
	LIB="lib64"
elif [ "$ARCH" == "aarch64" ]; then
	SRC="aarch64"
	LIB="lib64"
elif [ "$ARCH" == "armv7l" ]; then
	SRC="armhf"
	LIB="lib"
elif [ "$ARCH" == "riscv64" ]; then
	SRC="riscv64"
	LIB="lib"
else
	SRC="i686"
	LIB="lib"
fi

if [ "$XDG_SESSION_TYPE" == "wayland" ]; then
	echo "Please run installer in Xorg mode !"
	exit
fi

if [ "$INPUTABI" == "" ]; then
	cd $SRC
	for DRIVERABI in *; do
		if [ -f $DRIVERABI/penmount_drv.so ]; then
			INPUTABI=$DRIVERABI
			((ABICOUNT += 1))
		fi
	done
	if [ $ABICOUNT -gt 1 ]; then
		echo -n "Available PenMount device driver : "
		for DRIVERABI in *; do
			if [ -f "$DRIVERABI/penmount_drv.so" ]; then
				echo -n $DRIVERABI
				echo -n " ; "
			fi
		done
		echo -n "Please select Input ABI version : "
		read INPUTABI
	else
		echo "Using PenMount device driver : $INPUTABI"
	fi
	if [ ! -f "$INPUTABI/penmount_drv.so" ]; then
		echo "* {ERROR} No compatible device driver found !"
		exit
	fi
	cd ..
fi

echo "========================================"
echo "        PenMount X Installation         "
echo "========================================"

echo "[Installer] Stopping PenMount Utilities ..."
$SUDO killall -q gDraw gCal gPen gPen3 pm-gcalib pmsAttach inputattach

if [ -f /etc/systemd/system/penmount-serio.service ]; then
$SUDO rm /etc/systemd/system/penmount-serio.service
fi
if [ -f /lib/systemd/system/penmount-serio.service ]; then
$SUDO rm /lib/systemd/system/penmount-serio.service
fi

if [ -f /usr/bin/systemctl ] || [ -f /bin/systemctl ]; then
	$SUDO systemctl daemon-reload
fi

if [ -f /usr/lib/i386-linux-gnu/libudev.so ] && [ ! -f /usr/lib/i386-linux-gnu/libudev.so.0 ]; then
	/usr/lib/i386-linux-gnu/libudev.so /usr/lib/i386-linux-gnu/libudev.so.0
fi

echo "[Installer] Copying PenMount Utilities ..."
if [ ! -d $INSTALLDIR ]; then
	$SUDO mkdir $INSTALLDIR
fi
$SUDO $ROOT_INSTALL $SRC/pm-setup             $SYSTEMDIR
$SUDO $ROOT_INSTALL $SRC/gCal                 $SYSTEMDIR
$SUDO $ROOT_INSTALL $SRC/pm-xdraw             $SYSTEMDIR
if [ -f $SRC/pm-wcalib ]; then
$SUDO $ROOT_INSTALL $SRC/pm-wcalib            $SYSTEMDIR
fi
if [ -f $SRC/pm-gcalib ]; then
$SUDO $ROOT_INSTALL $SRC/pm-gcalib            $SYSTEMDIR
fi
if [ -f $SRC/pm-gcalib2 ]; then
$SUDO $ROOT_INSTALL $SRC/pm-gcalib2           $SYSTEMDIR
fi
$SUDO $ROOT_INSTALL $SRC/gDraw                $SYSTEMDIR
$SUDO $ROOT_INSTALL $SRC/gPen                 $SYSTEMDIR
if [ -f $SRC/gPen3 ]; then
$SUDO $ROOT_INSTALL $SRC/gPen3                $SYSTEMDIR
fi
$SUDO $ROOT_INSTALL -m 4755 $SRC/gPen-wrapper $SYSTEMDIR
$SUDO $ROOT_INSTALL -m 4755 $SRC/gCal-wrapper $SYSTEMDIR
$SUDO $ROOT_INSTALL $SRC/inputattach          $INSTALLDIR

echo "[Installer] Copying PenMount Resource Files..."
$SUDO $ROOT_INSTALL penmount.png              $INSTALLDIR
$SUDO $ROOT_INSTALL README                    $INSTALLDIR

$SUDO $ROOT_INSTALL penmount48.png   /usr/share/pixmaps/penmount.png
$SUDO $ROOT_INSTALL penmount.desktop /usr/share/applications

if [ ! -f /lib/modules/`uname -r`/kernel/drivers/input/touchscreen/penmount.ko.xz  ] && [ ! -f /lib/modules/`uname -r`/kernel/drivers/input/touchscreen/penmount.ko.zst  ]; then
	if [ -f ./modules/`uname -r`/penmount.ko.xz ]; then
		echo "[Installer] Copy serial kernel driver ..."
		$SUDO cp ./modules/`uname -r`/penmount.ko.xz /lib/modules/`uname -r`/kernel/drivers/input/touchscreen
	fi
fi

if [ -f /lib/modules/`uname -r`/kernel/drivers/input/touchscreen/penmount.ko.xz  ] || [ -f /lib/modules/`uname -r`/kernel/drivers/input/touchscreen/penmount.ko.zst  ] ; then
	$SUDO depmod
else
	echo "{INFO} PenMount serial driver not found !"
fi

echo "[Installer] Setting up System ..."

if [ ! -d /etc/penmount ]; then
	$SUDO mkdir /etc/penmount
fi
$SUDO chmod 777 /etc/penmount

if [ -d screen ]; then
	$SUDO cp -r screen /etc/penmount
fi

if [ -f ./penmount.dat ]; then
	$SUDO cp ./penmount.dat     /etc/penmount
fi

if [ -f ./beep.wav ]; then
	$SUDO cp ./beep.wav     /etc/penmount
fi


if [ -d ./locale ]; then
	$SUDO cp -r ./locale /usr/share
fi

if [ -f /usr/share/gnome-menus/update-gnome-menus-cache ]; then
	/usr/share/gnome-menus/update-gnome-menus-cache /usr/share/applications > ~/desktop.en_US.utf8.cache
	$SUDO mv ~/desktop.en_US.utf8.cache /usr/share/applications/desktop.en_US.utf8.cache
fi

echo "[Installer] Setting up X Server ..."

if [ -d /etc/X11/xorg.conf.d ]; then
    $SUDO rm /etc/X11/xorg.conf.d/*penmount*
fi
if [ -d /usr/share/X11/xorg.conf.d ]; then
    $SUDO rm /usr/share/X11/xorg.conf.d/*penmount*
fi
if [ -d /usr/lib/X11/xorg.conf.d ]; then
    $SUDO rm /usr/lib/X11/xorg.conf.d/*penmount*
fi

if [ -d /usr/share/hal/fdi/policy/20thirdparty ]; then
    $SUDO rm /usr/share/hal/fdi/policy/20thirdparty/*penmount*
fi

if [ ! -d /etc/X11/xorg.conf.d ] && [ ! -d /usr/share/X11/xorg.conf.d ] && [ ! -d /usr/share/X11/xorg.conf.d ]; then
	$SUDO mkdir /usr/share/X11/xorg.conf.d
fi

if [ "$1" = "-usb" ]; then
$SUDO /usr/sbin/pm-setup -s -d0
elif [ "$1" = "-m" ]; then
$SUDO /usr/sbin/pm-setup -m
elif [ "$1" = "-svc" ]; then
$SUDO /usr/sbin/pm-setup -s -svc
else
$SUDO /usr/sbin/pm-setup -s
fi

echo "[Installer] Copying PenMount X Input module file : " $INPUTABI

if [ -d /usr/$LIB/xorg/modules/input ] ; then 
	$SUDO find /usr/$LIB/xorg/modules/input -name penmount_drv.so -type f -delete
	if [ -f $SRC/$INPUTABI/penmount_drv.so ] ; then
		$SUDO $ROOT_INSTALL $SRC/$INPUTABI/penmount_drv.so /usr/$LIB/xorg/modules/input
	elif [ -f $SRC/penmount_drv.so ] ; then
		$SUDO $ROOT_INSTALL $SRC/penmount_drv.so /usr/$LIB/xorg/modules/input
	else
		echo "[Installer] ERROR! Cannot find suitable PenMount X Input module for the target system !"
	fi
elif [ -d /usr/lib/xorg/modules/input ] ; then
	$SUDO find /usr/lib/xorg/modules/input -name penmount_drv.so -type f -delete
	if [ -f $SRC/$INPUTABI/penmount_drv.so ] ; then
		$SUDO $ROOT_INSTALL $SRC/$INPUTABI/penmount_drv.so /usr/lib/xorg/modules/input
	elif [ -f $SRC/penmount_drv.so ] ; then
		$SUDO $ROOT_INSTALL $SRC/penmount_drv.so /usr/lib/xorg/modules/input
	else
		echo "[Installer] ERROR! Cannot find suitable PenMount X Input module for the target system !"
	fi
else
	echo "[Installer] Cannot find a proper X Input module directory !"
fi

if [ -f enable-wakeup-usb.sh ]; then
	$SUDO $ROOT_INSTALL enable-wakeup-usb.sh /etc/penmount/
fi

if [ -f enable-wakeup.service ]; then
	$SUDO $ROOT_INSTALL enable-wakeup.service /etc/systemd/system
fi

if [ -f /etc/systemd/system/enable-wakeup.service ]; then
	if [ -f /usr/bin/systemctl ] || [ -f /bin/systemctl ]; then
		$SUDO systemctl enable enable-wakeup.service
	fi
fi

if [ -d /lib/systemd/system-sleep ] && [ -f system-sleep-penmount.sh ] ; then
	$SUDO $ROOT_INSTALL system-sleep-penmount.sh /lib/systemd/system-sleep
fi

if [ -f 99-penmount-hidraw.rules ]; then
	$SUDO $ROOT_INSTALL 99-penmount-hidraw.rules /etc/udev/rules.d
fi

if [ -f 99-input-penmount.conf ]; then
	if [ -d /etc/X11/xorg.conf.d ]; then
		$SUDO $ROOT_INSTALL 99-input-penmount.conf /etc/X11/xorg.conf.d
	fi
	if [ -d /usr/share/X11/xorg.conf.d ]; then
		$SUDO $ROOT_INSTALL 99-input-penmount.conf /usr/share/X11/xorg.conf.d
	fi
	if [ -d /usr/lib/X11/xorg.conf.d ]; then
		$SUDO $ROOT_INSTALL 99-input-penmount.conf /usr/lib/X11/xorg.conf.d
	fi
	if [ -d /usr/lib64/X11/xorg.conf.d ]; then
		$SUDO $ROOT_INSTALL 99-input-penmount.conf /usr/lib64/X11/xorg.conf.d
	fi
	if [ -d /usr/share/vivante/X11/xorg.conf ]; then
		$SUDO $ROOT_INSTALL 99-input-penmount.conf /usr/share/vivante/X11/xorg.conf
	fi
fi

if [ -d /usr/share/vivante/X11/xorg.conf ] && [ -f /usr/share/X11/xorg.conf.d/999-input-penmount.conf ] ; then
	$SUDO $ROOT_INSTALL /usr/share/X11/xorg.conf.d/999-input-penmount.conf /usr/share/vivante/X11/xorg.conf
fi

if [ -f /etc/systemd/system/penmount-serio.service ]; then
	$SUDO systemctl start penmount-serio
elif [ -f /lib/systemd/system/penmount-serio.service ]; then
	$SUDO systemctl start penmount-serio
fi

echo "========================================"
echo "    PenMount Installation Finished !    "
echo "========================================"
echo "[Installer] Please restart the system to make changes take effect !"

