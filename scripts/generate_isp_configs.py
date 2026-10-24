#!/usr/bin/env python3
"""
Configuration Generation Script for ISP Business Network Automation.
Renders production-ready MikroTik RouterOS v7 (.rsc) configuration for Core BNG
and FTTH GPON OLT configuration (.cfg) from Jinja2 templates and host_vars.
"""

import sys
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
HOST_VARS_DIR = BASE_DIR / "inventory" / "host_vars"
GROUP_VARS_DIR = BASE_DIR / "inventory" / "group_vars" / "all"
OUTPUT_DIR = BASE_DIR / "generated_configs"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load common group vars
    common_vars = {}
    main_vars_file = GROUP_VARS_DIR / "main.yml"
    if main_vars_file.exists():
        with open(main_vars_file, "r", encoding="utf-8") as f:
            common_vars = yaml.safe_load(f) or {}

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    bng_template = env.get_template("mikrotik_isp_bng.j2")
    olt_template = env.get_template("gpon_olt_config.j2")

    host_files = sorted(HOST_VARS_DIR.glob("*.yml"))
    print(f"🚀 Rendering ISP configurations for {len(host_files)} devices...\n")

    for hf in host_files:
        device_key = hf.stem
        with open(hf, "r", encoding="utf-8") as f:
            host_data = yaml.safe_load(f)

        merged_context = {**common_vars, **host_data}
        role = host_data.get("device_role")

        if role == "core-bng-router":
            rendered = bng_template.render(merged_context)
            out_file = OUTPUT_DIR / f"{device_key}.rsc"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(rendered)
            print(f"📄 Generated Core BNG: {out_file.relative_to(BASE_DIR)} ({len(rendered.splitlines())} lines)")

        elif role == "ftth-olt":
            rendered = olt_template.render(merged_context)
            out_file = OUTPUT_DIR / f"{device_key}.cfg"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(rendered)
            print(f"📄 Generated GPON OLT: {out_file.relative_to(BASE_DIR)} ({len(rendered.splitlines())} lines)")

    print("\n✅ All ISP Network configurations generated successfully!")


if __name__ == "__main__":
    main()
