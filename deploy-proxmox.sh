#!/usr/bin/env bash
# ==============================================================================
# Protutech Docs - Proxmox VE Automated LXC Provisioning & Deployment Script
# ==============================================================================
# Usage: Run this script directly on your Proxmox VE Node Shell:
#   curl -fsSL https://raw.githubusercontent.com/IAndrexI/documentation/main/deploy-proxmox.sh | bash
# ==============================================================================

set -euo pipefail

CT_ID="${1:-110}"
CT_NAME="protutech-docs"
CT_RAM="512"
CT_DISK="4"
CT_CORES="1"
CT_STORAGE="local-zfs"
BRIDGE="vmbr0"

echo "=========================================================="
echo "  🚀 Protutech Documentation: Proxmox LXC Deployment"
echo "=========================================================="
echo "Container ID:   ${CT_ID}"
echo "Container Name: ${CT_NAME}"
echo "RAM / Disk:     ${CT_RAM} MB / ${CT_DISK} GB"
echo "Storage Pool:   ${CT_STORAGE}"
echo "=========================================================="

# Check if container ID already exists
if pct status "${CT_ID}" &>/dev/null; then
  echo "⚠️ Container ID ${CT_ID} already exists! Checking status..."
  pct status "${CT_ID}"
else
  # Locate latest Debian 12 template on Proxmox host
  echo "📦 Finding Debian 12 container template..."
  TEMPLATE=$(pveam list local | grep debian-12 | awk '{print $1}' | tail -n1 || true)

  if [ -z "${TEMPLATE}" ]; then
    echo "⬇️ Downloading debian-12-standard template..."
    pveam update
    pveam download local debian-12-standard_12.7-1_amd64.tar.zst || pveam download local $(pveam available | grep debian-12 | head -n1 | awk '{print $2}')
    TEMPLATE=$(pveam list local | grep debian-12 | awk '{print $1}' | tail -n1)
  fi

  echo "🛠️ Creating unprivileged LXC container ${CT_ID}..."
  pct create "${CT_ID}" "${TEMPLATE}" \
    --hostname "${CT_NAME}" \
    --cores "${CT_CORES}" \
    --memory "${CT_RAM}" \
    --swap 256 \
    --rootfs "${CT_STORAGE}:${CT_DISK}" \
    --net0 name=eth0,bridge="${BRIDGE}",ip=dhcp,firewall=1 \
    --features nesting=1 \
    --unprivileged 1 \
    --onboot 1 \
    --start 1

  echo "⏳ Waiting for container network allocation..."
  sleep 8
fi

echo "📥 Provisioning inside container ${CT_ID}..."
pct exec "${CT_ID}" -- bash -c "
  apt-get update -y &&
  apt-get install -y nginx git curl python3-pip python3-venv &&
  rm -rf /var/www/html/* &&
  git clone https://github.com/IAndrexI/documentation.git /tmp/docs &&
  python3 -m venv /opt/docs-venv &&
  /opt/docs-venv/bin/pip install --upgrade pip &&
  /opt/docs-venv/bin/pip install mkdocs-material mkdocs-minify-plugin &&
  cd /tmp/docs &&
  /opt/docs-venv/bin/mkdocs build --clean &&
  cp -r /tmp/docs/site/* /var/www/html/ &&
  chown -R www-data:www-data /var/www/html &&
  systemctl restart nginx
"

IP_ADDR=$(pct exec "${CT_ID}" -- ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' || echo "DHCP")

echo "=========================================================="
echo "  ✅ Deployment Complete!"
echo "  Documentation is live on Proxmox LXC ${CT_ID}:"
echo "  URL: http://${IP_ADDR}/"
echo "=========================================================="
