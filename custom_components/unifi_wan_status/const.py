"""Constants for the UniFi WAN Status integration."""

DOMAIN = "unifi_wan_status"

# Configuration
CONF_CONTROLLER = "controller"
CONF_SITE = "site"
CONF_VERIFY_SSL = "verify_ssl"

# Defaults
DEFAULT_SITE = "default"
DEFAULT_VERIFY_SSL = False
DEFAULT_SCAN_INTERVAL = 60  # seconds

# Attributes
ATTR_DEVICE_NAME = "device_name"
ATTR_DEVICE_MODEL = "device_model"
ATTR_IP_ADDRESS = "ip_address"
ATTR_GATEWAY = "gateway"
ATTR_DNS = "dns"
ATTR_SPEED = "speed"
ATTR_FULL_DUPLEX = "full_duplex"
ATTR_MAX_SPEED = "max_speed"
ATTR_ISP_NAME = "isp_name"
ATTR_ISP_ORGANIZATION = "isp_organization"
ATTR_WAN_TYPE = "wan_type"
ATTR_NETMASK = "netmask"
ATTR_RX_BYTES = "rx_bytes"
ATTR_TX_BYTES = "tx_bytes"
ATTR_RX_PACKETS = "rx_packets"
ATTR_TX_PACKETS = "tx_packets"
ATTR_UPTIME = "uptime"
ATTR_LATENCY = "latency"
