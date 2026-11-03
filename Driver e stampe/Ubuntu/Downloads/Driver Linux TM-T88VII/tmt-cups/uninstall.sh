#!/bin/bash

#set -x
LC_ALL=C
export LC_ALL

# Driver name
drivername="TM/BA Series Printer Driver for Linux"
driverver="Ver.1.4.1"
package_name="tmt-cups-1.4.1.0"

# Uninstall target
target_packages="
    tmt-cups
    tmt-cups-backend
    EPSON-Port-Communication-Service
"

# Interval (sec)
sleep_sec=0


version ()
{
    cat <<EOF
`basename $0`  for "${drivername}"  ${driverver}
  Copyright (C) 2010-2013 Seiko Epson Corporation. All rights reserved.

EOF
}

press_enter_key ()
{
    echo -n "Press the Enter key."
    read REPLY
}

usage ()
{
cat <<EOF

Package uninstaller for "${drivername}"
Target Package:${package_name}

usage: `basename $0` [option]

  option:
	-t | --test    Test mode          (do not uninstall)
	-h | --help    Show help message  (do not uninstall)
	-u | --usage   Show usage message (do not uninstall)
	-v | --version Show version info  (do not uninstall)

uninstalled packages:  ${target_packages}

EOF
}

# execute simple optional action, setting TEST option flag
TEST="no"
for a in $* ; do
    case "$a" in
		"-t" | "--test"    ) TEST="yes" ;;
		"-h" | "--help"    ) version ; usage ; exit 0 ;;
		"-u" | "--usage"   )           usage ; exit 0 ;;
		"-v" | "--version" ) version ;         exit 0 ;;
		"--") break ;;
		*) echo "[ERROR] Unknown option."; exit 255 ;;
    esac
done

check_command ()
{
    which "$1" 1>/dev/null 2>&1
}

# check package management system.
default_packager=""

for cmd in rpm dpkg ; do
    check_command $cmd
    if test $? -eq 0 ; then
		default_packager=$cmd
    fi
done
if test -z ${default_packager} ; then
    echo "[ERROR] Fatal error."
    press_enter_key
    exit 255
fi

# check installed package.
uninstaller=""

for cmd in rpm dpkg ; do
    check_command $cmd
    if test $? -eq 0 ; then
		if test "rpm" = "$cmd" ; then
			option="-q"
		else
			option="-l"
		fi
		for package in ${target_packages} ; do
			$cmd ${option} ${package} 1>/dev/null 2>&1
			if test $? -eq 0 ; then
			uninstaller=$cmd
			break
			fi
		done
		test "" != "${uninstaller}" && break
    fi
done

if test "" = "${uninstaller}" ; then
    uninstaller=${default_packager}
fi

# Change root.
if test 0 -ne `id -u`; then
    echo "Running the sudo command..."
    sudo $0 $*
    result=$?
    if test 1 -eq $result; then
		echo ""
		echo "[ERROR] The sudo command failed."
		echo "[ERROR] Please execute the `basename $0` again after changing to the root."
		press_enter_key
    fi
    exit $result
fi

# user confirm.
if test "no" = "${TEST}" ; then
	while true ; do
		echo -n "Uninstall ${package_name}  [y/n]? "
		read a
		answer="`echo $a | tr A-Z a-z`"
		case "$answer" in
			"y" | "yes" ) break ;;
			"n" | "no" )
				echo "Uninstallation canceled."
				press_enter_key
				exit 0 ;;
			* ) echo "[ERROR] Please enter \"y\" or \"n\"." ;;
		esac
    done
fi


# set uninstaller option.
if test "rpm" = "${uninstaller}" ; then
    if test "no" = "${TEST}" ; then
        option="-e"
    else
        option="-e --test"
    fi
else
    if test "no" = "${TEST}" ; then
        option="-P"
    else
        option="--no-act -P"
    fi
fi

# get list of printers that use TM/BA series printer driver being uninstalled
# set locale = en_US to unify output string format
LANG_O=${LANG}
LANG=en_US.utf8
# get the line including "tmbaprn:/ESDPRT" from lpstat output.
# and get the 3rd word from the line, setting it to tmprnlist
tmprnlist=`lpstat -t 2>/dev/null|grep "tmbaprn:/ESDPRT"|cut -d " " -f 3`
# recover locale
LANG=${LANG_O}

# preset answer to yes for deleting printer(s).
answer="y"
# Do uninstall.
if test "no" = "${TEST}" ; then
	# uninstall target_packages
    for package in ${target_packages} ; do
		echo "${uninstaller} ${option} ${package}"
		${uninstaller} ${option} ${package}
		sleep ${sleep_sec}
    done
    # user confirm: deleting printers that use the uninstalled TM/BA series printer driver
	if test "" != "$tmprnlist" ; then
		echo ""
		echo "Printer(s) using the uninstalled driver:"
		echo "$tmprnlist"
		# get answer
		while true ; do
			echo -n "Delete the enumerated printer(s) [y/n]? "
			read a
			answer="`echo $a | tr A-Z a-z`"
			case "$answer" in
				"y" | "yes" ) break ;;
				"n" | "no"  ) answer="n"; break ;;
				*         ) echo "[ERROR] Please enter \"y\" or \"n\"." ;;
			esac
		done
	fi
else
	# test mode; only display messages
	echo "* default_packager=${default_packager}"
	echo "* uninstaller=${uninstaller} ${option}"
    echo "* Target packages: ${target_packages}"
    echo "* Uninstall test:"
    ${uninstaller} ${option} ${target_packages}
	# Show recommendation message
	echo "Desirable to delete the printers that use the driver to be uninstalled."
fi

if test "y" = "${answer}" ; then
	# Delete CUPS printers that use the uninstalled driver.
	if test "" != "$tmprnlist" ; then
		# delete all printers in tmprnlist
		for tmprn in $tmprnlist ; do
			# remove the last ':'
			tmprn=${tmprn%:}
			# delete tmprn
			if test "no" = "${TEST}" ; then
				echo "Deleting printer: $tmprn"
				lpadmin -x $tmprn
			else
				# only display message on test mode
				echo "  Going to delete $tmprn."
			fi
		done
	else
		# printer that uses the driver being uninstalled not found
		echo "There is no printer to delete."
	fi
else
	# only display message when the printer deletion cancelled
	echo "Printer deletion canceled."
fi

echo ""
if test "no" = "${TEST}" ; then
	echo "*** The uninstallation finished. ***"
else
	echo "*** The uninstallation test finished. ***"
fi
echo ""
press_enter_key

# end of file
