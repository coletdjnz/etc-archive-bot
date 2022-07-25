"""

Class representing a video in the Elastic Search Database

"""

from const import INVALID_STRINGS


class ETCVideo:

    def __init__(self, **kwargs):

        self.id = kwargs.get('id', None)

        if self.id is None:
            raise ValueError('id is a required value.')

        self.title = kwargs.get('title', None)
        if self.title is not None:
            self.title = str(self.title).replace(r'\n', '')
            if self.title == "":
                self.title = None
        self.alternate_titles = self.__skip_invalid_strings(list(kwargs.get('alternate_titles', [])))
        self.description = kwargs.get('description', None)
        if self.description is not None:
            self.description = str(self.description).replace(r'\n', '')
            if self.description == "":
                self.description = None
        self.alternate_descriptions = self.__skip_invalid_strings(list(kwargs.get('alternate_descriptions', [])))
        self.duration = kwargs.get('duration', None)
        if self.duration is not None:
            self.duration = str(self.duration).replace(r'\n', '')
            if self.duration == "":
                self.duration = None
        self.date_published = kwargs.get('date_published', None)
        if self.date_published is not None:
            self.date_published = str(self.date_published).replace(r'\n', '')
            if self.date_published == "":
                self.date_published = None
        self.uploader = kwargs.get('uploader', None)
        if self.uploader is not None:
            self.uploader = str(self.uploader).replace(r'\n', '')
            if self.uploader == "":
                self.uploader = None
        self.alternate_uploaders = self.__skip_invalid_strings(list(kwargs.get('alternate_uploaders', [])))
        self.uploader_ids = self.__skip_invalid_strings(list(kwargs.get('uploader_ids', [])))
        self.tags = self.__skip_invalid_strings(list(kwargs.get('tags', [])))

        self.duplicate_of = self.__skip_invalid_strings(list(kwargs.get('duplicate_of', [])))

        self.__local_quality_width = kwargs.get('local_quality_width', None)

        if self.__local_quality_width is not None:
            if self.__local_quality_width == "":
                self.__local_quality_width = None
        self.__local_quality_height = kwargs.get('local_quality_height', None)
        if self.__local_quality_height is not None:
            if self.__local_quality_height == "":
                self.__local_quality_height = None
        self.archived = kwargs.get('archived', None)
        if self.archived is not None:
            self.archived = bool(self.archived)
        self.on_youtube = kwargs.get('on_youtube', None)
        if self.on_youtube is not None:
            self.on_youtube = bool(self.on_youtube)
        self.reupload_url = kwargs.get('reupload_url', None)
        if self.reupload_url is not None:
            self.reupload_url = str(self.reupload_url).replace(r'\n', '')

    def get_original_url(self):
        return f"https://www.youtube.com/watch?v={self.id}"

    def get_quality(self):

        if self.__local_quality_height is None or self.__local_quality_width is None:
            return None

        return int(self.__local_quality_width), int(self.__local_quality_height)

    def __eq__(self, other):

        if not isinstance(other, ETCVideo):
            return False

        if other.id == self.id:
            return True
        else:
            return False

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return f"DatabaseVideo(**{self.as_dict()})"

    @staticmethod
    def __skip_invalid_strings(l: list):
        return [s for s in l if s not in INVALID_STRINGS]

    def as_dict(self, pretty=False):
        d = {}
        d['id'] = self.id
        if self.title is not None:
            d['title'] = self.title
        if self.description is not None:
            d['description'] = self.description
        if self.duration is not None:
            d['duration'] = self.duration
        if self.date_published is not None:
            d['date_published'] = self.date_published
        if self.uploader is not None:
            d['uploader'] = self.uploader
        if self.__local_quality_width is not None:
            d['local_quality_width'] = self.__local_quality_width
        if self.__local_quality_height is not None:
            d['local_quality_height'] = self.__local_quality_height
        if self.archived is not None:
            d['archived'] = self.archived
        if self.on_youtube is not None:
            d['on_youtube'] = self.on_youtube
        if self.reupload_url is not None:
            d['reupload_url'] = self.reupload_url

        if len(self.alternate_titles) != 0:
            d['alternate_titles'] = self.alternate_titles
        if len(self.alternate_descriptions) != 0:
            d['alternate_descriptions'] = self.alternate_descriptions
        if len(self.alternate_uploaders) != 0:
            d['alternate_uploaders'] = self.alternate_uploaders
        if len(self.uploader_ids) != 0:
            d['uploader_ids'] = self.uploader_ids
        if len(self.tags) != 0:
            d['tags'] = self.tags
        if len(self.duplicate_of) != 0:
            d['duplicate_of'] = self.duplicate_of

        return d
