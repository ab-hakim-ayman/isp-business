# ==============================================================================
# MikroTik RouterOS v7 Production Configuration Script
# ISP Core BNG / BRAS Router Automation Engine
# Hostname: isp-core-bng01 | Site: ISP-NOC-Dhaka | ASN: AS139999
# ==============================================================================

/system identity set name="isp-core-bng01"
/system clock set time-zone-name="Asia/Dhaka"

# ------------------------------------------------------------------------------
# 1. Interface Lists
# ------------------------------------------------------------------------------
/interface list add name=WAN_UPSTREAM
/interface list add name=PON_ACCESS
/interface list add name=CAMPUS_HOTSPOT
/interface list add name=MANAGEMENT

/interface list member add interface=sfp-sfpplus1 list=WAN_UPSTREAM
/interface list member add interface=sfp-sfpplus2 list=WAN_UPSTREAM

# ------------------------------------------------------------------------------
# 2. OLT Downlink Bridge & VLAN Setup (vlan-filtering enabled)
# ------------------------------------------------------------------------------
/interface bridge add name=bridge-olt-downlink vlan-filtering=yes protocol-mode=rstp

/interface bridge port add bridge=bridge-olt-downlink interface=sfp-sfpplus3
/interface bridge port add bridge=bridge-olt-downlink interface=sfp-sfpplus4

# VLAN 10: Management
/interface vlan add interface=bridge-olt-downlink name=vlan10-mgmt vlan-id=10
/interface list member add interface=vlan10-mgmt list=MANAGEMENT
/ip address add address=10.10.1.1/24 interface=vlan10-mgmt comment="Out-of-Band Management IP"

# VLAN 100: FTTH PPPoE PON Access
/interface vlan add interface=bridge-olt-downlink name=vlan100-pon-access vlan-id=100
/interface list member add interface=vlan100-pon-access list=PON_ACCESS

# VLAN 200: Campus / Public Wi-Fi Hotspot
/interface vlan add interface=bridge-olt-downlink name=vlan200-hotspot vlan-id=200
/interface list member add interface=vlan200-hotspot list=CAMPUS_HOTSPOT

# Bridge VLAN Trunk / Tagging Table
/interface bridge vlan add bridge=bridge-olt-downlink tagged=sfp-sfpplus3,sfp-sfpplus4,bridge-olt-downlink vlan-ids=10,100,200,300 comment="ISP Subscriber & Uplink VLANs"

# ------------------------------------------------------------------------------
# 3. BGP Upstream & BDIX Peering (RouterOS v7)
# ------------------------------------------------------------------------------
# Upstream WAN Interface IP Addresses
/ip address add address=203.0.113.2/30 interface=sfp-sfpplus1 comment="10G Primary Global Transit via IIG"
/ip address add address=198.51.100.2/30 interface=sfp-sfpplus2 comment="10G Domestic Peering via BDIX"

# BGP Template Definition
/routing bgp template add name=isp-default-template as=139999 router-id=103.200.8.1 client-to-client-reflection=no

# Blackhole Routes for ISP Announced Prefix
/ip route add dst-address=103.200.8.0/22 blackhole comment="BGP Announced Block Anchor (103.200.8.0/22)"

# BGP Peering Connections
/routing bgp connection add name="IIG-Summit-Transit" remote.address=203.0.113.1 remote.as=64512 local.role=ebgp local.address=203.0.113.2 templates=isp-default-template output.network="103.200.8.0/22" routing-table=main comment="10G Primary Global Transit via IIG (Role: upstream)"
/routing bgp connection add name="BDIX-Domestic-Peering" remote.address=198.51.100.1 remote.as=64513 local.role=ebgp local.address=198.51.100.2 templates=isp-default-template output.network="103.200.8.0/22" routing-table=main comment="10G Domestic Peering via BDIX (Role: ixp)"

