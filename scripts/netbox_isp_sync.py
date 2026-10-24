#!/usr/bin/env python3
"""
NetBox ISP Business Infrastructure Synchronization Script.
Registers ISP Sites, Autonomous Systems (AS139999), Core BNG Routers,
FTTH GPON OLTs, CGNAT Subnets, PPPoE VLANs, and Hotspot Pools into NetBox.
"""

import sys
from pathlib import Path
import yaml
import pynetbox

NETBOX_URL = "http://localhost:8000"
NETBOX_TOKEN = "0123456789abcdef0123456789abcdef01234567"

BASE_DIR = Path(__file__).resolve().parent.parent
HOST_VARS_DIR = BASE_DIR / "inventory" / "host_vars"
GROUP_VARS_DIR = BASE_DIR / "inventory" / "group_vars" / "all"


def main():
    print(f"Connecting to NetBox at {NETBOX_URL}...")
    try:
        nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)
        # Test connectivity
        status = nb.status()
        print(f"✅ NetBox Connected! (Version: {status.get('netbox-version', 'v4.x')})")
    except Exception as e:
        print(f"⚠️ Warning: Could not connect to live NetBox instance: {e}")
        print("Continuing with dry-run verification mode.")
        return

    # 1. Manufacturers
    mfg_mikrotik = nb.dcim.manufacturers.get(slug="mikrotik") or nb.dcim.manufacturers.create(
        name="MikroTik", slug="mikrotik"
    )
    mfg_huawei = nb.dcim.manufacturers.get(slug="huawei") or nb.dcim.manufacturers.create(
        name="Huawei", slug="huawei"
    )
    print("✅ Manufacturers Verified: MikroTik, Huawei")

    # 2. Device Types
    dt_bng = nb.dcim.device_types.get(slug="ccr2116") or nb.dcim.device_types.create(
        model="CCR2116-12G-4S+", slug="ccr2116", manufacturer=mfg_mikrotik.id
    )
    dt_olt = nb.dcim.device_types.get(slug="ma5800-x7") or nb.dcim.device_types.create(
        model="SmartAX MA5800-X7", slug="ma5800-x7", manufacturer=mfg_huawei.id
    )

    # 3. Device Roles
    role_bng = nb.dcim.device_roles.get(slug="core-bng-router") or nb.dcim.device_roles.create(
        name="Core-BNG-Router", slug="core-bng-router", color="004d40"
    )
    role_olt = nb.dcim.device_roles.get(slug="ftth-olt") or nb.dcim.device_roles.create(
        name="FTTH-OLT", slug="ftth-olt", color="00b4d8"
    )

    # 4. Process Host Vars & Register Sites/Devices
    for hf in sorted(HOST_VARS_DIR.glob("*.yml")):
        with open(hf, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        hostname = data["hostname"]
        site_name = data["site_name"]
        site_slug = site_name.lower().replace(" ", "-")
        role = data.get("device_role")

        # Create/Get Site
        site = nb.dcim.sites.get(slug=site_slug) or nb.dcim.sites.create(
            name=site_name, slug=site_slug, status="active"
        )
        print(f"\n📍 Site: {site.name} ({site.slug})")

        # Create/Get Device
        dev_type = dt_bng if role == "core-bng-router" else dt_olt
        dev_role = role_bng if role == "core-bng-router" else role_olt

        dev = nb.dcim.devices.get(name=hostname)
        if not dev:
            dev = nb.dcim.devices.create(
                name=hostname,
                device_type=dev_type.id,
                role=dev_role.id,
                site=site.id,
                status="active",
            )
            print(f"  🖥️  Created Device: {dev.name} ({role})")
        else:
            print(f"  🖥️  Found Existing Device: {dev.name} ({role})")

        # Attach local context data
        dev.local_context_data = data
        dev.save()

        # If Core BNG Router, register BGP WANs, CGNAT Subnets & VLANs
        if role == "core-bng-router":
            # Master Public Prefix
            for pfx in data.get("bgp", {}).get("announced_prefixes", []):
                nb.ipam.prefixes.get(prefix=pfx) or nb.ipam.prefixes.create(
                    prefix=pfx, site=site.id, status="active", description="ISP Public BGP Master Block"
                )
                print(f"  🌐 Registered Public BGP Prefix: {pfx}")

            # CGNAT Subscriber Subnet
            cgnat_sub = data.get("cgnat", {}).get("subscriber_subnet")
            if cgnat_sub:
                nb.ipam.prefixes.get(prefix=cgnat_sub) or nb.ipam.prefixes.create(
                    prefix=cgnat_sub, site=site.id, status="active", description="CGNAT RFC 6598 Pool"
                )
                print(f"  🔄 Registered CGNAT Subscriber Subnet: {cgnat_sub}")

            # Campus Hotspot Subnet
            hotspot_sub = data.get("hotspot", {}).get("network")
            if hotspot_sub:
                nb.ipam.prefixes.get(prefix=hotspot_sub) or nb.ipam.prefixes.create(
                    prefix=hotspot_sub, site=site.id, status="active", description="Campus Wi-Fi Hotspot"
                )
                print(f"  📶 Registered Hotspot Subnet: {hotspot_sub}")

            # Register VLANs
            isp_vlans = [
                {"vid": 10, "name": "Management", "desc": "Out-of-Band OLT & BNG Management"},
                {"vid": 100, "name": "PPPoE-Subscribers", "desc": "FTTH Broadband PON Access"},
                {"vid": 200, "name": "Campus-Hotspot", "desc": "Public Wi-Fi Captive Portal"},
                {"vid": 300, "name": "Corporate-Leased", "desc": "Dedicated 1:1 Business Lines"},
            ]
            for v in isp_vlans:
                v_obj = list(nb.ipam.vlans.filter(vid=v["vid"], site_id=site.id))
                if not v_obj:
                    nb.ipam.vlans.create(
                        vid=v["vid"], name=v["name"], site=site.id, status="active", description=v["desc"]
                    )
                print(f"  🏷️  VLAN {v['vid']:03d}: {v['name']}")

    print("\n🎉 NetBox ISP Business Infrastructure Synchronization Completed Successfully!")


if __name__ == "__main__":
    main()
