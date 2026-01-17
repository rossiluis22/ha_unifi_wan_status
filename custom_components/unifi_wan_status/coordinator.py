"""DataUpdateCoordinator for UniFi WAN Status."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import requests
import urllib3
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class UniFiWANCoordinator(DataUpdateCoordinator):
    """Class to manage fetching UniFi WAN data."""

    def __init__(
        self,
        hass: HomeAssistant,
        controller: str,
        username: str,
        password: str,
        site: str,
        verify_ssl: bool,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.controller = controller
        self.username = username
        self.password = password
        self.site = site
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self._logged_in = False

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from UniFi Controller."""
        try:
            # Ensure we're logged in
            if not self._logged_in:
                await self.hass.async_add_executor_job(self._login)

            # Fetch device data
            data = await self.hass.async_add_executor_job(self._fetch_devices)
            return data

        except requests.exceptions.RequestException as err:
            # If authentication fails, try to log in again
            self._logged_in = False
            raise UpdateFailed(f"Error communicating with UniFi Controller: {err}")

    def _login(self) -> None:
        """Log in to the UniFi Controller."""
        login_url = f"{self.controller}/api/login"
        login_data = {"username": self.username, "password": self.password}
        
        try:
            resp = self.session.post(
                login_url,
                json=login_data,
                verify=self.verify_ssl,
                timeout=10
            )
            
            if resp.status_code != 200:
                raise UpdateFailed(f"Login failed: {resp.status_code} - {resp.text}")
            
            self._logged_in = True
            _LOGGER.debug("Successfully logged in to UniFi Controller")
            
        except requests.exceptions.RequestException as err:
            raise UpdateFailed(f"Login error: {err}")

    def _fetch_devices(self) -> dict[str, Any]:
        """Fetch device data from UniFi Controller."""
        devices_url = f"{self.controller}/api/s/{self.site}/stat/device"
        
        try:
            resp = self.session.get(
                devices_url,
                verify=self.verify_ssl,
                timeout=10
            )
            
            if resp.status_code == 401:
                # Session expired, try to login again
                self._logged_in = False
                self._login()
                resp = self.session.get(
                    devices_url,
                    verify=self.verify_ssl,
                    timeout=10
                )
            
            if resp.status_code != 200:
                raise UpdateFailed(
                    f"Error fetching devices: {resp.status_code} - {resp.text}"
                )
            
            devices = resp.json().get("data", [])
            
            # Fetch health data for ISP info
            health_data = self._fetch_health()
            
            # Extract ISP info from health data
            health_isp_name = "N/A"
            health_isp_org = "N/A"
            
            for subsystem in health_data:
                if subsystem.get("subsystem") == "wan":
                    health_isp_name = subsystem.get("isp_name", "N/A")
                    health_isp_org = subsystem.get("isp_organization", "N/A")
                    break

            # Process devices and extract WAN information
            wan_data = {}
            
            for device in devices:
                # Look for WAN interfaces
                wan_keys = [key for key in device.keys() if key.startswith("wan")]
                
                if wan_keys:
                    device_name = device.get("name", device.get("model", "Unknown"))
                    device_model = device.get("model", "Unknown")
                    device_mac = device.get("mac", "unknown")
                    
                    for wan_key in wan_keys:
                        wan_info = device[wan_key]
                        
                        # Create unique identifier for this WAN
                        wan_id = f"{device_mac}_{wan_key}"
                        
                        # Extract ISP information from device or fallback to health data
                        isp_name = wan_info.get("isp_name") or wan_info.get("ispName") or wan_info.get("provider")
                        isp_org = wan_info.get("isp_organization") or wan_info.get("ispOrganization") or wan_info.get("organization")
                        
                        # If not found in device, use health data (mostly for primary WAN)
                        # We assume the health data corresponds to the active WAN or the first one
                        if not isp_name and wan_info.get("up", False):
                             isp_name = health_isp_name
                             isp_org = health_isp_org
                        
                        if not isp_name:
                             isp_name = "N/A"
                        if not isp_org:
                             isp_org = "N/A"

                        # Calculate uptime in hours if available
                        uptime_seconds = wan_info.get("uptime", 0)
                        uptime_hours = round(uptime_seconds / 3600, 1) if uptime_seconds else 0
                        
                        wan_data[wan_id] = {
                            "name": f"{device_name} {wan_key.upper()}",
                            "wan_interface": wan_key,
                            "device_name": device_name,
                            "device_model": device_model,
                            "is_up": wan_info.get("up", False),
                            "ip": wan_info.get("ip", "N/A"),
                            "gateway": wan_info.get("gateway", "N/A"),
                            "dns": ", ".join(wan_info.get("dns", [])),
                            "speed": wan_info.get("speed", 0),
                            "full_duplex": wan_info.get("full_duplex", False),
                            "max_speed": wan_info.get("max_speed", 0),
                            "mac": device.get("mac", "Unknown"),
                            # ISP Information
                            "isp_name": isp_name,
                            "isp_organization": isp_org,
                            # Connection details
                            "wan_type": wan_info.get("type", "N/A"),
                            "netmask": wan_info.get("netmask", "N/A"),
                            # Statistics
                            "rx_bytes": wan_info.get("rx_bytes", 0),
                            "tx_bytes": wan_info.get("tx_bytes", 0),
                            "rx_packets": wan_info.get("rx_packets", 0),
                            "tx_packets": wan_info.get("tx_packets", 0),
                            "uptime": uptime_hours,
                            "latency": wan_info.get("latency", 0),
                        }
            
            if not wan_data:
                _LOGGER.warning("No WAN interfaces found on any devices")
            
            return wan_data
            
        except requests.exceptions.RequestException as err:
            raise UpdateFailed(f"Error fetching devices: {err}")

    def _fetch_health(self) -> list[dict[str, Any]]:
        """Fetch health data from UniFi Controller."""
        health_url = f"{self.controller}/api/s/{self.site}/stat/health"
        
        try:
            resp = self.session.get(
                health_url,
                verify=self.verify_ssl,
                timeout=10
            )
            
            if resp.status_code != 200:
                _LOGGER.warning(f"Error fetching health data: {resp.status_code}")
                return []
            
            return resp.json().get("data", [])
            
        except requests.exceptions.RequestException as err:
            _LOGGER.warning(f"Error fetching health data: {err}")
            return []

    async def async_shutdown(self) -> None:
        """Close the session when shutting down."""
        if self.session:
            await self.hass.async_add_executor_job(self.session.close)
