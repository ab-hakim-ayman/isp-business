# 🌐 ISP Business Network Automation (FTTH, BGP, CGNAT & NetDevOps)

An enterprise-grade, production-ready NetDevOps automation framework for an **Internet Service Provider (ISP) & WISP Business** powered by **MikroTik RouterOS v7 Core BNG**, **Dual Upstream BGP Multi-homing (IIG Transit & BDIX Peering)**, **Carrier-Grade NAT (CGNAT RFC 6598)**, **FTTH GPON OLT Provisioning**, **PPPoE Broadband Server**, and **Campus Hotspot Captive Portal**.

---

## 📌 Architecture Highlights

* **Autonomous System & BGP Multi-homing:**
  * **ISP ASN:** `AS139999` (CloudApex Telecom)
  * **Public IPv4 Allocated Block:** `103.200.8.0/22` (1024 Public IPs)
  * **Upstream 1 (Global Transit):** 10G link to IIG (`AS64512`, Local Preference 100)
  * **Upstream 2 (Domestic Peering):** 10G link to BDIX (`AS64513`, Local Preference 200 for lightning-fast YouTube, Facebook, and BDIX Cache)
* **Carrier-Grade NAT (CGNAT RFC 6598):**
  * **Subscriber Subnet:** `100.64.0.0/18` (16,384 private IPs for broadband clients)
  * **Public Pool:** `103.200.8.10-103.200.8.30` (Dynamic high-concurrency source NAT with optimized conntrack table supporting 500,000+ sessions).
* **FTTH PPPoE Broadband Access (VLAN 100):**
  * Hardware-accelerated PPPoE server on MikroTik RouterOS v7.
  * Centralized **RADIUS AAA & Billing Integration** (FreeRADIUS / daloRADIUS on Port 1812/1813 with CoA Disconnect on Port 3799).
  * 4 Pre-Configured Commercial Packages (Starter-15M, Standard-30M, Premium-60M, Corporate-100M) with BDIX Burst speed.
* **Campus & Public Wi-Fi Hotspot (VLAN 200):**
  * Subnet `172.16.200.0/23` (500+ concurrent students/visitors).
  * Captive portal with trial access (30 mins / 5 Mbps) and HTTP-CHAP user authentication.
* **FTTH GPON OLT Automation Layer:**
  * Automated Huawei/ZTE/V-SOL compatible GPON OLT profile generator.
  * Type 4 (Best-Effort) and Type 1 (CIR Dedicated) DBA Profiles.
  * Auto-find ONU discovery and automatic Line/Service profile binding.
* **NetDevOps Toolchain:**
  * **NetBox v4.7.3:** Central Source of Truth (DCIM & IPAM)
  * **Pydantic v2:** Strict IPv4 CIDR and ASN schema validation
  * **Jinja2:** Declarative configuration templating
  * **Ansible:** Automated orchestration and multi-device deployment

---

## 📁 Project Directory Structure

```text
isp-business/
├── README.md                           # Master ISP Architecture and Runbook
├── ansible.cfg                         # Ansible configuration with Vault and RouterOS plugins
├── .vault_pass                         # Secret password file for Ansible Vault
├── .yamllint                           # YAML syntax and code quality rules
├── docker-compose.monitoring.yml       # Observability Stack (Prometheus + Grafana + Exporter)
│
├── inventory/
│   ├── hosts.ini                       # Core BNG & OLT static inventory
│   ├── netbox.yml                      # NetBox Dynamic Inventory plugin
│   ├── group_vars/
│   │   └── all/
│   │       ├── main.yml                # Global ISP DNS, NTP, ASN, and CGNAT settings
│   │       └── vault.yml               # AES-256 encrypted router & RADIUS secrets
│   └── host_vars/
│       ├── core_bng_router.yml         # BNG data model (BGP, CGNAT, PPPoE, Hotspot)
│       └── gpon_olt_01.yml             # GPON OLT data model (PON ports, DBA profiles)
│
├── templates/
│   ├── mikrotik_isp_bng.j2             # Master MikroTik RouterOS v7 Core BNG Jinja2 template
│   └── gpon_olt_config.j2              # FTTH GPON OLT configuration template
│
├── playbooks/
│   ├── deploy_isp.yml                  # Master deployment playbook (generate & push)
│   └── verify_subscribers.yml          # Subscriber & BGP verification playbook
│
├── scripts/
│   ├── validate_isp_schema.py          # Pydantic v2 schema validation script
│   ├── generate_isp_configs.py         # Configuration renderer for BNG and OLT
│   └── netbox_isp_sync.py              # Syncs ISP sites, devices, prefixes, and VLANs to NetBox
│
├── configs/
│   ├── prometheus/prometheus.yml       # Prometheus scraping config
│   ├── mikrotik-exporter/config.yml    # BGP, PPPoE & Interface metrics scraper
│   └── grafana/                        # Pre-provisioned ISP Grafana dashboard
│
└── generated_configs/                  # Production-ready configuration scripts
    ├── core_bng_router.rsc             # MikroTik Core BNG script (/import file-name=core_bng_router.rsc)
    └── gpon_olt_01.cfg                 # GPON OLT production configuration script
```