# BGP Routing Filters: BDIX Local Preference 200, Transit Local Preference 100
/routing filter rule add chain=bgp-in-filters rule="if (bgp-communities includes 139999:100) { set bgp-local-pref 200; accept; } else { set bgp-local-pref 100; accept; }"

# ------------------------------------------------------------------------------
# 4. CGNAT (Carrier-Grade NAT RFC 6598) & Conntrack Optimization
# ------------------------------------------------------------------------------
# CGNAT Public Pool
/ip pool add name=cgnat-public-pool ranges=103.200.8.10-103.200.8.30 comment="Public IP Pool for CGNAT Subscribers"

# Dynamic Deterministic Source NAT
/ip firewall nat add action=src-nat chain=srcnat src-address=100.64.0.0/18 to-addresses=103.200.8.10-103.200.8.30 out-interface-list=WAN_UPSTREAM comment="CGNAT RFC 6598 Subscribers to Public Pool"

# Conntrack High-Capacity Tuning for ISP Subscriber Scale
/ip firewall connection tracking set tcp-established-timeout=12h tcp-syn-received-timeout=15s generic-timeout=5m max-entries=524288

# ------------------------------------------------------------------------------
# 5. FTTH PPPoE Broadband Server, Packages & RADIUS Billing
# ------------------------------------------------------------------------------
# Subscriber Address Pool
/ip pool add name=pool-pppoe-subscribers ranges=100.64.0.10-100.64.63.250 comment="PPPoE Subscriber Private IP Pool"
/ip address add address="100.64.0.1/32" network=100.64.0.1 interface=vlan100-pon-access comment="PPPoE Gateway Anchor"

# PPPoE Bandwidth Packages & Rate Limiting Profiles
/ppp profile add name="Starter-15M" local-address=100.64.0.1 remote-address=pool-pppoe-subscribers rate-limit="15M/15M" dns-server=1.1.1.1,8.8.8.8 comment="Package: Starter-15M (500 BDT)"
/ppp profile add name="Standard-30M" local-address=100.64.0.1 remote-address=pool-pppoe-subscribers rate-limit="30M/30M" dns-server=1.1.1.1,8.8.8.8 comment="Package: Standard-30M (800 BDT)"
/ppp profile add name="Premium-60M" local-address=100.64.0.1 remote-address=pool-pppoe-subscribers rate-limit="60M/60M" dns-server=1.1.1.1,8.8.8.8 comment="Package: Premium-60M (1200 BDT)"
/ppp profile add name="Corporate-100M" local-address=100.64.0.1 remote-address=pool-pppoe-subscribers rate-limit="100M/100M" dns-server=1.1.1.1,8.8.8.8 comment="Package: Corporate-100M (3000 BDT)"

# PPPoE Server Service Binding
/interface pppoe-server server add service-name=isp-broadband-pppoe interface=vlan100-pon-access default-profile=Standard-30M max-mtu=1480 max-mru=1480 authentication=pap,chap,mschap2 disabled=no

# RADIUS Billing Integration (FreeRADIUS / daloRADIUS)
/radius add service=ppp address=10.10.1.50 secret="RadiusSecureIspKey2026!" authentication-port=1812 accounting-port=1813 timeout=3s comment="Central ISP Billing RADIUS"
/radius incoming set accept=yes port=3799
/ppp aaa set use-radius=yes accounting=yes interim-update=5m

# Demo PPPoE Subscriber Accounts
/ppp secret add name="user_demo_gulshan" password="UserPass2026!" profile="Standard-30M" service=pppoe comment="Demo FTTH Home Broadband User"
/ppp secret add name="corp_client_banani" password="CorpPass2026!" profile="Corporate-100M" service=pppoe comment="Demo Corporate Leased Line Client"

# ------------------------------------------------------------------------------
# 6. Campus / Public Wi-Fi Hotspot (Captive Portal)
# ------------------------------------------------------------------------------
/ip address add address=172.16.200.1/23 interface=vlan200-hotspot comment="Campus Hotspot Gateway"
/ip pool add name=pool-hotspot ranges=172.16.200.50-172.16.201.250 comment="Campus Hotspot Pool"

