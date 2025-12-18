"""Config flow for UniFi WAN Status integration."""
from __future__ import annotations

import logging
from typing import Any

import requests
import urllib3
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_CONTROLLER,
    CONF_SITE,
    CONF_VERIFY_SSL,
    DEFAULT_SITE,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CONTROLLER, default="https://192.168.1.1:8443"): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SITE, default=DEFAULT_SITE): str,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    session = requests.Session()

    try:
        # Attempt to log in
        login_url = f"{data[CONF_CONTROLLER]}/api/login"
        login_data = {
            "username": data[CONF_USERNAME],
            "password": data[CONF_PASSWORD],
        }

        resp = await hass.async_add_executor_job(
            lambda: session.post(
                login_url,
                json=login_data,
                verify=data[CONF_VERIFY_SSL],
                timeout=10,
            )
        )

        if resp.status_code != 200:
            raise InvalidAuth

        # Try to fetch devices to ensure we have access
        devices_url = f"{data[CONF_CONTROLLER]}/api/s/{data[CONF_SITE]}/stat/device"
        resp = await hass.async_add_executor_job(
            lambda: session.get(
                devices_url,
                verify=data[CONF_VERIFY_SSL],
                timeout=10,
            )
        )

        if resp.status_code != 200:
            raise CannotConnect

    except requests.exceptions.Timeout:
        raise CannotConnect
    except requests.exceptions.RequestException:
        raise CannotConnect
    finally:
        await hass.async_add_executor_job(session.close)

    # Return info that you want to store in the config entry.
    return {"title": f"UniFi Controller ({data[CONF_CONTROLLER]})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UniFi WAN Status."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
