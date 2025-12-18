"""Sensor platform for UniFi WAN Status."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DEVICE_MODEL,
    ATTR_DEVICE_NAME,
    ATTR_DNS,
    ATTR_FULL_DUPLEX,
    ATTR_GATEWAY,
    ATTR_IP_ADDRESS,
    ATTR_ISP_NAME,
    ATTR_ISP_ORGANIZATION,
    ATTR_LATENCY,
    ATTR_MAX_SPEED,
    ATTR_NETMASK,
    ATTR_RX_BYTES,
    ATTR_RX_PACKETS,
    ATTR_SPEED,
    ATTR_TX_BYTES,
    ATTR_TX_PACKETS,
    ATTR_UPTIME,
    ATTR_WAN_TYPE,
    DOMAIN,
)
from .coordinator import UniFiWANCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniFi WAN Status sensors based on a config entry."""
    coordinator: UniFiWANCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create a sensor for each WAN interface found
    entities = []
    for wan_id in coordinator.data:
        entities.append(UniFiWANSensor(coordinator, wan_id))

    async_add_entities(entities)


class UniFiWANSensor(CoordinatorEntity[UniFiWANCoordinator], SensorEntity):
    """Representation of a UniFi WAN Status sensor."""

    def __init__(self, coordinator: UniFiWANCoordinator, wan_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._wan_id = wan_id
        self._attr_has_entity_name = True

        # Get initial data
        wan_data = coordinator.data.get(wan_id, {})
        
        # Set unique ID
        self._attr_unique_id = f"{DOMAIN}_{wan_id}"
        
        # Set device info for grouping
        self._attr_device_info = {
            "identifiers": {(DOMAIN, wan_data.get("mac", wan_id))},
            "name": wan_data.get("device_name", "UniFi Device"),
            "manufacturer": "Ubiquiti",
            "model": wan_data.get("device_model", "Unknown"),
        }

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        wan_data = self.coordinator.data.get(self._wan_id, {})
        return wan_data.get("wan_interface", "WAN").upper()

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        wan_data = self.coordinator.data.get(self._wan_id, {})
        return "Online" if wan_data.get("is_up", False) else "Offline"

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        wan_data = self.coordinator.data.get(self._wan_id, {})
        if wan_data.get("is_up", False):
            return "mdi:wan"
        return "mdi:earth-off"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        wan_data = self.coordinator.data.get(self._wan_id, {})
        
        attrs = {
            ATTR_DEVICE_NAME: wan_data.get("device_name", "Unknown"),
            ATTR_DEVICE_MODEL: wan_data.get("device_model", "Unknown"),
            ATTR_IP_ADDRESS: wan_data.get("ip", "N/A"),
            ATTR_GATEWAY: wan_data.get("gateway", "N/A"),
            ATTR_DNS: wan_data.get("dns", "N/A"),
        }
        
        # ISP Information
        isp_name = wan_data.get("isp_name", "N/A")
        isp_org = wan_data.get("isp_organization", "N/A")
        
        if isp_name != "N/A":
            attrs[ATTR_ISP_NAME] = isp_name
        
        if isp_org != "N/A":
            attrs[ATTR_ISP_ORGANIZATION] = isp_org
        
        # Connection type and network info
        if wan_data.get("wan_type") != "N/A":
            attrs[ATTR_WAN_TYPE] = wan_data["wan_type"]
        
        if wan_data.get("netmask") != "N/A":
            attrs[ATTR_NETMASK] = wan_data["netmask"]
        
        # Speed info
        if wan_data.get("speed"):
            attrs[ATTR_SPEED] = wan_data["speed"]
        
        if wan_data.get("max_speed"):
            attrs[ATTR_MAX_SPEED] = wan_data["max_speed"]
        
        if "full_duplex" in wan_data:
            attrs[ATTR_FULL_DUPLEX] = wan_data["full_duplex"]
        
        # Statistics
        rx_bytes = wan_data.get("rx_bytes", 0)
        tx_bytes = wan_data.get("tx_bytes", 0)
        
        if rx_bytes:
            attrs[ATTR_RX_BYTES] = self._format_bytes(rx_bytes)
            
        if tx_bytes:
            attrs[ATTR_TX_BYTES] = self._format_bytes(tx_bytes)
        
        if wan_data.get("rx_packets"):
            attrs[ATTR_RX_PACKETS] = wan_data["rx_packets"]
        
        if wan_data.get("tx_packets"):
            attrs[ATTR_TX_PACKETS] = wan_data["tx_packets"]
        
        # Uptime
        uptime = wan_data.get("uptime", 0)
        if uptime:
            attrs[ATTR_UPTIME] = f"{uptime} hours"
        
        # Latency
        if wan_data.get("latency"):
            attrs[ATTR_LATENCY] = f"{wan_data['latency']} ms"
        
        return attrs
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._wan_id in self.coordinator.data
