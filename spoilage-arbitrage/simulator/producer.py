#!/usr/bin/env python3
"""Mock IoT simulator for avocado reefer containers.

Streams one reading per container every --interval seconds to Kafka
(or prints JSON lines with --dry-run). About 25% of voyages get an
injected fault (temperature drift or humidity spike) so the Week 3
Spoilage Arbitrage models have something to detect.
"""
import argparse
import json
import math
import random
import sys
import time
from datetime import datetime, timezone

PORTS = {
    "Veracruz": (19.20, -96.13),
    "Lazaro Cardenas": (17.96, -102.20),
    "Callao": (-12.05, -77.15),
}
MARKETS = {
    "Rotterdam": (51.92, 4.48),
    "Hamburg": (53.55, 9.99),
    "Los Angeles": (33.74, -118.27),
    "New York": (40.67, -74.04),
}
SHIP_KM_PER_HOUR = 35
FAULT_RATE = 0.25


def haversine_km(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(h))


class Container:
    def __init__(self, cid):
        self.cid = cid
        self.new_voyage(random_start=True)

    def new_voyage(self, random_start=False):
        self.origin = random.choice(list(PORTS))
        self.destination = random.choice(list(MARKETS))
        self.o, self.d = PORTS[self.origin], MARKETS[self.destination]
        self.transit_h = haversine_km(self.o, self.d) / SHIP_KM_PER_HOUR
        self.elapsed_h = random.uniform(0, 0.5) * self.transit_h if random_start else 0.0
        self.setpoint = random.uniform(5.5, 7.0)
        self.fault = None
        if random.random() < FAULT_RATE:
            self.fault = random.choice(["temp_drift", "humidity_spike"])
        self.fault_start_h = min(random.uniform(5, 30), 0.5 * self.transit_h)
        # Ground truth for checking Week 3 results later (goes to stderr, not Kafka)
        print(f"[truth] {self.cid} {self.origin}->{self.destination} "
              f"transit={self.transit_h:.0f}h fault={self.fault}", file=sys.stderr)

    def step(self, sim_hours):
        self.elapsed_h += sim_hours
        if self.elapsed_h >= self.transit_h:
            self.new_voyage()
        frac = self.elapsed_h / self.transit_h
        lat = self.o[0] + (self.d[0] - self.o[0]) * frac
        lon = self.o[1] + (self.d[1] - self.o[1]) * frac

        temp = self.setpoint + random.gauss(0, 0.2)
        hum = 88 + random.gauss(0, 1.2)
        if self.fault and self.elapsed_h >= self.fault_start_h:
            hrs = self.elapsed_h - self.fault_start_h
            if self.fault == "temp_drift":
                temp += min(0.3 * hrs, 10)
            else:
                hum = min(99.5, hum + min(1.5 * hrs, 9))

        vib = abs(random.gauss(0.08, 0.03))
        if random.random() < 0.02:
            vib = random.uniform(0.4, 1.2)

        return {
            "container_id": self.cid,
            "commodity": "avocado",
            "event_ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "temperature_c": round(temp, 2),
            "humidity_pct": round(hum, 1),
            "vibration_g": round(vib, 3),
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "origin": self.origin,
            "destination": self.destination,
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--containers", type=int, default=20)
    ap.add_argument("--interval", type=float, default=5, help="real seconds between rounds")
    ap.add_argument("--sim-minutes", type=float, default=60, help="simulated minutes per round")
    ap.add_argument("--ticks", type=int, default=0, help="stop after N rounds (0 = forever)")
    ap.add_argument("--bootstrap", default="localhost:9092")
    ap.add_argument("--topic", default="iot.sensor.readings")
    ap.add_argument("--dry-run", action="store_true", help="print JSON, don't use Kafka")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    producer = None
    if not args.dry_run:
        from confluent_kafka import Producer
        producer = Producer({"bootstrap.servers": args.bootstrap})

    def on_delivery(err, msg):
        if err:
            print(f"[kafka error] {err}", file=sys.stderr)

    containers = [Container(f"CNT-{i:04d}") for i in range(1, args.containers + 1)]
    tick = 0
    try:
        while args.ticks == 0 or tick < args.ticks:
            for c in containers:
                msg = c.step(args.sim_minutes / 60)
                payload = json.dumps(msg)
                if producer:
                    producer.produce(args.topic, key=c.cid, value=payload,
                                     callback=on_delivery)
                    producer.poll(0)
                else:
                    print(payload)
            tick += 1
            if args.ticks == 0 or tick < args.ticks:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopping...", file=sys.stderr)
    finally:
        if producer:
            producer.flush(10)


if __name__ == "__main__":
    main()
