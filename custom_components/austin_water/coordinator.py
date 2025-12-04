from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .watersmart import WaterSmartClient

_LOGGER = logging.getLogger(__name__)


class AustinWaterCoordinator(DataUpdateCoordinator):
    """Coordinate Austin Water data updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: ClientSession,
        entry: ConfigEntry,
        update_interval: timedelta,
    ) -> None:
        self.entry = entry
        self.client = WaterSmartClient(
            session,
            {
                "username": entry.data.get(CONF_USERNAME),
                "password": entry.data.get(CONF_PASSWORD),
                **entry.data,
                **entry.options,
            },
        )

        super().__init__(
            hass,
            _LOGGER,
            name="Austin Water Usage",
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> list[Any]:
        try:
            return await self.client.fetch_usage()
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Unable to refresh data: {err}") from err
