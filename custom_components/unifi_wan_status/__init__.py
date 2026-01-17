"""The UniFi WAN Status integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady


from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import CONF_CONTROLLER, CONF_SITE, CONF_VERIFY_SSL, DOMAIN
from .coordinator import UniFiWANCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UniFi WAN Status from a config entry."""
    coordinator = UniFiWANCoordinator(
        hass,
        controller=entry.data[CONF_CONTROLLER],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        site=entry.data[CONF_SITE],
        verify_ssl=entry.data[CONF_VERIFY_SSL],
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady("Unable to connect to UniFi Controller")

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Clean up orphaned entities
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    
    # Currently active WAN IDs from coordinator
    active_wan_ids = coordinator.data.keys()
    
    # Identify orphans
    # Our unique_id format is f"{DOMAIN}_{wan_id}" -> "unifi_wan_status_{mac}_{interface}"
    
    # Iterate over a copy of registered entities
    entries = er.async_entries_for_config_entry(
        entity_registry, entry.entry_id
    )
    
    for entity_entry in entries:
        # Check if this entity's unique identifier matches an active WAN
        # The unique_id is stored in entity_entry.unique_id
        # We need to strip the prefix strictly to match wan_id
        
        # Example unique_id: unifi_wan_status_28:70:4e:73:d3:66_wan1
        # The DOMAIN is "unifi_wan_status", so we check if it starts with it
        
        # Simpler approach: check if the unique_id corresponds to any active wan_id
        # We construct expected unique_ids for active wans
        is_active = False
        for wan_id in active_wan_ids:
            expected_unique_id = f"{DOMAIN}_{wan_id}"
            if entity_entry.unique_id == expected_unique_id:
                is_active = True
                break
        
        if not is_active:
            _LOGGER.info("Removing orphaned entity: %s", entity_entry.entity_id)
            entity_registry.async_remove(entity_entry.entity_id)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()

    return unload_ok
