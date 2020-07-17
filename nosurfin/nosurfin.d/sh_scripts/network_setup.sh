#!/bin/sh
ipv4_forward=$(sysctl -n net.ipv4.conf.all.forwarding)
ipv6_forward=$(sysctl -n net.ipv6.conf.all.forwarding )
icmp_redirect=$(sysctl -n net.ipv4.conf.all.send_redirects )
ipv4_nat_80=$(iptables -t nat -L OUTPUT --line-numbers | grep "http\s.\+ports\s8080" | wc -l)
ipv4_nat_443=$(iptables -t nat -L OUTPUT --line-numbers | grep "https\s.\+ports\s8080" | wc -l)
ipv6_nat_80=$(ip6tables -t nat -L OUTPUT --line-numbers | grep "http\s.\+ports\s8080" | wc -l)
ipv6_nat_443=$(ip6tables -t nat -L OUTPUT --line-numbers | grep "https\s.\+ports\s8080"| wc -l)
user_name='root'
if [ "$#" -gt "0" ]
then
    user_name=$1
    echo 'User name has been set as:' $user_name
fi

echo 'Block started! Configuring network for block.'

if [ $ipv4_forward == 0 ]
then
    sysctl -w net.ipv4.ip_forward=1
fi

if [ $ipv6_forward == 0 ]
then
    sysctl -w net.ipv6.conf.all.forwarding=1
fi

if [ $icmp_redirect == 1 ]
then
    sysctl -w net.ipv4.conf.all.send_redirects=0
fi

if [ $ipv4_nat_80 == 0 ]
then
    iptables -t nat -A OUTPUT -p tcp -m owner ! --uid-owner "$user_name" --dport 80 -j REDIRECT --to-port 8080
fi

if [ $ipv4_nat_443 == 0 ]
then
    iptables -t nat -A OUTPUT -p tcp -m owner ! --uid-owner "$user_name" --dport 443 -j REDIRECT --to-port 8080
fi


if [ $ipv6_nat_80 == 0 ]
then
    ip6tables -t nat -A OUTPUT -p tcp -m owner ! --uid-owner "$user_name" --dport 80 -j REDIRECT --to-port 8080
fi

if [ $ipv6_nat_443 == 0 ]
then
    ip6tables -t nat -A OUTPUT -p tcp -m owner ! --uid-owner "$user_name" --dport 443 -j REDIRECT --to-port 8080
fi

echo 'Done'
