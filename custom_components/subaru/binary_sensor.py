"""Support for Subaru binary sensors."""
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_BATTERY_CHARGING,
    DEVICE_CLASS_DOOR,
    DEVICE_CLASS_PLUG,
    DEVICE_CLASS_POWER,
    BinarySensorEntity,
)
import subarulink.const as sc

from .const import (
    API_GEN_2,
    DOMAIN,
    ENTRY_COORDINATOR,
    ENTRY_VEHICLES,
    VEHICLE_API_GEN,
    VEHICLE_HAS_EV,
)
from .entity import SubaruEntity

SENSOR_NAME = "name"
SENSOR_FIELD = "field"
SENSOR_CLASS = "class"
SENSOR_ON_VALUE = "on_value"

BINARY_SENSOR_ICONS = {DEVICE_CLASS_POWER: {True: "mdi:engine", False: "mdi:engine-off"},
                       DEVICE_CLASS_BATTERY_CHARGING: {True: "mdi:car-electric", False: "mdi:car"},
                       DEVICE_CLASS_DOOR: {True: "mdi:door-open", False: "mdi:door-closed"},
                       DEVICE_CLASS_PLUG: {True: "mdi:power-plug", False: "mid:power-plug-off"}}

# Binary Sensor data available to "Subaru Safety Plus" subscribers with Gen2 vehicles
API_GEN_2_SENSORS = [
    {
        SENSOR_NAME: "Ignition",
        SENSOR_FIELD: sc.VEHICLE_STATE,
        SENSOR_CLASS: DEVICE_CLASS_POWER,
        SENSOR_ON_VALUE: sc.IGNITION_ON,
    },
    {
        SENSOR_NAME: "Trunk",
        SENSOR_FIELD: sc.DOOR_BOOT_POSITION,
        SENSOR_CLASS: DEVICE_CLASS_DOOR,
        SENSOR_ON_VALUE: sc.DOOR_OPEN,
    },
    {
        SENSOR_NAME: "Hood",
        SENSOR_FIELD: sc.DOOR_ENGINE_HOOD_POSITION,
        SENSOR_CLASS: DEVICE_CLASS_DOOR,
        SENSOR_ON_VALUE: sc.DOOR_OPEN,
    },
    {
        SENSOR_NAME: "Front Left Door",
        SENSOR_FIELD: sc.DOOR_FRONT_LEFT_POSITION,
        SENSOR_CLASS: DEVICE_CLASS_DOOR,
        SENSOR_ON_VALUE: sc.DOOR_OPEN,
    },
    {
        SENSOR_NAME: "Front Right Door",
        SENSOR_FIELD: sc.DOOR_FRONT_RIGHT_POSITION,
        SENSOR_CLASS: DEVICE_CLASS_DOOR,
        SENSOR_ON_VALUE: sc.DOOR_OPEN,
    },
    {
        SENSOR_NAME: "Rear Left Door",
        SENSOR_FIELD: sc.DOOR_REAR_LEFT_POSITION,
        SENSOR_CLASS: DEVICE_CLASS_DOOR,
        SENSOR_ON_VALUE: sc.DOOR_OPEN,
    },
    {
        SENSOR_NAME: "Rear Right Door",
        SENSOR_FIELD: sc.DOOR_REAR_RIGHT_POSITION,
        SENSOR_CLASS: DEVICE_CLASS_DOOR,
        SENSOR_ON_VALUE: sc.DOOR_OPEN,
    },
]

# Binary Sensor data available to "Subaru Safety Plus" subscribers with PHEV vehicles
EV_SENSORS = [
    {
        SENSOR_NAME: "EV Charge Port",
        SENSOR_FIELD: sc.EV_IS_PLUGGED_IN,
        SENSOR_CLASS: DEVICE_CLASS_PLUG,
        SENSOR_ON_VALUE: [sc.LOCKED_CONNECTED, sc.UNLOCKED_CONNECTED],
    },
    {
        SENSOR_NAME: "EV Battery Charging",
        SENSOR_FIELD: sc.EV_CHARGER_STATE_TYPE,
        SENSOR_CLASS: DEVICE_CLASS_BATTERY_CHARGING,
        SENSOR_ON_VALUE: sc.CHARGING,
    },
]


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Subaru binary sensors by config_entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id][ENTRY_COORDINATOR]
    vehicle_info = hass.data[DOMAIN][config_entry.entry_id][ENTRY_VEHICLES]
    entities = []
    for vin in vehicle_info.keys():
        _create_sensor_entities(entities, vehicle_info[vin], coordinator, hass)
    async_add_entities(entities, True)


def _create_sensor_entities(entities, vehicle_info, coordinator, hass):
    sensors_to_add = []

    if vehicle_info[VEHICLE_API_GEN] == API_GEN_2:
        sensors_to_add.extend(API_GEN_2_SENSORS)

    if vehicle_info[VEHICLE_HAS_EV]:
        sensors_to_add.extend(EV_SENSORS)

    for subaru_sensor in sensors_to_add:
        entities.append(
            SubaruBinarySensor(
                vehicle_info,
                coordinator,
                subaru_sensor[SENSOR_NAME],
                subaru_sensor[SENSOR_FIELD],
                subaru_sensor[SENSOR_CLASS],
                subaru_sensor[SENSOR_ON_VALUE],
            )
        )


class SubaruBinarySensor(SubaruEntity, BinarySensorEntity):
    """Class for Subaru binary sensors."""

    def __init__(
        self, vehicle_info, coordinator, title, data_field, sensor_class, on_value
    ):
        """Initialize the binary sensor."""
        super().__init__(vehicle_info, coordinator)
        self.hass_type = "binary_sensor"
        self.title = title
        self.data_field = data_field
        self.sensor_class = sensor_class
        self.on_value = on_value

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self.sensor_class

    @property
    def icon(self):
        """Return icon for sensor."""
        return BINARY_SENSOR_ICONS[self.sensor_class][self.is_on]

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        if type(self.on_value) == list:
            return self.get_current_value() in self.on_value
        return self.get_current_value() == self.on_value

    def get_current_value(self):
        """Get raw value from the coordinator."""
        if self.coordinator.data.get(self.vin):
            return self.coordinator.data[self.vin]["status"].get(self.data_field)
