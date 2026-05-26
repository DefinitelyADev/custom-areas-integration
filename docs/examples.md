# Configuration Examples

This document provides practical examples of how to configure areas for different scenarios.

## Basic Area Configuration

### Living Room with Motion Detection
```
Area Name: Living Room
Motion Sensor: binary_sensor.living_room_motion
Temperature Sensor: sensor.living_room_temperature
Active Power Threshold: 10
```

**Use Case**: Basic area monitoring with motion detection and temperature tracking.

### Home Office with Power Monitoring
```
Area Name: Home Office
Power Sensor: sensor.home_office_power
Motion Sensor: binary_sensor.home_office_motion
Temperature Sensor: sensor.home_office_temperature
Active Power Threshold: 50
```

**Use Case**: Office space where activity is determined by both motion and computer power usage.

## Advanced Configurations

### Kitchen with Multiple Sensors
```
Area Name: Kitchen
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
Area Name: Master Bedroom
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
Area Name: Main Bathroom
Motion Sensor: binary_sensor.bathroom_motion
Humidity Sensor: sensor.bathroom_humidity
Window Sensor: binary_sensor.bathroom_window
Active Power Threshold: 15
```

**Use Case**: Bathroom monitoring focused on occupancy and humidity for ventilation control.

## Energy Monitoring Examples

### Home Theater Setup
```
Area Name: Home Theater
Power Sensor: sensor.av_receiver_power
Motion Sensor: binary_sensor.home_theater_motion
Temperature Sensor: sensor.home_theater_temperature
Active Power Threshold: 20
```

**Use Case**: Entertainment area where power consumption indicates usage.

### Laundry Room
```
Area Name: Laundry Room
Power Sensor: sensor.washer_power
Motion Sensor: binary_sensor.laundry_motion
Temperature Sensor: sensor.laundry_temperature
Active Power Threshold: 10
```

**Use Case**: Utility area with appliance power monitoring.

## Automation Integration Examples

### Lighting Automation Trigger
Use the area state in automations:

```yaml
automation:
  - alias: "Living Room Lights On"
    trigger:
      platform: state
      entity_id: sensor.custom_area_living_room
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
      entity_id: sensor.custom_area_master_bedroom
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
      entity_id: sensor.custom_area_kitchen
      attribute: window_open
      to: true
    condition:
      condition: state
      entity_id: sensor.custom_area_kitchen
      state: 'idle'
    action:
      service: notify.mobile_app
      data:
        message: "Kitchen window opened while area is unoccupied"
```

## Dashboard Examples

### Area Status Card
```yaml
type: entities
entities:
  - entity: sensor.custom_area_living_room
  - type: attribute
    entity: sensor.custom_area_living_room
  attribute: temperature
    name: Temperature
  - type: attribute
    entity: sensor.custom_area_living_room
  attribute: power
  name: Power
  - type: attribute
    entity: sensor.custom_area_living_room
    attribute: occupied
    name: Motion Detected
```

### Multi-Area Overview
```yaml
type: glance
title: Area Status
entities:
  - sensor.custom_area_living_room
  - sensor.custom_area_kitchen
  - sensor.custom_area_home_office
  - sensor.custom_area_master_bedroom
```

## Troubleshooting Examples

### Debug State Attributes
Check all attributes of an area sensor:
```yaml
service: system_log.write
data:
  message: "Area attributes: {{ state_attr('sensor.custom_area_living_room', 'all') }}"
```

### Monitor State Changes
```yaml
automation:
  - alias: "Area State Monitor"
    trigger:
      platform: state
      entity_id: sensor.custom_area_living_room
    action:
      service: system_log.write
      data:
        message: "Living room changed to {{ trigger.to_state.state }}"
```

## Best Practices

### Sensor Selection
- Choose sensors that accurately represent area activity
- Use appropriate power thresholds for different area types
- Consider both motion and power for comprehensive detection

### Naming Conventions
- Use descriptive area names
- Keep names consistent with your Home Assistant entity naming
- Include location context when needed

### Threshold Tuning
- Start with conservative thresholds
- Monitor actual usage patterns
- Adjust based on false positives/negatives

### Entity Organization
- Group related sensors by area
- Use consistent naming patterns
- Document sensor purposes in entity names