---

## 📑 Broadband Packages & Bandwidth Profiles

| Package Name | Global Internet Speed | BDIX Domestic Speed | Burst Limit | Address Pool | Monthly Price |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Starter-15M** | 15 Mbps (1:8) | 40 Mbps (1:1) | 40M / 10s | `pool-pppoe-subscribers` | 500 BDT |
| **Standard-30M** | 30 Mbps (1:8) | 75 Mbps (1:1) | 75M / 10s | `pool-pppoe-subscribers` | 800 BDT |
| **Premium-60M** | 60 Mbps (1:4) | 120 Mbps (1:1) | 120M / 10s | `pool-pppoe-subscribers` | 1,200 BDT |
| **Corporate-100M**| 100 Mbps (1:1 CIR) | 100 Mbps (1:1) | 100M (No Burst) | Dedicated / Static IP | 3,000 BDT |

---

## 📑 IPAM, BGP & CGNAT Addressing Plan

| Network Zone | Subnet Block | Gateway / IP | Purpose |
| :--- | :--- | :--- | :--- |
| **ISP Public BGP Block** | `103.200.8.0/22` | `103.200.8.1` (Router-ID) | Global Route Announcement (AS139999). |
| **Upstream IIG Transit** | `203.0.113.0/30` | `203.0.113.1` (IIG Peer) | 10G Global Internet Transit (sfp-sfpplus1). |
| **BDIX Domestic Peering**| `198.51.100.0/30`| `198.51.100.1` (BDIX Peer) | 10G Domestic IXP Peering (sfp-sfpplus2). |
| **CGNAT Subscriber Pool**| `100.64.0.0/18` | `100.64.0.1` | RFC 6598 Shared IP Pool for 16,384 Subscribers. |
| **Public CGNAT NAT Pool**| `103.200.8.10-30`| N/A | High-capacity Outbound Source NAT IP Pool. |
| **Campus Wi-Fi Hotspot** | `172.16.200.0/23`| `172.16.200.1` | Captive Portal for 500+ Concurrent Users (VLAN 200). |
| **Out-of-Band Management**| `10.10.1.0/24` | `10.10.1.1` | Core Router, OLT, and Billing Management (VLAN 10). |

---

## 🚀 Quick Start & Operations Guide

### 1. Validate Data Models with Pydantic v2
Ensure there are no invalid ASNs, overlapping subnets, or CIDR boundary errors:
```bash
python3 scripts/validate_isp_schema.py
```

### 2. Generate Production Configurations
Render MikroTik RouterOS v7 `.rsc` and GPON OLT `.cfg` files:
```bash
python3 scripts/generate_isp_configs.py
```
Output files will be generated in `generated_configs/`:
* `generated_configs/core_bng_router.rsc`
* `generated_configs/gpon_olt_01.cfg`

### 3. Synchronize to NetBox (Central Source of Truth)
Push the ISP topology, AS139999, BNG routers, OLTs, CGNAT pools, and VLANs to NetBox:
```bash
python3 scripts/netbox_isp_sync.py
```
View the live data at: **[http://localhost:8000](http://localhost:8000)** (User: `admin` / Password: `admin`).

### 4. Deploy via Ansible
Deploy configurations across both Core BNG and GPON OLT devices:
```bash
ansible-playbook -i inventory/hosts.ini playbooks/deploy_isp.yml
```
Or pull dynamically from NetBox:
```bash
ansible-playbook -i inventory/netbox.yml playbooks/deploy_isp.yml
```

### 5. Verify Network & Subscriber Health
Check BGP sessions, active PPPoE subscribers, and CGNAT connection counts:
```bash
ansible-playbook -i inventory/hosts.ini playbooks/verify_subscribers.yml
```

---

## 📊 Observability & Telemetry (Prometheus & Grafana)

The ISP Business includes a dedicated monitoring stack running via Docker Compose:

```bash
# Start ISP Prometheus, Grafana, and MikroTik Exporter
docker compose -f docker-compose.monitoring.yml up -d
```

### 🖥️ Dashboards & Endpoints:
* **Grafana Dashboard:** [http://localhost:3002](http://localhost:3002)
  * **Credentials:** `admin` / `admin`
  * **Auto-Provisioned Dashboard:** `ISP Business Core Network Overview`
  * **Panels Included:**
    * ⚡ **Core BNG Health:** CPU load, Free RAM, System Uptime
    * 🌐 **10G Transit Traffic:** Primary IIG Global Transit vs BDIX Domestic Peering (RX/TX Mbps)
    * 🏢 **Broadband Subscribers:** VLAN 100 FTTH PPPoE aggregated throughput
    * 📶 **Campus Wi-Fi Hotspot:** VLAN 200 bandwidth and concurrent active users
    * 🛡️ **CGNAT Telemetry:** Total active NAT connections and conntrack table utilization
* **Prometheus Metrics:** [http://localhost:9092](http://localhost:9092)
* **MikroTik Exporter Metrics:** [http://localhost:9437/metrics](http://localhost:9437/metrics)
