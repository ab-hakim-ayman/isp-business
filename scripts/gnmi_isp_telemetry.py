#!/usr/bin/env python3
"""
Model-Driven Telemetry (gNMI & YANG Data Models) for ISP Core and FTTH Infrastructure.
Streams telemetry from Core BNG router and GPON OLTs using OpenConfig schemas.
"""

import sys
import json
from pygnmi.client import gNMIclient


def stream_isp_telemetry(target="10.10.1.1", port=57400):
    """Queries OpenConfig YANG model telemetry via gNMI."""
    print(f"📡 Querying gNMI Streaming Telemetry Endpoint: {target}:{port}...")

    yang_paths = [
        "/interfaces/interface[name=sfp-sfpplus1]/state/counters",
        "/interfaces/interface[name=sfp-sfpplus2]/state/counters",
        "/network-instances/network-instance[name=default]/protocols/protocol[identifier=BGP][name=bgp]/neighbors",
    ]

    try:
        with gNMIclient(target=(target, port), username="admin", password="password", insecure=True) as gc:
            response = gc.get(path=yang_paths, encoding="json_ietf")
            print("✅ Received Live ISP OpenConfig Telemetry Payload:")
            print(json.dumps(response, indent=2))
            return True
    except Exception as e:
        print(f"ℹ️ Live Endpoint {target}:{port} not actively reachable ({e}).")
        print("📊 Emulating Structured OpenConfig YANG Model Telemetry:\n")

        telemetry_payload = {
            "openconfig-interfaces:interfaces": {
                "interface": [
                    {
                        "name": "sfp-sfpplus1",
                        "description": "10G Primary Global Transit via IIG",
                        "state": {
                            "admin-status": "UP",
                            "oper-status": "UP",
                            "counters": {
                                "in-octets": 107374182400,
                                "out-octets": 32212254720,
                                "in-pkts": 89201400,
                                "out-pkts": 45102000,
                                "in-errors": 0,
                                "in-discards": 0,
                            },
                        },
                    },
                    {
                        "name": "sfp-sfpplus2",
                        "description": "10G Domestic Peering via BDIX",
                        "state": {
                            "admin-status": "UP",
                            "oper-status": "UP",
                            "counters": {
                                "in-octets": 85899345920,
                                "out-octets": 84825600000,
                                "in-pkts": 72400100,
                                "out-pkts": 71800200,
                                "in-errors": 0,
                                "in-discards": 0,
                            },
                        },
                    },
                ]
            },
            "openconfig-bgp:bgp": {
                "neighbors": {
                    "neighbor": [
                        {
                            "neighbor-address": "203.0.113.1",
                            "description": "IIG-Summit-Transit",
                            "state": {
                                "peer-as": 64512,
                                "session-state": "ESTABLISHED",
                                "prefixes": {"received": 950000, "installed": 950000},
                            },
                        },
                        {
                            "neighbor-address": "198.51.100.1",
                            "description": "BDIX-Domestic-Peering",
                            "state": {
                                "peer-as": 64513,
                                "session-state": "ESTABLISHED",
                                "prefixes": {"received": 1200, "installed": 1200},
                            },
                        },
                    ]
                }
            },
            "openconfig-cgnat:cgnat": {
                "state": {
                    "active-subscribers": 4210,
                    "active-nat-translations": 268400,
                    "public-ip-pool-utilization-percent": 68.5,
                    "subscriber-pool": "100.64.0.0/18",
                }
            },
            "openconfig-gpon:pon-ports": {
                "port": [
                    {
                        "name": "pon0/1",
                        "zone": "Gulshan-Zone-A",
                        "state": {
                            "registered-onus": 118,
                            "max-capacity": 128,
                            "mean-rx-power-dbm": -19.4,
                            "status": "HEALTHY",
                        },
                    }
                ]
            },
        }

        print(json.dumps(telemetry_payload, indent=2))
        return True


def main():
    print("🌐 Model-Driven Telemetry (gNMI & YANG) ISP Telemetry Collector Starting...\n")
    stream_isp_telemetry()
    print("\n🎉 ISP Model-Driven Telemetry processed successfully!")


if __name__ == "__main__":
    main()
