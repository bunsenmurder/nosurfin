#!/bin/bash
# Can be overriden if using a diffrent superuser account
user_name='root'
if [ "$#" -gt "0" ]
then
    user_name=$1
    echo 'User name has been set as:' $user_name
fi

echo 'Block started! Configuring network for block.'
ipv4_set () {
    # Sets network settings if not set already
    ipv4_forward=$(sysctl -n net.ipv4.conf.all.forwarding)
    ipv4_nat_80=$(iptables -t nat -L OUTPUT --line-numbers | grep "http\s.\+ports\s8080" | wc -l)
    ipv4_nat_443=$(iptables -t nat -L OUTPUT --line-numbers | grep "https\s.\+ports\s8080" | wc -l)

    if [ $ipv4_forward == 0 ]
    then
        sysctl -w net.ipv4.ip_forward=1
    fi

    if [ $ipv4_nat_80 == 0 ]
    then
    	iptables -t nat -A OUTPUT -p tcp -m owner ! --uid-owner "$user_name" --dport 80 -j REDIRECT --to-port 8080
    fi

    if [ $ipv4_nat_443 == 0 ]
    then
        iptables -t nat -A OUTPUT -p tcp -m owner ! --uid-owner "$user_name" --dport 443 -j REDIRECT --to-port 8080
    fi
}
ipv6_set () {
    # Sets network settings if not set already
    ipv6_forward=$(sysctl -n net.ipv6.conf.all.forwarding)
    ipv6_nat_80=$(ip6tables -t nat -L OUTPUT --line-numbers | grep "http\s.\+ports\s8080" | wc -l)
    ipv6_nat_443=$(ip6tables -t nat -L OUTPUT --line-numbers | grep "https\s.\+ports\s8080"| wc -l)

    if [ $ipv6_forward == 0 ]
    then
        sysctl -w net.ipv6.conf.all.forwarding=1
    fi

    if [ $ipv6_nat_80 == 0 ]
    then
    	ip6tables -t nat -A OUTPUT -p tcp -m owner ! --uid-owner "$user_name" --dport 80 -j REDIRECT --to-port 8080
    fi

    if [ $ipv6_nat_443 == 0 ]
    then
    	ip6tables -t nat -A OUTPUT -p tcp -m owner ! --uid-owner "$user_name" --dport 443 -j REDIRECT --to-port 8080
    fi
}

icmp_redirect=$(sysctl -n net.ipv4.conf.all.send_redirects)
if [ $icmp_redirect == 1 ]
then
    sysctl -w net.ipv4.conf.all.send_redirects=0
fi
# Sets ipv4 rules
ipv4_set
# Sets ipv6 rules if system supports ipv6
if [ $(sysctl -a | grep net.ipv6) ]
then
    ipv6_set
fi

echo 'Done'
