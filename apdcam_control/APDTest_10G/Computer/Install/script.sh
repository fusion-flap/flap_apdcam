#!/bin/sh
su
yum -yq update
yum -yq install libcap-dev
echo apdcontrol    ALL=(ALL)       ALL >> /etc/sudoers
echo 128000000 > /proc/sys/net/core/rmem_max
sysctl -w net.core.rmem_max=128000000
echo apd hard memlock 2000000000 >> /etc/security/limits.conf
echo apd soft memlock 2000000000 >> /etc/security/limits.conf
ifconfig eth0 mtu 9000
echo ifconfig eth0 mtu 9000 >> /etc/rc.local
cp iptables /etc/sysconfig
