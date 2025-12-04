from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_LAST_UPDATE, ATTR_USAGE, DEFAULT_NAME, DOMAIN
from .coordinator import AustinWaterCoordinator
from .watersmart import UsageRow


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AustinWaterCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AustinWaterUsageSensor(coordinator)], True)


class AustinWaterUsageSensor(CoordinatorEntity[AustinWaterCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_name = f"{DEFAULT_NAME} Last Hour"

    def __init__(self, coordinator: AustinWaterCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_usage"
        self._attr_native_unit_of_measurement = "gal"

    @property
    def native_value(self) -> StateType:
        usage = self._latest_usage
        if usage:
            return usage.gallons
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        usage = self._latest_usage
        history = [asdict(item) for item in self.coordinator.data] if self.coordinator.data else []
        attributes: dict[str, Any] = {ATTR_USAGE: history}
        if usage:
            attributes[ATTR_LAST_UPDATE] = usage.read_date.isoformat()
        return attributes

    @property
    def _latest_usage(self) -> UsageRow | None:
        if not self.coordinator.data:
            return None
        return sorted(self.coordinator.data, key=lambda row: row.read_date, reverse=True)[0]
