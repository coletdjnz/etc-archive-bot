import discord
from discord.ext import commands
from embeds import VideoEmbed, VideoListingEmbed
from etcdatabase import ETCDatabase
import argparse
import logging
import yaml
import datetime
from dateutil.parser import parse
from thumbnail import IPFSThumbnailHandler
from const import (
    PREFIX,
    MAX_LIST,
    TITLE_PHRASES,
    MERGE_PHRASE
)

bot = commands.Bot(command_prefix=PREFIX)
db: ETCDatabase
log = logging.getLogger('root')


# format: 'userid: {videos to choose}
user_choose = {}


@bot.command()
async def choose(ctx, num):
    """
    Choose a video from a search
    """
    embed = None
    async with ctx.typing():
        if ctx.message.author in user_choose:
            try:
                index = int(num) - 1
                if index in [a for a in range(0, len(user_choose[ctx.message.author]))]:
                    embed = VideoEmbed(user_choose[ctx.message.author][index])
                    thumb = await get_thumb(user_choose[ctx.message.author][index].id)
                    embed.set_image(url=thumb)
                    user_choose.pop(ctx.message.author)

            except ValueError:
                user_choose.pop(ctx.message.author)
    if isinstance(embed, VideoEmbed):
        await ctx.send(embed=embed)


async def search_intermediate(query=None, field=None, match_phrase=True, sort_by_field=None, sort=0, extra_querys=None):

    if extra_querys is None:
        extra_querys = []
    if sort == 1:
        sort_order = "desc"
    else:
        sort_order = "asc"

    if sort_by_field is not None:
        sort_item = {'sort':[{sort_by_field:{'order': sort_order}}, '_score']}
    else:
        sort_item = {}
    size_item = {"size": MAX_LIST}

    queries = []
    query_bool_dict = {}
    source_filters = []

    if len(extra_querys) != 0:
        queries.extend(extra_querys)
        log.info("Added extra queries")

    if query is None and field is None:  # Just get everything
        queries.append({"match_all": {}})
        log.info("Getting everything")

    elif query is None and field is not None:  # Get all of a particular field
        queries.append({"match_all": {}})
        source_filters.append(field)
        log.info("Getting everything for a particular field")
    elif match_phrase is not None and field is not None: # Search a field and match a phrase
        queries.append({'match_phrase': {field: query}})
        log.info("Searching a field and matching a phrase")
    elif match_phrase is not None and field is None:  # Match a phrase but search globally
        queries.append({'multi_match': {"type": "phrase", "query": query}})
        log.info("Match a phrase but search globally")
    elif match_phrase is None and field is not None:  #  Do not match phrase, search by field (remember this one includes a query)
        queries.append({'match': {field: query}})
        log.info("Do not match a phrase but search by field")
    elif match_phrase is None and field is None:
        queries.append({'multi_match': {"type": "best_fields", "query": query}})
        log.info("Search globally but don't match phrase")
    else:
        log.error("Invalid combination for searching.")
        queries.append({"match_none": {}})

    if len(source_filters) > 0:
        source_item = {"_source": source_filters}
    else:
        source_item = {}

    if len(queries) > 0:
        query_bool_dict.setdefault("must", []).extend(queries)

    query_item = {"query": {"bool": query_bool_dict}}

    search_object = {**size_item, **source_item, **query_item, **sort_item}
    log.info(search_object)
    return await db.search(search_object)


@bot.command()
async def searchr(ctx, date: str, query=None, field=None):
    """
    Search by date. Range is +- 4 days from given.
    """
    async with ctx.typing():
        # Convert the date
        datetime_utc = parse(date, fuzzy=True).replace(tzinfo=datetime.timezone.utc).timestamp()
        log.info(f"Converted date to epoch: {datetime_utc}")
        date_query = await db.get_date_range_query(datetime_utc, range=8)

        search_data = await search_intermediate(query=query, field=field, extra_querys=[date_query])

        if len(search_data) == 0:
            embed = discord.Embed(title="Error", description=f"No entries in database for date range:{date}", colour=0xff0000)
        elif len(search_data) == 1:
            embed = VideoEmbed(search_data[0])
            thumb = await get_thumb(search_data[0].id)
            embed.set_image(url=thumb)
        else:
            embed = VideoListingEmbed(search_data)
            user_choose[ctx.message.author] = search_data

    await ctx.send(embed=embed)


@bot.command()
async def search(ctx, query: str, field=None):
    """
    Search the database by phrase. Make sure it is in quotes.
    """
    async with ctx.typing():
        search_data = await search_intermediate(query=query, field=field)

        if len(search_data) == 0:
            embed = discord.Embed(title="Error", description=f"No entries in database for query:{query}", colour=0xff0000)
        elif len(search_data) == 1:
            embed = VideoEmbed(search_data[0])
            thumb = await get_thumb(search_data[0].id)
            embed.set_image(url=thumb)
        else:
            embed = VideoListingEmbed(search_data)
            user_choose[ctx.message.author] = search_data

    await ctx.send(embed=embed)


@bot.command()
async def searchda(ctx, query: str, field=None):
    """
    Search database, sorted by date ascending
    """
    async with ctx.typing():
        search_data = await search_intermediate(query=query, sort_by_field='date_published', sort=0, field=field)

        if len(search_data) == 0:
            embed = discord.Embed(title="Error", description=f"No entries in database for query:{query}", colour=0xff0000)
        elif len(search_data) == 1:
            embed = VideoEmbed(search_data[0])
            thumb = await get_thumb(search_data[0].id)
            embed.set_image(url=thumb)
        else:
            embed = VideoListingEmbed(search_data)
            user_choose[ctx.message.author] = search_data

    await ctx.send(embed=embed)


