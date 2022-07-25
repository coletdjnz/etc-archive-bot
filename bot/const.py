import os

__CHANNEL_AVATARS = {'https://web.archive.org/web/20200306204335im_/https://yt3.ggpht.com/a/AATXAJyLkfDzhn_3eXDOW-_sIOdMVf8HhU_16MGpVw=s100-c-k-c0xffffffff-no-rj-mo': ['MachinimaETC', 'UCdIaNUarhzLSXGoItz7BHVA', 'machinimaetc'],
                     'https://web.archive.org/web/20181201101415im_/https://yt3.ggpht.com/a-/AN66SAy5I5_a-Pa4CuY687qid-2KoLQd5x359wFqEg=s100-mo-c-c0xffffffff-rj-k-no': ['machinima', 'UCcMTZY1rFXO3Rj44D5VMyiw', 'Machinima'],
                     'https://web.archive.org/web/20200307151923im_/https://yt3.ggpht.com/a/AATXAJzirvLpa6p9LIM99v4qY9stAWOI0CfhWVRoNw=s100-c-k-c0xffffffff-no-rj-mo': ['UCXD7b5Qj5z7oV6kggtXD-eQ']}

CHANNEL_AVATARS = {}

for avatar_url in __CHANNEL_AVATARS:
    for uploader_id in __CHANNEL_AVATARS[avatar_url]:
        CHANNEL_AVATARS[uploader_id] = avatar_url


EMBED_MAX_LENGTH = 6000
EMBED_TITLE_MAX_LENGTH = 256
EMBED_DESCRIPTION_MAX_LENGTH = 2048
EMBED_FIELD_NAME_MAX_LENGTH = 256
EMBED_FIELD_VALUE_MAX_LENGTH = 1024
EMBED_MAX_FIELDS = 25
STR_SHORTED_SUFFIX = " [...]"


INVALID_STRINGS = (None, "", " ", "NA")

MARKDOWN_CHARACTERS = ["_", "*"]

PREFIX = os.getenv("BOT_PREFIX", "!")
MAX_LIST = 20
TITLE_PHRASES = ['Weekly Weird News', 'News Dump', 'Tech Newsday', 'Tech Tuesday', 'Tech Tuesday', 'TechNewsday', 'ETC Podcast', 'T.U.G.S', 'TUGS', 'Creepy Text Theatre', 'Ask Us Anything!', 'ETC Live', 'Spacebar']
MERGE_PHRASE = {'Tech Tuesday/Newsday': ('Tech Newsday', 'Tech Tuesday', 'TechNewsday', 'Tech Tuesday'), 'T.U.G.S.': ('T.U.G.S', 'TUGS')}