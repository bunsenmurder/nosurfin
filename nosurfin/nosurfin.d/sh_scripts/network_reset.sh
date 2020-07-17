#!/bin/sh
ipv4_forward=$(sysctl -n net.ipv4.conf.all.forwarding)
ipv6_forward=$(sysctl -n net.ipv6.conf.all.forwarding )
icmp_redirect=$(sysctl -n net.ipv4.conf.all.send_redirects )
ipv4_nat_80=$(iptables -t nat -L OUTPUT --line-numbers | grep "http\s.\+ports\s8080" | wc -l)
ipv4_nat_443=$(iptables -t nat -L OUTPUT --line-numbers | grep "https\s.\+ports\s8080" | wc -l)
ipv6_nat_80=$(ip6tables -t nat -L OUTPUT --line-numbers | grep "http\s.\+ports\s8080" | wc -l)
ipv6_nat_443=$(ip6tables -t nat -L OUTPUT --line-numbers | grep "https\s.\+ports\s8080"| wc -l)
echo 'Block Finished. Resetting Network Settings'
# Turns off ip forwarding and turns on icmp redirects.
if [ $ipv4_forward == 1 ]
then
    sysctl -w net.ipv4.ip_forward=0
fi

if [ $ipv6_forward == 1 ]
then
    sysctl -w net.ipv6.conf.all.forwarding=0
fi

if [ $icmp_redirect == 0 ]
then
    sysctl -w net.ipv4.conf.all.send_redirects=1
fi

if [ $ipv4_nat_80 -gt 0 ]
then
    rule_id=$(iptables -t nat -L OUTPUT --line-numbers | grep "http\s.\+ports\s8080" | awk '{match($0, "[0-9]+",group)}END{print group[0]}')
    iptables -t nat -D OUTPUT $rule_id
fi

if [ $ipv4_nat_443 -gt 0 ]
then
    rule_id=$(iptables -t nat -L OUTPUT --line-numbers | grep "https\s.\+ports\s8080" | awk '{match($0, "[0-9]+",group)}END{print group[0]}')
    iptables -t nat -D OUTPUT $rule_id
fi


if [ $ipv6_nat_80 -gt 0 ]
then
    rule_id=$(ip6tables -t nat -L OUTPUT --line-numbers | grep "http\s.\+ports\s8080" | awk '{match($0, "[0-9]+",group)}END{print group[0]}')
    ip6tables -t nat -D OUTPUT $rule_id
fi

if [ $ipv6_nat_443 -gt 0 ]
then
    rule_id=$(ip6tables -t nat -L OUTPUT --line-numbers | grep "https\s.\+ports\s8080" | awk '{match($0, "[0-9]+",group)}END{print group[0]}')
    ip6tables -t nat -D OUTPUT $rule_id
fi
echo 'Done'