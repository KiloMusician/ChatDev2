#!/usr/bin/env python3
"""Performance Monitoring Script for NuSyQ-Hub

Tracks CPU, memory, and runtime stats for key processes.
"""

import argparse
import time

import psutil


def monitor(interval=2, duration=30):
    print(f"Monitoring system performance every {interval}s for {duration}s...")
    start = time.time()
    while time.time() - start < duration:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        print(f"CPU: {cpu:5.1f}% | Memory: {mem:5.1f}%")
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Monitor system performance.")
    parser.add_argument("--interval", type=int, default=2, help="Seconds between samples")
    parser.add_argument("--duration", type=int, default=30, help="Total seconds to monitor")
    args = parser.parse_args()
    monitor(args.interval, args.duration)


if __name__ == "__main__":
    main()
