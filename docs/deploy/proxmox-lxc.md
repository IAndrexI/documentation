# Proxmox LXC Microservice Deployment Guide

This guide details how to deploy and maintain the Protutech Engineering Documentation platform directly on Proxmox VE as a dedicated, unprivileged Debian Linux container (LXC). Running the documentation inside a native LXC microservice provides sub-millisecond execution, direct ZFS dataset integration, and strict Linux kernel user namespace sandboxing while consuming less than 15 MB of total RAM.

---

## 1. Automated Provisioning via Turnkey Host Script

For rapid deployment, we maintain an automated setup script that executes on the Proxmox VE host shell. The script provisions container ID `100`, configures unprivileged UID mappings, downloads the Debian 12 minimal rootfs, installs runtime packages, and configures an Nginx service daemon automatically:

```bash
# Execute in the Proxmox VE 9.2 Host Root Shell
bash -c "$(curl -fsSL https://raw.githubusercontent.com/IAndrexI/documentation/main/deploy-proxmox.sh)"
```

The script verifies Proxmox version compatibility, checks for free disk allocation in `local-zfs`, and outputs the assigned private IP address and port bindings upon completion.

---

## 2. Programmatic Container Creation via `pct` CLI

If you manage your homelab infrastructure via scripts, Ansible, or CLI automation, you can provision the container using Proxmox's native `pct create` utility.

### Step 1: Provision Container Specification

Run the following command on the Proxmox host node:

```bash
# Download the Debian 12 Standard Template if not already present
pveam update
pveam download local debian-12-standard_12.7-1_amd64.tar.zst

# Provision Unprivileged LXC Container
pct create 100 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname protutech-docs \
  --ostype debian \
  --arch amd64 \
  --cores 1 \
  --memory 512 \
  --swap 256 \
  --storage local-zfs \
  --rootfs local-zfs:4 \
  --net0 name=eth0,bridge=vmbr0,firewall=1,ip=192.168.0.100/24,gw=192.168.0.1 \
  --nameserver 192.168.0.102 \
  --searchdomain protutech.vip \
  --features nesting=1 \
  --unprivileged 1 \
  --onboot 1 \
  --start 1
```

### Parameter Breakdown & Architectural Rationale

| Flag / Parameter | Value | Technical Rationale |
| :--- | :--- | :--- |
| `--unprivileged 1` | Unprivileged User Namespaces | Maps `root` inside the container (`UID 0`) to `UID 100000` on the host kernel. Prevents privilege escalation escapes. |
| `--cores 1` | 1 CPU Core | Static HTML serving by Nginx requires minimal processing capacity. |
| `--memory 512` | 512 MB RAM Ceiling | Production RAM consumption is $<15\text{MB}$. Generous headroom for compiler tasks. |
| `--rootfs local-zfs:4` | 4 GB ZFS Subvolume | Sufficient storage for operating system packages, Nginx binaries, and compiled documentation artifacts. |
| `--features nesting=1` | cgroups v2 Nesting | Enables systemd service isolation and sub-process accounting inside Debian 12. |
| `--onboot 1` | Automatic Boot Order | Automatically starts container upon hypervisor hardware reboot. |

---

## 3. Kernel User Namespace Mapping Verification

Because the container is unprivileged, verify that Linux user and group namespace translation is enforced:

```bash
# Check container configuration file on Proxmox host
cat /etc/pve/lxc/100.conf | grep unprivileged
# Output: unprivileged: 1

# Inspect the subuid and subgid range allocations on the host
cat /etc/subuid
# root:100000:65536
```

Any process executing as `root` (UID 0) inside container 100 has zero administrative authority on the Proxmox host; the kernel strictly treats it as unprivileged user ID `100000`.

---

## 4. In-Container Software Configuration & Web Serving

Once the container is running, enter the container console and initialize the environment:

