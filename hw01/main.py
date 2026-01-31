import subprocess
import requests
import numpy as np
import sys
import csv
import geopy.distance
import matplotlib.pyplot as plt
import random

def get_ip_from_host(host):
    response = subprocess.run(["ping", "-i", "0.002", "-c", "1", host], capture_output=True, text=True)
    # cannot resolve this host
    if response.returncode != 0 or "0 packets received" in response.stdout:
        return None
    ip = response.stdout[response.stdout.find('(') + 1: response.stdout.find(')') ]
    return ip

# returns the list of ip addresses from iperf3
# while resolving hosts to ip addresses
def get_ips(file_name):
    ips = []
    with open(file_name) as file_obj:
        # skips heading
        heading = next(file_obj)

        reader_obj = csv.reader(file_obj)

        for row in reader_obj:
            host = row[0]
            # the host can be either a name or the
            # ip address, use ping to get the actual ip
            ip = get_ip_from_host(host)
            if ip != None:
                ips.append(ip)

    return ips

def get_rtts(ips):
    # I decided to run ping 4 times because running it for more takes a very long time 
    # for all of the ip addresses
    rtt = [None for _ in range(len(ips))]
    for i, ip in enumerate(ips):
        response = subprocess.run(["ping", "-i", "0.002", "-c", "100", ip], capture_output=True, text=True)
        if response.returncode != 0:
            continue

        stats = response.stdout.splitlines()[-1]
        rtt_times = stats[stats.find('=') + 2: stats.rfind('m') - 1].split('/')
        for j in range(len(rtt_times)):
            rtt_times[j] = float(rtt_times[j])
        rtt[i] = rtt_times

    return rtt

def get_rtts_to_hops(ips):
    rtt = [None for _ in range(len(ips))]
    for i, ip in enumerate(ips):
        response = subprocess.run(["traceroute", "-w", "1", "-q", "1", ip], capture_output=True, text=True)
        if response.returncode != 0:
            continue

        rtt[i] = []
        for line in response.stdout.splitlines():
            if "*" in line:
                continue
            # take the first hop time
            idx = line.find(" ms")
            rtt[i].append(float(line[:idx].split()[-1]))

    return rtt

def get_geo(ips):
    geo = [None for _ in range(len(ips))]
    for i, ip in enumerate(ips):
        response = subprocess.run(["curl", "-H", "Authorization: Bearer 9e53f5fb00657d", f"https://ipinfo.io/{ip}/loc"], capture_output=True, text=True)
        if response.returncode == 0:
            location = response.stdout.strip().split(',')
            geo[i] = (float(location[0]), float(location[1]))

    return geo

def get_my_ip():
    response = subprocess.run(["curl", "-H", "Authorization: Bearer 9e53f5fb00657d", "https://ipinfo.io/ip"], capture_output=True, text=True)
    if response.returncode == 0:
        return response.stdout
    return None

def get_distance_to_me(my_geo, geo):
    return geopy.distance.geodesic(my_geo, geo).km

def q1(ips):
    print('Question 1')
    print('Running part a')
    # part a
    rtt, geo = get_rtts(ips), get_geo(ips)
    for i, ip in enumerate(ips):
        if rtt[i] and geo[i]:
            print(f"ip = {ip}")
            print(f"min rtt = {rtt[i][0]}")
            print(f"max rtt = {rtt[i][2]}")
            print(f"avg rtt = {rtt[i][1]}")
            print(f"geolocation = {geo[i]}")
        if i != len(ips) - 1:
            print()

    # part b: scatter plot of distance vs rtt
    print('Running part b')
    my_geo = geo[-1]
    if my_geo == None:
        print("Error: Unable to get my own location, can't plot")
        return

    #it's unclear whether we are supposed to consider our own destination
    #but i consider it for completeness sake ig
    xs = []
    ys = []
    for i, ip in enumerate(ips):
        if rtt[i] and geo[i]:
            xs.append(get_distance_to_me(my_geo, geo[i]))
            ys.append(rtt[i][1])

    plt.xlabel("Distance from my location (km)")
    plt.ylabel("Average rtt (ms)")
    plt.scatter(xs, ys)
    plt.savefig("figures/1b.png")

    plt.clf()

    # part c
    print('Running part c')
    xs = []
    ys = []
    for i, ip in enumerate(ips):
        if rtt[i] and geo[i]:
            xs.append(get_distance_to_me(my_geo, geo[i]))
            ys.append(rtt[i][0])

    plt.xlabel("Distance from my location (km)")
    plt.ylabel("Minimum rtt (ms)")
    plt.scatter(xs, ys)
    plt.savefig("figures/1c1.png")

    plt.clf()

    xs = []
    ys = []
    for i, ip in enumerate(ips):
        if rtt[i] and geo[i]:
            xs.append(get_distance_to_me(my_geo, geo[i]))
            ys.append(rtt[i][2])

    plt.xlabel("Distance from my location (km)")
    plt.ylabel("Maximum rtt (ms)")
    plt.scatter(xs, ys)
    plt.savefig("figures/1c2.png")

    plt.clf()

