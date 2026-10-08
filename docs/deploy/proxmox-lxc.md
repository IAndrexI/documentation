# Proxmox LXC Deployment Guide

Step-by-step instructions for deploying this documentation website directly on Proxmox VE as a dedicated, lightweight Debian LXC microservice.

---

## 1. Quick Install via Turnkey Script

Run this single command in your **Proxmox VE Host Shell**:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/IAndrexI/documentation/main/deploy-proxmox.sh)"
```

---

## 2. Manual Proxmox Container Creation

If you prefer to configure the container manually through the Proxmox Web GUI:

1. Click **Create CT** (top-right of Proxmox VE).
2. General Settings:
   * **CT ID:** `100` (or your next available ID)
   * **Hostname:** `protutech-docs`
   * **Unprivileged container:** `Yes`
3. Template:
   * Select `debian-12-standard` (or Ubuntu 24.04).
4. Disks:
   * **Storage:** `local-zfs` (4 GB is plenty).
5. CPU & Memory:
   * **Cores:** `1 Core`
   * **Memory:** `512 MB` (RAM usage in production is $<15\text{MB}$).
6. Network:
   * **Bridge:** `vmbr0`
   * **IPv4:** DHCP or Static LAN IP (e.g. `192.168.0.185/24`).

---

## 3. Inside the Container: Install & Serve

Once inside the new LXC console:

```bash
# Update and install Nginx & Git
apt update && apt install -y nginx git curl

# Clone the documentation repository
cd /var/www
rm -rf html/*
git clone https://github.com/IAndrexI/documentation.git /tmp/docs

# Copy the built website to Nginx root
cp -r /tmp/docs/site/* /var/www/html/

# Ensure proper permissions
chown -R www-data:www-data /var/www/html
systemctl restart nginx
```

Access the site on your local network at:
`http://<LXC_IP>`
