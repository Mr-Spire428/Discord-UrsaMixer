# UrsaMixer
Discord bot for DM audio playlists

## Connecting to discord
Create a `.env` file in this directory like so:
```
URSA_APPID=YOUR_APP_ID
URSA_TOKEN=YOUR_DISCORD_TOKEN
```
Alternatively, provide `URSA_APPID` and `URSA_TOKEN` as environment variables.

## Track configuration
Ursa loads it's track configuration from a JSON form.

By default, ursa will attempt to load this from `~/.config/ursa.config`
but the location can be overridden on the command line using the `--config` switch.

The basic form of this JSON document is like so:
```JSON
{
  "Context": {
    "Phase": [
      ["/path/to/track.ogg", 0]
    ],
    "Phase 2": [
      ["/path/to/part1.ogg", 1],
      ["/path/to/part2_looped.ogg", 1]
    ]
  },
  "Another Context": {
    "random tracks": [
      ["/some/track.mp3", -1],
      ["/some/other/track.ogg", -1],
      ["/yet/another/track.ogg", -1]
    ],
    "finale": [
      ["/path/to/finale.mp3", 0]
    ]
  }
}
```
So Ursa will expect two nested dictionaries that contains a list, which contains a list with a string and a number.

The first two names are used to generate "directories" in the tracks UI, the nested list has:
- A path to a local audio file
- a number denoting which track is played next

The track number will determine which track Ursa plays next, starting at 0.

e.g. the first track with the number 0 will loop into itself indefinitely.

As a special case, if the number is -1, Ursa will select a track from the list at random.

## Running UrsaMixer
to run _UrsaMixer_, run

```commandline
python -m ursa
```

or

```commandline
python -m ursa --config path/to/config.json
```

from this directory.