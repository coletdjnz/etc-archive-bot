from elasticsearch import AsyncElasticsearch
from video import ETCVideo
import logging
import math
log = logging.getLogger('root')

"""

This wil handle all the interaction to the ETC Database

It returns database data as ETCVideo objects, 
as well gathering data from all 3 databases.

"""


class ETCDatabase:

    def __init__(self, etc_index, youtube_index, local_index, **kwargs):
        self._etc_index = etc_index
        self._youtube_index = youtube_index
        self._local_index = local_index
        self.__es_object = None
        self.connect(**kwargs)

    def connect(self, **kwargs):
        self.__es_object = AsyncElasticsearch(**kwargs)

    async def get_client(self):
        return self.__es_object

    async def search(self, query):
        # Search main database for query
        try:
            videos_raw = await self.__es_object.search(index=self._etc_index, body=query)

            videos_raw = videos_raw['hits']['hits']

            # Inject data about the videos from the other databases
            for index, item in enumerate(videos_raw):
                video_id = item['_source']['id']

                reupload_vid = await self.get_reupload_vid(video_id)
                local_yt_vid = await self.get_archived_vid(video_id)

                if len(reupload_vid) > 0:
                    videos_raw[index]['_source'].update({'on_youtube': True, 'reupload_url': f"https://www.youtube.com/watch?v={reupload_vid['id']}"})
                if len(local_yt_vid) > 0:
                    videos_raw[index]['_source'].update({'archived': True,
                                   'local_quality_width': local_yt_vid['width'],
                                    'local_quality_height': local_yt_vid['height']})
            return await self._convert_to_etcvideo(videos_raw)
        except ValueError:
            log.error("KeyError while searching database")

        return []

    # Returns the reupload video
    # Note: this will return 1 result only
    async def get_reupload_vid(self, video_id):
        try:
            s = await self.__es_object.search(index=self._youtube_index, body={'query': {'match_phrase': {"original_id": video_id}}})
            return s['hits']['hits'][0]['_source']
        except (KeyError, IndexError):
            return {}

    async def get_archived_vid(self, video_id):
        try:
            s = await self.__es_object.search(index=self._local_index, body={'query': {'match_phrase': {"id": video_id}}})
            return s['hits']['hits'][0]['_source']
        except (KeyError, IndexError):
            return {}

    @staticmethod
    async def _convert_to_etcvideo(videos: list):
        return [ETCVideo(**v['_source']) for v in videos]

    async def get_stats(self, phrases=None):

        if phrases is None:
            phrases = []
        # Generates statistics about the database
        total_db = await self.get_count(index=self._etc_index)
        total_reuploaded = await self.get_count(index=self._youtube_index)
        total_classic = await self.get_count_by_field(index=self._local_index, field="collection", phrase="Classic ETC")
        total_modern = await self.get_count_by_field(index=self._local_index, field="collection", phrase="Modern ETC")

        num_video_archived = total_classic + total_modern

        phrase_stats = {}

        for phrase in set(phrases):
            phrase_stats[phrase] = await self.get_stats_by_phrase(phrase)

        pure_modern_etc_archived = await self.modern_etc_main_channel()
        return {
            'total': total_db,
            'total_archived': num_video_archived,
            'total_reuploaded': total_reuploaded,
            'total_classic': total_classic,
            'total_modern': total_modern,
            'pure_modern_etc_archived': pure_modern_etc_archived,
            'phrase': phrase_stats
        }

    async def get_stats_by_phrase(self, phrase: str):
        """

        This grabs stats by phrase in the title
        E.g "Weekly Weird News"

        1. Get ids of videos with the phrase in title in the main db [total altogether]
        2. Get number of videos in youtube db by those id [total uploaded to yt]
        3. Get number of videos in local db by those ids [total archived]

        returns a tuple
        (total, total_yt, total_archived)
        """
        log.info(f"Getting stats for phrase {phrase}")
        videos_main_db = await self.__es_object.search(index=self._etc_index, size=10000, body={"_source": ['id'], "query": {
            "match_phrase": {'title': phrase}}})

        videos_yt_db = await self.multi_search(index=self._youtube_index, field="original_id",
                                    items=[a['_source']['id'] for a in videos_main_db['hits']['hits']])

        videos_lcl_db = await self.multi_search(index=self._local_index, field="id",
                                    items=list(set([a['_source']['id'] for a in videos_main_db['hits']['hits']])))
        videos_on_yt = 0
        for response in videos_yt_db['responses']:
            videos_on_yt += response['hits']['total']['value']

        videos_archived = 0
        hits = []
        for a in videos_lcl_db['responses']:
            if a['hits']['total']['value'] == 1:
                try:
                    hits.append(a['hits']['hits'][0]['_source']['id'])
                except KeyError:
                    raise KeyError
        videos_archived += len(set(hits))

        return {'total': videos_main_db['hits']['total']['value'], 'total_reuploaded': videos_on_yt, 'total_archived':videos_archived}

    async def multi_search(self, index, field, items: list):
        if len(items) == 0:
            return []
        list_of_queries = []
        for thing in items:
            list_of_queries.append({"index": index})
            list_of_queries.append({"_source": True, "query": {"match_phrase": {field: thing}}})

        return await self.__es_object.msearch(list_of_queries[:-1])

    async def get_count_by_field(self, index, field, phrase):
        data = await self.__es_object.count(index=index, body={'query': {'match_phrase': {field: phrase}}})
        return data['count']

    async def get_count(self, index):
        data = await self.__es_object.cat.count(index=index, params={"format": "json"})
        return int(data[0]['count'])

    async def get_date_range_query(self, date_epoch, range):
        query = {"range": {"date_published": {"format": "epoch_second", "gte": f"{date_epoch - (math.floor(range/2) * 86400)}", "lte": f"{date_epoch + (math.ceil(range/2)*86400)}"}}}
        return query

    async def modern_etc_main_channel(self):
        query = {"query": {
            "bool": {
                "filter": [
                    {
                        "bool": {
                            "should": [
                                {
                                    "bool": {
                                        "should": [
                                            {
                                                "match_phrase": {
                                                    "uploader_ids": "MachinimaETC"
                                                }
                                            }
                                        ],
                                        "minimum_should_match": 1
                                    }
                                },
                                {
                                    "bool": {
                                        "should": [
                                            {
                                                "bool": {
                                                    "should": [
                                                        {
                                                            "match_phrase": {
                                                                "uploader_ids": "UCdIaNUarhzLSXGoItz7BHVA"
                                                            }
                                                        }
                                                    ],
                                                    "minimum_should_match": 1
                                                }
                                            },
                                            {
                                                "bool": {
                                                    "should": [
                                                        {
                                                            "match_phrase": {
                                                                "uploader": "etc show"
                                                            }
                                                        }
                                                    ],
                                                    "minimum_should_match": 1
                                                }
                                            }
                                        ],
                                        "minimum_should_match": 1
                                    }
                                }
                            ],
                            "minimum_should_match": 1
                        }
                    },
                    {
                        "range": {
                            "date_published": {
                                "format": "strict_date_optional_time",
                                "gte": "2014-06-01T00:00:00.000Z",
                                "lte": "2019-01-24T23:21:13.800Z"
                            }
                        }
                    }
                ],
            }
        }}

        videos_main_db = await self.__es_object.search(index=self._etc_index, size=10000,
                                                       body={"_source": ['id'], **query})

        videos_main_db_set = [a['_source']['id'] for a in videos_main_db['hits']['hits']]
        videos_lcl_db = await self.multi_search(index=self._local_index, field="id",
                                                items=videos_main_db_set)

        hits = []
        try:
            for a in videos_lcl_db['responses']:
                if a['hits']['total']['value'] == 1:
                    try:
                        hits.append(a['hits']['hits'][0]['_source']['id'])
                    except KeyError:
                        raise KeyError
        except TypeError:
            pass

        return len(set(hits)), len(videos_main_db_set)