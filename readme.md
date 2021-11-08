# waybar-calendar
A custom widget for waybar

See [example config](example_config.json):

```
{
    "custom/waybar-calendar": {
        "format": "{}",
        "return-type": "json",
        "max-length": 120,
        "interval": 30,
        "exec": "python $HOME/Projects/waybar-calendar/check_db.py"
    }
}
```

Todo:
- Calendar reading from Google url
- Multi-calendar support
- Prettier widget config / css
- Timezone configuration