```bash
# Enter the container environment from the host
pct enter 100

# 1. Update package indices and install runtime software
apt update && apt install -y nginx git curl rsync

# 2. Configure dedicated directory for documentation source and builds
mkdir -p /opt/protutech-docs
cd /opt/protutech-docs

# 3. Clone the official documentation repository
git clone https://github.com/IAndrexI/documentation.git .

# 4. Synchronize pre-compiled static assets to Nginx web root
rsync -av --delete /opt/protutech-docs/site/ /var/www/html/

# 5. Enforce strict permissions
chown -R www-data:www-data /var/www/html
chmod -R 755 /var/www/html
```

### Production Nginx Site Configuration inside Container

Deploy this site configuration at `/etc/nginx/sites-available/protutech-docs`:

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name docs.protutech.vip localhost;

    root /var/www/html;
    index index.html;

    # Gzip Compression Optimization
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/json image/svg+xml;

    # Immutable Asset Cache Headers (1 Year)
    location ~* \.(?:css|js|woff2?|svg|png|jpg|ico)$ {
        expires 1y;
        add_header Cache-Control "public, max-age=31536000, immutable";
        access_log off;
    }

    # HTML Documents (Fast Revalidation)
    location ~* \.html$ {
        expires 1h;
        add_header Cache-Control "public, max-age=3600, must-revalidate";
    }

    location / {
        try_files $uri $uri/ /index.html =404;
    }
}
```

Enable the configuration and reload the web server:

```bash
ln -sf /etc/nginx/sites-available/protutech-docs /etc/nginx/sites-enabled/default
systemctl restart nginx
```

---

## 5. Automated Systemd Git Synchronization Timer

To ensure that the hosted documentation automatically syncs with your GitHub repository whenever documentation is committed, configure a dedicated systemd service and timer inside the container.

### Step 1: Create Sync Script (`/usr/local/bin/sync-docs.sh`)

```bash
#!/bin/bash
set -euo pipefail

DOCS_DIR="/opt/protutech-docs"
WEB_ROOT="/var/www/html"

cd "$DOCS_DIR"

# Fetch latest origin state
git fetch origin main --quiet

# Check if origin has new commits
LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse origin/main)

if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
    echo "[$(date -Iseconds)] New documentation commit detected. Syncing..."
    git pull origin main --quiet
    
    # Re-copy static site files to web root
    rsync -av --delete "$DOCS_DIR/site/" "$WEB_ROOT/"
    chown -R www-data:www-data "$WEB_ROOT"
    echo "[$(date -Iseconds)] Synchronization complete: $REMOTE_HASH"
fi
```

Make the script executable:

```bash
chmod +x /usr/local/bin/sync-docs.sh
```

### Step 2: Create Systemd Service (`/etc/systemd/system/docs-sync.service`)

```ini
[Unit]
Description=Protutech Documentation GitHub Auto-Sync Worker
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/sync-docs.sh
StandardOutput=journal
StandardError=journal
```

### Step 3: Create Systemd Timer (`/etc/systemd/system/docs-sync.timer`)

```ini
[Unit]
Description=Run Protutech Documentation Sync every 5 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and activate the timer:

```bash
systemctl daemon-reload
systemctl enable --now docs-sync.timer
systemctl list-timers --all | grep docs-sync
```

---

## 6. ZFS Snapshot & Disaster Recovery

Because container 100 resides on the `local-zfs` pool, snapshotting and rolling back state takes less than 100 milliseconds and consumes zero additional storage until data blocks mutate.

```bash
# Create an atomic snapshot before major structural edits (Run on Proxmox host)
zfs snapshot local-zfs/subvol-100-disk-0@pre-upgrade-$(date +%F)

# List all container snapshots
zfs list -t snapshot | grep subvol-100-disk-0

# Instant rollback in case of corrupted assets
pct stop 100
zfs rollback local-zfs/subvol-100-disk-0@pre-upgrade-2026-10-09
pct start 100
```
