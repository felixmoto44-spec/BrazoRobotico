#!/bin/bash
# Configurar WiFi Access Point en Arduino UNO Q (Qualcomm Debian Linux)
# Ejecutar como root

set -e

WIFI_IFACE="wlan0"
SSID="RobotHand"
CHANNEL=6
PASSWORD="robot2026"
SUBNET="192.168.4.0/24"
IP="192.168.4.1"

echo "[1/5] Instalando dependencias..."
apt-get update -qq
apt-get install -y -qq hostapd dnsmasq

echo "[2/5] Configurando interfaz WiFi..."
ip link set $WIFI_IFACE down
ip addr flush dev $WIFI_IFACE
ip addr add $IP/24 dev $WIFI_IFACE
ip link set $WIFI_IFACE up

echo "[3/5] Creando hostapd.conf..."
cat > /etc/hostapd/hostapd.conf << EOF
interface=$WIFI_IFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=$CHANNEL
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

echo "[4/5] Configurando dnsmasq..."
cat > /etc/dnsmasq.conf << EOF
interface=$WIFI_IFACE
dhcp-range=192.168.4.10,192.168.4.100,12h
dhcp-option=3,$IP
dhcp-option=6,$IP
no-resolv
log-queries
log-dhcp
EOF

echo "[5/5] Arrancando servicios..."
pkill hostapd 2>/dev/null || true
pkill dnsmasq 2>/dev/null || true
sleep 1
hostapd -B /etc/hostapd/hostapd.conf
dnsmasq -C /etc/dnsmasq.conf

echo ""
echo "=============================="
echo "WiFi AP '$SSID' activo"
echo "IP: $IP"
echo "Password: $PASSWORD"
echo "=============================="
