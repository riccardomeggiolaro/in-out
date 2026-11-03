#! /bin/sh

if [ -d /sys/bus/usb/drivers/usb ]; then
	search_dir=/sys/bus/usb/drivers/usb
fi

for entry in "$search_dir"/*
do
	case $entry in
	.);;
	..);;
	*)
		for entry2 in "$entry"/*
		do
			if [ "${entry2##*/}" = "idVendor" ]; then
				idVendor=`cat $search_dir/${entry##*/}/${entry2##*/}`
				if [ "$idVendor" = "14e1" ]; then
					product=`cat $search_dir/${entry##*/}/product`
					echo "Enable wakeup for "$product
					echo "enabled" >  $search_dir/${entry##*/}/power/wakeup
				fi
			fi
		done
	;;
	esac
done