def q2(ips):
    print('Question 2')

    # part a
    print('Running part a')
    random_ips = random.sample(ips[:-1], 5)
    print("The 5 random ip addresses =", ' '.join(random_ips))
    rtts_to_hops = get_rtts_to_hops(random_ips)
    for i, ip in enumerate(random_ips):
        print(f"Hops for ip = {ip}")
        if rtts_to_hops[i] != None:
            for j in range(len(rtts_to_hops[i])):
                print(f"    Time to hop {j} is {rtts_to_hops[i][j]}")
        else:
            print(f"ip = {ip} stopped responding unexpectedly")
        print()

    # part b
    print('Running part b')
    x = []
    for i, ip in enumerate(random_ips):
        if rtts_to_hops[i] != None:
            x.append(ip)

    rtt_per_hop = []
    for i, ip in enumerate(random_ips):
        if rtts_to_hops[i] != None:
            diffs = [rtts_to_hops[i][0]]
            max_rtt = diffs[0]
            for j in range(1, len(rtts_to_hops[i])):
                if rtts_to_hops[i][j] > max_rtt:
                    diffs.append(rtts_to_hops[i][j] - max_rtt)
                    max_rtt = rtts_to_hops[i][j]
            rtt_per_hop.append(diffs)

    # make all bars have the same number of hops
    # purely for stacked plot purposes
    max_hops = max(len(d) for d in rtt_per_hop)
    ys = []
    for hop in range(max_hops):
        y = []
        for i in range(len(rtt_per_hop)):
            if hop < len(rtt_per_hop[i]):
                y.append(rtt_per_hop[i][hop])
            else:
                y.append(0)
        ys.append(np.array(y))

    bottom = np.zeros(len(ys[0]))
    for i in range(len(ys)):
        plt.bar(x, ys[i], bottom=bottom)
        bottom = bottom + ys[i]

    plt.xticks(range(len(x)), x, rotation=45)
    plt.xlabel("Destination IPs")
    plt.ylabel("rtt per hop (ms)")

    plt.tight_layout()
    plt.savefig("figures/2b.png")
    plt.clf()

    # part c
    rtt = get_rtts(random_ips)
    print('Running part c')
    xs = []
    ys = []
    for i, ip in enumerate(random_ips):
        if rtts_to_hops[i] != None and rtt[i] != None:
            xs.append(len(rtts_to_hops[i]))
            ys.append(rtt[i][1])

    plt.xlabel("Hop count")
    plt.ylabel("Average rtt (ms)")
    plt.scatter(xs, ys)
    plt.savefig("figures/2c.png")

    plt.clf()

    # part d
    # no code

def main():
    if len(sys.argv) != 2:
        print("Error: Please specify the csv file from iperf3")
        return

    # --- general stuff start ---
    file_name = sys.argv[1]
    ips = get_ips(file_name)
    my_ip = get_my_ip()
    ips.append(my_ip)
    random.seed(9)
    # --- general stuff end --- 

    if my_ip == None:
        print("Error: Unable to get my own ip")
        return

    q1(ips)
    q2(ips)

if __name__ == "__main__":
    main()
