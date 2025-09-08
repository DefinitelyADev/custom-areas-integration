# Configuration Examples

This document provides practical examples of how to configure rooms for different scenarios.

## Basic Room Configuration

### Living Room with Motion Detection
```
Room Name: Living Room
Motion Sensor: binary_sensor.living_room_motion
Temperature Sensor: sensor.living_room_temperature
Active Power Threshold: 10
```

**Use Case**: Basic room monitoring with motion detection and temperature tracking.

### Home Office with Power Monitoring
```
Room Name: Home Office
Power Sensor: sensor.home_office_power
Motion Sensor: binary_sensor.home_office_motion
Temperature Sensor: sensor.home_office_temperature
Active Power Threshold: 50
```

**Use Case**: Office space where activity is determined by both motion and computer power usage.

## Advanced Configurations

### Kitchen with Multiple Sensors
```
Room Name: Kitchen
Power Sensor: sensor.kitchen_power
Motion Sensor: binary_sensor.kitchen_motion
Temperature Sensor: sensor.kitchen_temperature
Humidity Sensor: sensor.kitchen_humidity
Window Sensor: binary_sensor.kitchen_window
Active Power Threshold: 25
```

**Use Case**: Comprehensive kitchen monitoring including cooking activity, temperature, humidity, and ventilation.

### Bedroom with Climate Control
```
Room Name: Master Bedroom
Motion Sensor: binary_sensor.master_bedroom_motion
Temperature Sensor: sensor.master_bedroom_temperature
Humidity Sensor: sensor.master_bedroom_humidity
Climate Entity: climate.master_bedroom_thermostat
Window Sensor: binary_sensor.master_bedroom_window
Active Power Threshold: 5
```

**Use Case**: Bedroom monitoring with climate control integration and low power threshold for night lights.

### Bathroom with Ventilation
```
Room Name: Main Bathroom
Motion Sensor: binary_sensor.bathroom_motion
Humidity Sensor: sensor.bathroom_humidity
Window Sensor: binary_sensor.bathroom_window
Active Power Threshold: 15
```

**Use Case**: Bathroom monitoring focused on occupancy and humidity for ventilation control.

## Energy Monitoring Examples

### Home Theater Setup
```
Room Name: Home Theater
Power Sensor: sensor.av_receiver_power
Motion Sensor: binary_sensor.home_theater_motion
Temperature Sensor: sensor.home_theater_temperature
Active Power Threshold: 20
```

**Use Case**: Entertainment area where power consumption indicates usage.

### Laundry Room
```
Room Name: Laundry Room
Power Sensor: sensor.washer_power
Motion Sensor: binary_sensor.laundry_motion
Temperature Sensor: sensor.laundry_temperature
Active Power Threshold: 10
```

**Use Case**: Utility room with appliance power monitoring.

## Automation Integration Examples

### Lighting Automation Trigger
Use the room state in automations:

```yaml
automation:
  - alias: "Living Room Lights On"
    trigger:
      platform: state
      entity_id: sensor.living_room_summary
      to: 'active'
    action:
      service: light.turn_on
      entity_id: light.living_room
```

### Climate Control
```yaml
automation:
  - alias: "Bedroom Climate Control"
    trigger:
      platform: state
      entity_id: sensor.master_bedroom_summary
      to: 'active'
    action:
      service: climate.set_temperature
      data:
        entity_id: climate.master_bedroom_thermostat
        temperature: 21
```

### Security Notifications
```yaml
automation:
  - alias: "Kitchen Window Alert"
    trigger:
      platform: state
      entity_id: sensor.kitchen_summary
      attribute: window_open
      to: true
    condition:
      condition: state
      entity_id: sensor.kitchen_summary
      state: 'idle'
    action:
      service: notify.mobile_app
      data:
        message: "Kitchen window opened while room is unoccupied"
```

## Dashboard Examples

### Room Status Card
```yaml
type: entities
entities:
  - entity: sensor.living_room_summary
  - type: attribute
    entity: sensor.living_room_summary
    attribute: temperature_c
    name: Temperature
  - type: attribute
    entity: sensor.living_room_summary
    attribute: power_w
    name: Power Usage
  - type: attribute
    entity: sensor.living_room_summary
    attribute: occupied
    name: Motion Detected
```

### Multi-Room Overview
```yaml
type: glance
title: Room Status
entities:
  - sensor.living_room_summary
  - sensor.kitchen_summary
  - sensor.home_office_summary
  - sensor.master_bedroom_summary
```

## Troubleshooting Examples

### Debug State Attributes
Check all attributes of a room sensor:
```yaml
service: system_log.write
data:
  message: "Room attributes: {{ state_attr('sensor.living_room_summary', 'all') }}"
```

### Monitor State Changes
```yaml
automation:
  - alias: "Room State Monitor"
    trigger:
      platform: state
      entity_id: sensor.living_room_summary
    action:
      service: system_log.write
      data:
        message: "Living room changed to {{ trigger.to_state.state }}"
```

## Best Practices

### Sensor Selection
- Choose sensors that accurately represent room activity
- Use appropriate power thresholds for different room types
- Consider both motion and power for comprehensive detection

### Naming Conventions
- Use descriptive room names
- Keep names consistent with your Home Assistant entity naming
- Include location context when needed

### Threshold Tuning
- Start with conservative thresholds
- Monitor actual usage patterns
- Adjust based on false positives/negatives

### Entity Organization
- Group related sensors by room
- Use consistent naming patterns
- Document sensor purposes in entity names
