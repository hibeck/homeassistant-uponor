import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    CURRENT_HVAC_OFF,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS

from . import (
    DOMAIN,
    SIGNAL_UPONOR_STATE_UPDATE
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    state_proxy = hass.data[DOMAIN]["state_proxy"]

    entities = []
    for thermostat in hass.data[DOMAIN]["thermostats"]:
        if thermostat.lower() in hass.data[DOMAIN]["names"]:
            name = hass.data[DOMAIN]["names"][thermostat.lower()]
        else:
            name = state_proxy.get_room_name(thermostat)
        entities.append(UponorClimate(state_proxy, thermostat, name))
    if entities:
        async_add_entities(entities, update_before_add=False)

class UponorClimate(ClimateEntity):

    def __init__(self, state_proxy, thermostat, name):
        self._state_proxy = state_proxy
        self._thermostat = thermostat
        self._name = name
        self._is_on = self._state_proxy.get_setpoint(self._thermostat) > self.min_temp

    @property
    def name(self):
        return self._name
    
    @property
    def unique_id(self):
        return self._name + '_thermostat_' + self._state_proxy.get_thermostat_serial(self._thermostat)

    @property
    def should_poll(self):
        return False

    async def async_added_to_hass(self):
        async_dispatcher_connect(
            self.hass, SIGNAL_UPONOR_STATE_UPDATE, self._update_callback
        )

    @callback
    def _update_callback(self):
        self._is_on = self._state_proxy.get_setpoint(self._thermostat) > self.min_temp
        self.async_schedule_update_ha_state(True)

    @property
    def supported_features(self):
        if self._is_on:
            return SUPPORT_TARGET_TEMPERATURE
        return 0

    @property
    def hvac_action(self):
        if not self._is_on:
            return CURRENT_HVAC_OFF
        if self._state_proxy.is_heating_active(self._thermostat):
            return CURRENT_HVAC_HEAT
        return CURRENT_HVAC_IDLE

    @property
    def hvac_mode(self):
        if self._is_on:
            return HVAC_MODE_HEAT
        return HVAC_MODE_OFF

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVAC_MODE_OFF and self._is_on:
            await self._state_proxy.async_turn_off(self._thermostat)
            self._is_on = False
        if hvac_mode == HVAC_MODE_HEAT and not self._is_on:
            await self._state_proxy.async_turn_on(self._thermostat)
            self._is_on = True

    @property
    def hvac_modes(self):
        return [HVAC_MODE_HEAT, HVAC_MODE_OFF]

    @property
    def temperature_unit(self):
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        return self._state_proxy.get_temperature(self._thermostat)

    @property
    def current_humidity(self):
        return self._state_proxy.get_humidity(self._thermostat)

    @property
    def min_temp(self):
        return self._state_proxy.get_min_limit(self._thermostat)

    @property
    def max_temp(self):
        return self._state_proxy.get_max_limit(self._thermostat)

    @property
    def target_temperature(self):
        return self._state_proxy.get_setpoint(self._thermostat)

    @property
    def device_state_attributes(self):
        at = {
                'id': self._thermostat,
                'serial': self._state_proxy.get_thermostat_serial(self._thermostat),
                'status': self._state_proxy.get_status(self._thermostat),
                'floor_sensor': self._state_proxy.get_regulation_mode(self._thermostat)
            }
        if self._state_proxy.get_regulation_mode(self._thermostat) == 1:
            at['floor_temp'] = self._state_proxy.get_floor_temperature(self._thermostat)
            at['min_floor_temp'] = self._state_proxy.get_min_floor_temperature(self._thermostat)
            at['max_floor_temp'] = self._state_proxy.get_max_floor_temperature(self._thermostat)
        return at;

    def set_temperature(self, **kwargs):
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None and self._is_on:
            self._state_proxy.set_setpoint(self._thermostat, temp)

