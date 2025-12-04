from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_EMAIL_FOLDER,
    CONF_EMAIL_HOST,
    CONF_EMAIL_PASSWORD,
    CONF_EMAIL_PORT,
    CONF_EMAIL_USERNAME,
    CONF_SUBJECT_FILTER,
    CONF_WAIT_TIME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)


class AustinWaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Austin Water."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(title="Austin Water", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_EMAIL_HOST): str,
                vol.Optional(CONF_EMAIL_PORT, default=993): int,
                vol.Optional(CONF_EMAIL_USERNAME): str,
                vol.Optional(CONF_EMAIL_PASSWORD): str,
                vol.Optional(CONF_EMAIL_FOLDER, default="INBOX"): str,
                vol.Optional(CONF_SUBJECT_FILTER, default="verification"): str,
                vol.Optional(CONF_WAIT_TIME, default=90): int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_import(self, user_input: dict | None = None) -> FlowResult:
        """Handle YAML import."""
        return await self.async_step_user(user_input)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return AustinWaterOptionsFlowHandler(config_entry)


class AustinWaterOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Austin Water."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="Austin Water Options", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                ): int
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
