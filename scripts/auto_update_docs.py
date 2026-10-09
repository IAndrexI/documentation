#!/usr/bin/env python3
"""
Protutech Ecosystem - Automated Documentation Synchronizer
Monitors Proxmox VE containers/VMs and GitHub repositories.
Automatically generates/updates documentation markdown files, updates navigation,
and rebuilds the static MkDocs website.
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from datetime import datetime

# Root paths
SCRIPT_DIR = Path(__file__).resolve().parent
DOCS_ROOT = SCRIPT_DIR.parent
PAGES_DIR = DOCS_ROOT / "docs"
MKDOCS_FILE = DOCS_ROOT / "mkdocs.yml"

# Proxmox VE API Configuration
PVE_HOST = os.getenv("PVE_HOST", "192.168.0.2")
PVE_PORT = os.getenv("PVE_PORT", "8006")
PVE_NODE = os.getenv("PVE_NODE", "pve")
PVE_TOKEN_ID = os.getenv("PVE_TOKEN_ID", "")
PVE_TOKEN_SECRET = os.getenv("PVE_TOKEN_SECRET", "")
PVE_VERIFY_SSL = os.getenv("PVE_VERIFY_SSL", "false").lower() == "true"

# GitHub Configuration
GITHUB_USER = os.getenv("GITHUB_USER", "IAndrexI")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

def log(msg):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] [AutoUpdate] {msg}", flush=True)

def query_proxmox_containers():
    """Queries Proxmox VE API for active and configured LXC containers."""
    if not PVE_TOKEN_ID or not PVE_TOKEN_SECRET:
        log("Proxmox API tokens not set (PVE_TOKEN_ID / PVE_TOKEN_SECRET). Checking pvesh CLI fallback...")
        try:
            # Fallback if running directly on Proxmox node shell
            res = subprocess.run(["pvesh", "get", f"/nodes/{PVE_NODE}/lxc", "--output-format", "json"],
                                 capture_output=True, text=True, check=True)
            return json.loads(res.stdout)
        except Exception:
            log("No direct pvesh available. Skipping live Proxmox query.")
            return []

    url = f"https://{PVE_HOST}:{PVE_PORT}/api2/json/nodes/{PVE_NODE}/lxc"
    headers = {
        "Authorization": f"PVEAPIToken={PVE_TOKEN_ID}={PVE_TOKEN_SECRET}",
        "Accept": "application/json"
    }

    ctx = None
    if not PVE_VERIFY_SSL:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("data", [])
    except Exception as e:
        log(f"Error querying Proxmox API: {e}")
        return []

def query_github_repositories():
    """Queries GitHub API for the user's latest repositories."""
    url = f"https://api.github.com/users/{GITHUB_USER}/repos?sort=updated&per_page=30"
    headers = {
        "User-Agent": "Protutech-Docs-Sync",
        "Accept": "application/vnd.github.v3+json"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log(f"Error querying GitHub API: {e}")
        return []

def update_cluster_manifest(containers, repos):
    """Generates an updated dynamic inventory markdown page."""
    manifest_path = PAGES_DIR / "infra" / "proxmox-live-inventory.md"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Proxmox Cluster Live Container Inventory",
        "",
        "This inventory page is automatically synchronized with Proxmox VE hypervisor state and GitHub.",
        f"**Last Sync Timestamp:** `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`",
        "",
        "---",
        "",
        "## ⬡ Live Proxmox LXC Containers",
        "",
        "| VMID | Container Name | Status | CPU Limit | RAM Max | Disk Usage |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    if containers:
        for c in sorted(containers, key=lambda x: int(x.get("vmid", 0))):
            vmid = c.get("vmid", "Unknown")
            name = c.get("name", "Unknown")
            status = c.get("status", "Unknown")
            cpus = c.get("cpus", 1)
            maxmem_gb = round(c.get("maxmem", 0) / (1024**3), 2)
            disk_gb = round(c.get("maxdisk", 0) / (1024**3), 2)
            badge = "● Running" if status == "running" else "○ Stopped"
            lines.append(f"| `{vmid}` | **{name}** | {badge} | {cpus} vCPU | {maxmem_gb} GB | {disk_gb} GB |")
    else:
        lines.append("| *N/A* | *No live containers retrieved (check API credentials)* | - | - | - | - |")

    lines.extend([
        "",
        "---",
        "",
        "## ⬡ Synchronized GitHub Repositories",
        "",
        "| Repository | Description | Last Updated | Default Branch |",
        "| :--- | :--- | :--- | :--- |"
    ])

    if repos and isinstance(repos, list):
        for r in repos[:15]:
            name = r.get("name", "")
            desc = r.get("description") or "Homelab service component"
            updated = r.get("updated_at", "")[:10]
            branch = r.get("default_branch", "main")
            html_url = r.get("html_url", "#")
            lines.append(f"| [{name}]({html_url}) | {desc} | `{updated}` | `{branch}` |")
    else:
        lines.append("| *N/A* | *No GitHub repositories retrieved* | - | - |")

    manifest_path.write_text("\n".join(lines), encoding="utf-8")
    log(f"Updated live inventory page at: {manifest_path}")

def rebuild_mkdocs():
    """Runs clean MkDocs build."""
    log("Rebuilding static documentation website...")
    try:
        cmd = [sys.executable, "-m", "mkdocs", "build", "--clean"]
        subprocess.run(cmd, cwd=DOCS_ROOT, check=True)
        log("Website rebuild completed successfully.")
    except Exception as e:
        log(f"Failed to rebuild MkDocs: {e}")

def main():
    log("Starting automated documentation sync cycle...")
    containers = query_proxmox_containers()
    repos = query_github_repositories()

    update_cluster_manifest(containers, repos)
    rebuild_mkdocs()
    log("Sync cycle finished.")

if __name__ == "__main__":
    main()
