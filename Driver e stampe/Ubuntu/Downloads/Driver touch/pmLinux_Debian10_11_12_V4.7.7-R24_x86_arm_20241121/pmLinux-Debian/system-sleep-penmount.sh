#!/bin/sh

case "$1" in
    pre)
            ;;
    post)
            echo reload-audio > /etc/penmount/action
            ;;
    *) exit $NA
            ;;
esac
