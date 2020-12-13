import logging

from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT
)
from . import (
    DOMAIN,
    SIGNAL_UPONOR_STATE_UPDATE
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    state_proxy = hass.data[DOMAIN]["state_proxy"]

    entities = []
    for controller in hass.data[DOMAIN]["controllers_with_outdoortemp"]:
        entities.append(UponorSensor(state_proxy, controller, 'uponor_outdoortemp_C' + controller))
    if entities:
        async_add_entities(entities, update_before_add=False)

class UponorSensor(Entity):

    def __init__(self, state_proxy, controller, name):
        self._state_proxy = state_proxy
        self._controller = controller
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return 'C' + self._name + '_outdoortemp_' + self._state_proxy.get_controller_serial(self._controller)

    @property
    def device_class(self):
        return DEVICE_CLASS_TEMPERATURE
    
    @property
    def unit_of_measurement(self):
        return TEMP_CELSIUS
    
    @property
    def state(self):
        return self._state_proxy.get_outdoor_temperature(self._controller)
    
    async def async_added_to_hass(self):
        async_dispatcher_connect(
            self.hass, SIGNAL_UPONOR_STATE_UPDATE, self._update_callback
        )

    @callback
    def _update_callback(self):
        self.async_schedule_update_ha_state(True)
    
    @property
    def device_state_attributes(self):
        return {
            'id': 'C' + self._controller,
            'serial': self._state_proxy.get_controller_serial(self._controller)

        }