@bot.command()
async def searchdd(ctx, query: str, field=None):
    """
    Search database, sorted by date descending
    """
    async with ctx.typing():
        search_data = await search_intermediate(query=query, sort_by_field='date_published', sort=1, field=field)

        if len(search_data) == 0:
            embed = discord.Embed(title="Error", description=f"No entries in database for query:{query}", colour=0xff0000)
        elif len(search_data) == 1:
            embed = VideoEmbed(search_data[0])
            thumb = await get_thumb(search_data[0].id)
            embed.set_image(url=thumb)
        else:
            embed = VideoListingEmbed(search_data)
            user_choose[ctx.message.author] = search_data

    await ctx.send(embed=embed)

@bot.command()
async def thumb(ctx, video_id=None):
    """
    Get a thumbnail for a particular video id
    """
    async with ctx.typing():
        thumb_folder = await thumbdb.get_thumb_folder()
        if video_id is None:
            e = discord.Embed(title="ETC Thumbnails", description="The thumbnails the ETC Bot uses are stored on the IPFS network. "
                                                                 f"You can view the latest database here: {thumb_folder}")
            e.set_footer(text=f"If you were looking for a particular thumbnail, type {PREFIX}thumb <video id>")
        else:
            d = await thumbdb.get_thumb_url(video_id)
            if d is None:
                e = discord.Embed(title="Error", description=f"No thumbnail found for video {video_id}!")
            else:
                e = discord.Embed(title=f"Thumbnail for {video_id}")
                e.set_image(url=d)
            e.set_footer(text=f"To get info on this video: {PREFIX}search {video_id} id ")
        await ctx.send(embed=e)


async def get_thumb(video_id):
    thumb = await thumbdb.get_thumb_url(video_id)
    if thumb is None:
        return ""
    return thumb


@bot.command()
async def stats(ctx, series=None):
    """
    Display stats about the database.
    """
    async with ctx.typing():
        embed = discord.Embed(title="ETC Database Statistics")

        if series is not None:
            phrases = TITLE_PHRASES
            embed.description = "Note: that the numbers for series are estimates based off keywords in the video title." \
                                "**They are far from accurate**, " \
                                "but give an idea of how many videos we *at least* have."
        else:
            phrases = []
        stats_received = await db.get_stats(phrases=phrases)
        for merge_pair in MERGE_PHRASE:
            _data = {}
            for merge in MERGE_PHRASE[merge_pair]:
                try:
                    for key in stats_received['phrase'][merge]:
                        _data.setdefault(key, 0)
                        _data[key] += int(stats_received['phrase'][merge][key])
                    del stats_received['phrase'][merge]
                except KeyError:
                    continue
            if len(_data) != 0:
                stats_received['phrase'][merge_pair] = _data
        total_archived_string = f"{stats_received['total_archived']} ({stats_received['total_modern']} + {stats_received['total_classic']})"

        embed.add_field(name="Total Entries", value=stats_received['total'], inline=False)
        embed.add_field(name="Total Re-uploaded", value=stats_received['total_reuploaded'], inline=False)
        embed.add_field(name="Total Archived (Modern + Classic)", value=total_archived_string, inline=False)
        embed.add_field(name="Total Archived (Modern, MachinimaETC Only)", value=str(stats_received['pure_modern_etc_archived'][0]) + "/" + str(stats_received['pure_modern_etc_archived'][1]) + f" ({round((stats_received['pure_modern_etc_archived'][0]/stats_received['pure_modern_etc_archived'][1]) * 100, 1)}%)", inline=False)
        for phrase_stat in sorted(stats_received['phrase']):
            embed.add_field(name=phrase_stat, inline=True, value=f"Total: {stats_received['phrase'][phrase_stat]['total']}"
                                                    f"\nTotal Re-uploaded: {stats_received['phrase'][phrase_stat]['total_reuploaded']}"
                                                    f"\nTotal Archived: {stats_received['phrase'][phrase_stat]['total_archived']}")
    await ctx.send(embed=embed)


@bot.command()
async def about(ctx):
    embed = discord.Embed(title="About ETC Archive Bot", description=f"Source code available at https://github.com/coletdjnz/etc-archive-bot")
    await ctx.send(embed=embed)


async def print_info():
    client = await db.get_client()
    info = await client.info()
    log.info(info)


@bot.event
async def on_ready():
    log.info('Logged in as')
    log.info(bot.user.name)
    log.info(bot.user.id)
    log.info('------')

    bot.loop.create_task(thumbdb.start_ipns_checker())

if __name__ == '__main__':
    # Load the config
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Configuration file", required=True)

    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    logging.basicConfig(level=config['discord']['log_level'])

    db = ETCDatabase(config['elasticsearch']['main_index'],
                     config['elasticsearch']['yt_index'],
                     config['elasticsearch']['local_index'], hosts=config['elasticsearch']['hosts'])
    thumbdb = IPFSThumbnailHandler(ipns_hash=config['thumbnails']['ipns'], cache_file=config['thumbnails']['cache'],
                                   ipfs_host=config['thumbnails']['host'], ipfs_port=config['thumbnails']['port'])

    bot.run(config['discord']['token'])


