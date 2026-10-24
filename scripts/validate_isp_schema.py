#!/usr/bin/env python3
"""
Pydantic v2 Schema Validator for ISP Business Network Automation.
Validates BGP Autonomous Systems, CGNAT Subnets (RFC 6598), PPPoE Packages,
Hotspot Subnets, and FTTH GPON OLT Configurations.
"""

import sys
import ipaddress
from pathlib import Path
from typing import List, Optional, Literal, Union
import yaml
from pydantic import BaseModel, Field, field_validator


# ==============================================================================
# 1. BGP & Core Routing Models
# ==============================================================================
class BGPPeer(BaseModel):
    name: str
    remote_asn: int = Field(..., ge=1, le=4294967295)
    peer_ip: str
    local_ip: str
    interface: str
    description: str
    local_preference: int = Field(default=100, ge=1, le=1000)
    role: Literal["upstream", "ixp", "peer", "customer"]

    @field_validator("peer_ip")
    @classmethod
    def validate_peer_ip(cls, v: str) -> str:
        ipaddress.IPv4Address(v)
        return v

    @field_validator("local_ip")
    @classmethod
    def validate_local_ip(cls, v: str) -> str:
        ipaddress.IPv4Interface(v)
        return v


class BGPConfig(BaseModel):
    local_asn: int = Field(..., ge=1, le=4294967295)
    router_id: str
    announced_prefixes: List[str]
    peers: List[BGPPeer]

    @field_validator("router_id")
    @classmethod
    def validate_rtr_id(cls, v: str) -> str:
        ipaddress.IPv4Address(v)
        return v

    @field_validator("announced_prefixes")
    @classmethod
    def validate_prefixes(cls, v: List[str]) -> List[str]:
        for p in v:
            ipaddress.IPv4Network(p, strict=True)
        return v


# ==============================================================================
# 2. CGNAT & Subscriber Models
# ==============================================================================
class CGNATConfig(BaseModel):
    subscriber_subnet: str
    gateway_ip: str
    public_pool_range: str
    port_range: str

    @field_validator("subscriber_subnet")
    @classmethod
    def validate_cgnat_sub(cls, v: str) -> str:
        ipaddress.IPv4Network(v, strict=True)
        return v

    @field_validator("gateway_ip")
    @classmethod
    def validate_gw_ip(cls, v: str) -> str:
        ipaddress.IPv4Address(v)
        return v


class PPPoEPackage(BaseModel):
    name: str
    rate_limit: str
    burst_limit: str
    burst_threshold: str
    burst_time: str
    price_bdt: int = Field(..., gt=0)


class PPPoEServerConfig(BaseModel):
    enabled: bool
    service_name: str
    interface: str
    vlan_id: int = Field(..., ge=1, le=4094)
    mtu: int = Field(..., ge=1280, le=1500)
    mru: int = Field(..., ge=1280, le=1500)
    address_pool: str
    packages: List[PPPoEPackage]


class HotspotConfig(BaseModel):
    enabled: bool
    interface: str
    vlan_id: int = Field(..., ge=1, le=4094)
    network: str
    gateway: str
    gateway_ip: str
    dhcp_range: str
    trial_uptime_limit: str
    trial_rate_limit: str

    @field_validator("network")
    @classmethod
    def validate_network(cls, v: str) -> str:
        ipaddress.IPv4Network(v, strict=True)
        return v

    @field_validator("gateway")
    @classmethod
    def validate_gw(cls, v: str) -> str:
        ipaddress.IPv4Interface(v)
        return v


class CoreBNGRouterModel(BaseModel):
    hostname: str
    site_name: str
    device_role: str
    management_ip: str
    management_interface: str
    bgp: BGPConfig
    cgnat: CGNATConfig
    pppoe_server: PPPoEServerConfig
    hotspot: HotspotConfig
    olt_trunk_interfaces: List[str]


# ==============================================================================
# 3. FTTH GPON OLT Models
# ==============================================================================
class PONPort(BaseModel):
    port_id: str
    name: str
    max_onus: int = Field(..., ge=1, le=128)
    vlan_id: int = Field(..., ge=1, le=4094)


class DBAProfile(BaseModel):
    id: int = Field(..., ge=1, le=128)
    name: str
    type: int = Field(..., ge=1, le=5)
    max_bandwidth_kbps: Optional[int] = None
    fix_bandwidth_kbps: Optional[int] = None


class GPONOLTModel(BaseModel):
    hostname: str
    site_name: str
    device_role: str
    management_ip: str
    management_vlan: int = Field(..., ge=1, le=4094)
    gateway_ip: str
    uplink_port: str
    uplink_vlans: List[int]
    pon_ports: List[PONPort]
    dba_profiles: List[DBAProfile]
    auto_find_onu: bool
    auto_register_default_vlan: int = Field(..., ge=1, le=4094)


# ==============================================================================
# 4. Main Validator Execution
# ==============================================================================
def main():
    workspace = Path(__file__).resolve().parent.parent
    host_vars_dir = workspace / "inventory" / "host_vars"

    files = sorted(host_vars_dir.glob("*.yml"))
    if not files:
        print(f"❌ Error: No YAML files found in {host_vars_dir}")
        sys.exit(1)

    print(f"🔍 Validating {len(files)} ISP Business network data model(s) with Pydantic v2...\n")
    has_errors = False

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)

            role = raw_data.get("device_role")
            if role == "core-bng-router":
                model = CoreBNGRouterModel(**raw_data)
                print(
                    f"✅ {file_path.name}: Core BNG Router Validated! ("
                    f"Site: {model.site_name}, ASN: {model.bgp.local_asn}, "
                    f"BGP Peers: {len(model.bgp.peers)}, Packages: {len(model.pppoe_server.packages)})"
                )
            elif role == "ftth-olt":
                model = GPONOLTModel(**raw_data)
                print(
                    f"✅ {file_path.name}: FTTH GPON OLT Validated! ("
                    f"Site: {model.site_name}, PON Ports: {len(model.pon_ports)}, "
                    f"Uplink VLANs: {model.uplink_vlans})"
                )
            else:
                print(f"⚠️ {file_path.name}: Skipped unknown role: {role}")
        except Exception as e:
            print(f"❌ {file_path.name}: Validation Failed!\n   {e}\n")
            has_errors = True

    if has_errors:
        print("\n💥 Schema validation failed for one or more ISP data models.")
        sys.exit(1)
    else:
        print("\n🎉 All ISP Business network data models passed validation successfully!")


if __name__ == "__main__":
    main()
