#!/bin/bash
# Use fully qualified private DNS name for the host name.  Kube wants it this way.
HOSTNAME=$(curl http://169.254.169.254/latest/meta-data/hostname)
echo $HOSTNAME > /etc/hostname
sed -i -e "s|\(127\.0\..\..\s*\)|\1$HOSTNAME |" /etc/hosts
hostname $HOSTNAME
