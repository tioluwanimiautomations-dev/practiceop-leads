#!/usr/bin/env python3
"""Orchestrator. Usage: python run_market.py --market miami_broward --step 1-2"""
import argparse
import importlib

from lib.common import load_market

STEPS = {1: "s1_scrape", 2: "s2_filter"}  # 3-6 not built yet


def parse_steps(s):
    a, _, b = s.partition("-")
    return range(int(a), int(b or a) + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", required=True)
    ap.add_argument("--step", default="1-2", help="N or N-M")
    ap.add_argument("--seed", type=int, default=None, help="seed for random dropped-name sample")
    args = ap.parse_args()
    market = load_market(args.market)
    for n in parse_steps(args.step):
        if n not in STEPS:
            raise SystemExit(f"step {n} not built yet")
        importlib.import_module(f"steps.{STEPS[n]}").run(market, seed=args.seed)


if __name__ == "__main__":
    main()
