# rf2mqtt
Send RF 433MHz codes to an MQTT broker. Works well with Home Assistant

# Example of usage with Home Assistant
```yaml
mqtt:
    broker: 172.17.0.2
automation:
  - id: '5527299'
    alias: rc_bedroom_volume_down
    description: Control bedroom volume via rc (down)
    trigger:
    - payload: 5527299
  	platform: mqtt
  	topic: rc
    condition: []
    action:
    - entity_id: media_player.bedroom
  	service: media_player.volume_down
``` 

# Installation
```bash
./install.sh
```

# Dependencies
python3, virtualenv, docker