/ip dhcp-server add address-pool=pool-hotspot interface=vlan200-hotspot name=dhcp-hotspot lease-time=1h disabled=no
/ip dhcp-server network add address=172.16.200.0/23 gateway=172.16.200.1 dns-server=1.1.1.1,8.8.8.8 comment="Campus Hotspot Network"

/ip hotspot profile add name=hsp-profile hotspot-address=172.16.200.1 html-directory=hotspot login-by=http-chap,trial trial-uptime-limit=30m trial-user-profile=trial-profile
/ip hotspot user profile add name=trial-profile rate-limit="5M/5M" shared-users=1 comment="Free Trial Profile"
/ip hotspot add name="campus-hotspot" interface=vlan200-hotspot profile=hsp-profile address-pool=pool-hotspot disabled=no

/ip firewall nat add action=masquerade chain=srcnat src-address=172.16.200.0/23 out-interface-list=WAN_UPSTREAM comment="Campus Hotspot Internet Masquerade"

# ------------------------------------------------------------------------------
# 7. Fair-Share QoS Traffic Engineering (PCQ)
# ------------------------------------------------------------------------------
/queue type add name="isp-pcq-down" kind=pcq pcq-classifier=dst-address pcq-rate=0 comment="Dynamic Downlink Shaper"
/queue type add name="isp-pcq-up" kind=pcq pcq-classifier=src-address pcq-rate=0 comment="Dynamic Uplink Shaper"

# ------------------------------------------------------------------------------
# 8. Security & Firewall Protection
# ------------------------------------------------------------------------------
/ip firewall filter
add action=accept chain=input connection-state=established,related comment="Accept Established/Related"
add action=drop chain=input connection-state=invalid comment="Drop Invalid Input"
add action=accept chain=input protocol=icmp comment="Allow ICMP Diagnostic Ping"

# Allow BGP Peering (TCP 179) from WAN Upstreams
add action=accept chain=input dst-port=179 protocol=tcp in-interface-list=WAN_UPSTREAM comment="Allow BGP from Upstream"

# Allow PPPoE Discovery (PPPoE & PPPoE-Discovery Protocols)
add action=accept chain=input protocol=gre comment="Allow GRE"

# Management Access: Only allowed from Management VLAN 10
add action=accept chain=input in-interface=vlan10-mgmt comment="Allow Full Admin from Management VLAN"
add action=accept chain=input dst-port=161 protocol=udp in-interface=vlan10-mgmt comment="Allow SNMP Polling"
add action=accept chain=input dst-port=8728,8729 protocol=tcp in-interface=vlan10-mgmt comment="Allow RouterOS API"

# Drop Unwanted Access to Core Router
add action=drop chain=input in-interface-list=WAN_UPSTREAM comment="Block Router Services from Public Internet"

# Forward Chain: FastTrack
add action=fasttrack-connection chain=forward connection-state=established,related hw-offload=yes comment="FastTrack Established/Related"
add action=accept chain=forward connection-state=established,related comment="Accept Established/Related Forward"
add action=drop chain=forward connection-state=invalid comment="Drop Invalid Forward"

# ------------------------------------------------------------------------------
# 9. Observability, SNMP & Prometheus Exporter
# ------------------------------------------------------------------------------
/snmp set enabled=yes contact="noc@cloudapex.net" location="ISP-NOC-Dhaka"
/snmp community add name=isp-monitor addresses=0.0.0.0/0 read-access=yes security=none

/user group add name=monitoring policy=read,api,test comment="Read-only monitoring policy"
/user add name=prometheus group=monitoring password="IspPromMonSecure2026!" comment="Prometheus Exporter Scraper"
/ip service enable api

# ==============================================================================
# ISP Core BNG Router configuration rendered successfully.
# ==============================================================================