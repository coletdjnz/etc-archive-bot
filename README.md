# ETC Archive Bot

Discord bot for the [ETC Archive Discord Server](https://discord.gg/5u543AztQp)

This allows for easy searching and displaying of archived metadata of the Youtube channel(s). The metadata was originally collected from sources such as archive.org and the Wayback Machine.

### Commands
```
!about
!choose <num>                     Choose a video from a search. 
!help                             Shows this message
!search <query> [field]           Search the database by phrase. Make sure it is in quotes.
!searchda <query> [field]         Search database, sorted by date ascending
!searchdd <query> [field]         Search database, sorted by date descending
!searchr <date> [query] [field]   Search by date. Range is +- 4 days from given.
!stats [series]                   Display stats about the database.
!thumb [video_id]                 Get a thumbnail for a particular video id
```

### Installation

Docker: See [docker-compose.yml](./docker-compose.yml)

Python: 

1. Install requirements:

    `pip install  -r requirements.txt`

2. Set up configuration file with discord bot token, elasticsearch indexes and IPFS details (for thumbnails)
    - see [config.yml](./config/config.yml) for more details
3. Run the bot:
 
    `python3 bot.py --config /path/to/config.yml`

This also requires running an IPFS client.

Note: this requires an elasticsearch database containing relevant indexes. Details of which have not been published yet.

### Remarks

This is an old project from ~2020. It will only receive occasional maintenance updates.