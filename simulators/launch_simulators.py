#!/usr/bin/env python3
"""
Pond Simulators Launcher

This script provides easy control for starting pond simulators individually or together.

Usage:
    python launch_simulators.py pond_001        # Start pond 001 simulator
    python launch_simulators.py pond_002        # Start pond 002 simulator
    python launch_simulators.py both           # Start both simulators (in separate terminals)
    python launch_simulators.py --help         # Show help
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def launch_pond_001():
    """Launch pond 001 simulator"""
    print("🚀 Starting Pond 001 Simulator...")
    script_path = Path(__file__).parent / "pond_001_simulator.py"
    subprocess.run([sys.executable, str(script_path)])


def launch_pond_002():
    """Launch pond 002 simulator"""
    print("🚀 Starting Pond 002 Simulator...")
    script_path = Path(__file__).parent / "pond_002_simulator.py"
    subprocess.run([sys.executable, str(script_path)])


def launch_both():
    """Launch both simulators in separate processes"""
    print("🚀 Starting Both Pond Simulators...")
    print("📋 Instructions:")
    print("   1. Open two separate terminal windows")
    print("   2. In terminal 1, run: python simulators/pond_001_simulator.py")
    print("   3. In terminal 2, run: python simulators/pond_002_simulator.py")
    print("   4. To stop a simulator, press Ctrl+C in its terminal")
    print("\nAlternatively, you can run them in background:")
    print("   python simulators/pond_001_simulator.py &")
    print("   python simulators/pond_002_simulator.py &")


def main():
    parser = argparse.ArgumentParser(
        description="Launch pond simulators for the aquaculture monitoring system"
    )
    parser.add_argument(
        "simulator",
        choices=["pond_001", "pond_002", "both"],
        help="Which simulator(s) to launch"
    )
    
    args = parser.parse_args()
    
    if args.simulator == "pond_001":
        launch_pond_001()
    elif args.simulator == "pond_002":
        launch_pond_002()
    elif args.simulator == "both":
        launch_both()


if __name__ == "__main__":
    main()
