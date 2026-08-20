SUDO=`which sudo`
echo "========================================"
echo "       PenMount XInput Uninstaller      "
echo "========================================"


echo "(1) Remove device driver configurations"
if [ -f /etc/X11/xorg.conf.d/99-input-penmount.conf ]; then
	$SUDO rm /etc/X11/xorg.conf.d/99-input-penmount.conf
fi

if [ -f /etc/X11/xorg.conf.d/999-input-penmount.conf ]; then
	$SUDO rm /etc/X11/xorg.conf.d/999-input-penmount.conf
fi

if [ -f /usr/share/X11/xorg.conf.d/99-input-penmount.conf ]; then
	$SUDO rm /usr/share/X11/xorg.conf.d/99-input-penmount.conf
fi

if [ -f /usr/share/X11/xorg.conf.d/999-input-penmount.conf ]; then
	$SUDO rm /usr/share/X11/xorg.conf.d/999-input-penmount.conf
fi

if [ -f /usr/lib/X11/xorg.conf.d/99-input-penmount.conf ]; then
	$SUDO rm /usr/lib/X11/xorg.conf.d/99-input-penmount.conf
fi

if [ -f /usr/lib/X11/xorg.conf.d/999-input-penmount.conf ]; then
	$SUDO rm /lib/share/X11/xorg.conf.d/999-input-penmount.conf
fi

if [ -f /usr/share/hal/fdi/policy/20thirdparty/99-x11-penmount.fdi ]; then
	$SUDO rm /usr/share/hal/fdi/policy/20thirdparty/99-x11-penmount.fdi
fi

echo "(2) Remove device driver binary files"
$SUDO killall pm-tchsrv pm-gcalib gPen gDraw pm-setup pm-xdraw 
if [ -f /usr/lib/xorg/modules/input/penmount_drv.so ]; then
	$SUDO rm /usr/lib/xorg/modules/input/penmount_drv.so
fi

if [ -f /usr/sbin/pm-gcalib ]; then
	$SUDO rm /usr/sbin/pm-gcalib
fi

if [ -f /usr/sbin/gPen ]; then
	$SUDO rm /usr/sbin/gPen
fi

if [ -f /usr/sbin/gCal ]; then
	$SUDO rm /usr/sbin/gCal
fi

if [ -f /usr/sbin/gDraw ]; then
	$SUDO rm /usr/sbin/gDraw
fi

if [ -f /usr/sbin/pm-setup ]; then
	$SUDO rm /usr/sbin/pm-setup
fi

if [ -f /usr/sbin/pm-xdraw ]; then
	$SUDO rm /usr/sbin/pm-xdraw
fi

if [ -d /usr/sbin/gPen-wrapper ]; then
	$SUDO rm -rf /usr/sbin/gPen-wrapper
fi

if [ -d /usr/sbin/gCal-wrapper ]; then
	$SUDO rm -rf /usr/sbin/gCal-wrapper
fi

if [ -d /usr/sbin/pm-tchsrv ]; then
	$SUDO rm -rf /usr/sbin/pm-tchsrv
fi

echo "(3) Remove device driver assitance services"
if [ -f /etc/systemd/system/penmount-serio.service ]; then
	$SUDO rm /etc/systemd/system/penmount-serio.service
fi

if [ -f /lib/systemd/system/penmount-serio.service ]; then
	$SUDO rm /lib/systemd/system/penmount-serio.service
fi

if [ -f /lib/systemd/system/enable-wakeup.service ]; then
	$SUDO systemctl disable enable-wakeup.service
	$SUDO rm /lib/systemd/system/enable-wakeup.service
fi

echo "(4) Remove device driver desktop items"
if [ -f /usr/share/applications/penmount.desktop ]; then
	$SUDO rm /usr/share/applications/penmount.desktop
fi

if [ -f /usr/share/pixmaps/penmount.png ]; then
	$SUDO rm /usr/share/pixmaps/penmount.png
fi

if [ -f /usr/share/gnome-menus/update-gnome-menus-cache ]; then
	/usr/share/gnome-menus/update-gnome-menus-cache /usr/share/applications > ~/desktop.en_US.utf8.cache
	$$SUDO mv ~/desktop.en_US.utf8.cache /usr/share/applications/desktop.en_US.utf8.cache
fi

if [ -d /etc/penmount ]; then
	$SUDO rm -rf /etc/penmount
fi

if [ -f /etc/udev/rules.d/99-penmount-hidraw.rules ]; then
	$SUDO rm /etc/udev/rules.d/99-penmount-hidraw.rules
fi

if [ -d /usr/share/penmount ]; then
	$SUDO rm -rf /usr/share/penmount/penmount.png
fi

if [ -f /lib/systemd/system-sleep/system-sleep-penmount.sh ]; then
    $SUDO rm /lib/systemd/system-sleep/system-sleep-penmount.sh
fi

$SUDO sed -i.bak 's:/usr/sbin/pm-tchsrv::g' /etc/rc.local

echo "========================================"
echo "   PenMount XInput Uninstall Finished ! "
echo "========================================"
echo "[Installer] Please restart the system to make changes take effect !"

