import discord
import datetime
from video import ETCVideo
from const import (
    CHANNEL_AVATARS,
    EMBED_MAX_LENGTH,
    EMBED_TITLE_MAX_LENGTH,
    EMBED_DESCRIPTION_MAX_LENGTH,
    EMBED_FIELD_NAME_MAX_LENGTH,
    EMBED_FIELD_VALUE_MAX_LENGTH,
    EMBED_MAX_FIELDS,
    STR_SHORTED_SUFFIX,
    MARKDOWN_CHARACTERS
)

import logging
log = logging.getLogger('root')


class VideoListingEmbed(discord.Embed):
    def __init__(self, videos: list):

        description = ""

        for index, video in enumerate(videos):
            archived_text_entries = []
            if video.archived is not None:
                if video.archived:
                    archived_text_entries.append("H")
            if video.on_youtube is not None:
                if video.on_youtube:
                    archived_text_entries.append("YT")

            if video.title is not None:
                video_title_santized = self.replace_multi(video.title, MARKDOWN_CHARACTERS, "")
            else:
                video_title_santized = "Unknown Title"

            video_info_string = f"{video_title_santized} ({video.id})\n"
            description += f"""**{index+1}** - {str(sorted(archived_text_entries)).replace("'", "") if len(archived_text_entries) >0 else ""} {video_info_string}"""

        super().__init__(title=f"Select video with !choose 1-{len(videos)}:",
                         colour=self.colour,
                         description=description)

    @staticmethod
    def replace_multi(string: str, old: list, new: str):

        for replace in old:
            if replace in string:
                string = string.replace(replace, new)
        return string


class VideoEmbed(discord.Embed):

    def __init__(self, video: ETCVideo):

        self.colour = 0xff0000
        super().__init__(title=f"Video {video.id}",
                         colour=self.colour, url=video.reupload_url)

        fields = video.as_dict()
        self.__process_fields(fields)
        self.__shorten_fields(fields)
        self.__add_fields(fields)
        self.__add_thumbnail(video)

    def set_image(self, url):
        if url is None:
            return
        super().set_image(url=url)

    @staticmethod
    def __process_fields(fields):
        """

        Process specific fields

        """

        # Convert Epoch time to readable time
        try:
            dt = int(float(fields['date_published']))
            fields['date_published'] = str(datetime.datetime.utcfromtimestamp(dt).replace(
                tzinfo=datetime.timezone.utc).strftime('%Y-%m-%d')) + f" UTC"
        except ValueError as e:
            log.debug(f"Failed to convert date: {e}")
            pass
        except KeyError:
            # not a valid field
            pass

        # Convert quality fields to WidthxHeight

        try:
            width = str(fields['local_quality_width'])
            height = str(fields['local_quality_height'])

            fields['archived_resolution'] = width + "x" + height
            del fields['local_quality_width']
            del fields['local_quality_height']

        except KeyError:
            # width or height are not in database
            pass

        # Convert boolean to Yes or No
        for field in fields.keys():
            if isinstance(fields[field], bool):
                fields[field] = "Yes" if fields[field] else "No"

    def __add_thumbnail(self, video):

        for uploader_id in video.uploader_ids:
            if uploader_id in CHANNEL_AVATARS:
                url = CHANNEL_AVATARS[uploader_id]
                self.set_thumbnail(url=url)
                return

    def __add_fields(self, fields):
        """

        get the fields

        """

        for field in fields:
            self.add_field(name=field.replace("_", " ").title(),
                            value=', '.join([str(f) for f in fields[field]]) if isinstance(fields[field], list) else fields[field], inline=False)

    @staticmethod
    def __list_as_string(l: list):
        return ", ".join([str(a) for a in l])

    def __shorten_list_str(self, l: list, max_length: int):

        list_copy = list(l)
        length = len(self.__list_as_string(l + [STR_SHORTED_SUFFIX]))

        if length <= max_length:
            return list_copy

        while length > max_length:  # do 1 character less
            list_copy.pop(len(list_copy)-1)
            length = len(self.__list_as_string(list_copy + [STR_SHORTED_SUFFIX]))
        return list_copy + [STR_SHORTED_SUFFIX]

    @staticmethod
    def __shorten_str(s: str, max_length: int):
        if len(s) <= max_length:
            return s

        if s.endswith(STR_SHORTED_SUFFIX):
            s = s[:-len(STR_SHORTED_SUFFIX)]

        return s[:max_length-len(STR_SHORTED_SUFFIX)] + STR_SHORTED_SUFFIX

    def __shorten_fields(self, fields):

        """

        Shortens fields to meet discord's requirements. This should work most of the time.

        Currently doesn't take into account other elements are that not fields e.g url for thumbnail.

        """

        balanced_fields = fields

        # Check if they are already balanced
        def check_length():
            total_fn_length = 0
            total_f_length = 0

            for field in balanced_fields:
                total_fn_length += len(field)

                total_f_length += len(self.__list_as_string(balanced_fields[field]) if isinstance(balanced_fields[field], list) else balanced_fields[field])

            log.debug(f"Total length of field names: {total_fn_length}")
            log.debug(f"Total length of fields: {total_f_length}")

            if (total_length := (total_fn_length + total_f_length)) <= EMBED_MAX_LENGTH:
                log.debug(f"Total Length is {total_length}, which satisfies the max length of {EMBED_MAX_LENGTH}")
                return balanced_fields
            else:
                log.debug(f"Total Length is {total_length}, which DOES NOT satisfies the max length of {EMBED_MAX_LENGTH}")

        # Ensure each field complies with discord embed limits
        for field_name in list(balanced_fields.keys()):

            log.debug(f"Checking field {field_name}")
            # Shorten the list based on how it will be printed with  , .join()
            if isinstance(balanced_fields[field_name], list):
                log.debug(f"Shortening by list")
                balanced_fields[field_name] = self.__shorten_list_str(balanced_fields[field_name], EMBED_FIELD_VALUE_MAX_LENGTH)
            else:
                # shorten everything else by string representation
                balanced_fields[field_name] = self.__shorten_str(str(balanced_fields[field_name]), EMBED_FIELD_VALUE_MAX_LENGTH)

            # Check field name length
            if len(field_name) >= EMBED_FIELD_NAME_MAX_LENGTH:
                log.debug("Field name is too long")
                balanced_fields[self.__shorten_str(field_name, EMBED_FIELD_NAME_MAX_LENGTH)] = balanced_fields[field_name]
                del balanced_fields[field_name]

        return check_length()
