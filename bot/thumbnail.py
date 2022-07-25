import asyncio
import aioipfs
import aiohttp
import logging
import random
import json
log = logging.getLogger("root")

TRUSTED_PUBLIC_IPFS_GATEWAYS = ("https://ipfs.io", "https://dweb.link", "https://gateway.ipfs.io", "https://cloudflare-ipfs.com")
RECHECK_IPNS_TIME_S = 18000
IPFS_THUMBNAIL_GET_TIMEOUT = 3


class IPFSThumbnailHandler:

    def __init__(self, ipns_hash, cache_file=None,
                 ipfs_host=None,
                 ipfs_port=None):
        self.__ipns_hash = ipns_hash
        self.__ipfs_thumb_folder_hash = None
        self.__ipfs_client = aioipfs.AsyncIPFS(host='localhost' if ipfs_host is None else ipfs_host,
                                               port=5001 if ipfs_port is None else ipfs_port)
        self.__cache_file = cache_file
        if self.__cache_file is not None:
            try:
                with open(self.__cache_file) as f:
                    self.__ipfs_thumb_folder_hash = json.load(f).get('thumb_folder_hash')
                    log.debug(f"Loaded thumb_folder_hash from cache: {self.__ipfs_thumb_folder_hash}")
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                pass

    async def __save_thumb_folder_hash(self, t_hash):
        try:
            with open(self.__cache_file, 'w') as f:
                log.debug(f"Writing thumb_folder_hash to cache file: {self.__cache_file}")
                json.dump({'thumb_folder_hash': t_hash}, f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            log.error("Failed to write thumb_folder_hash to cache file")

    async def __update_pins(self):
        """
        Ensure latest thumbnail folder to IPFS
        """
        log.info("Updating IPFS thumb folder pin...")
        current_prog = None
        if self.__ipfs_thumb_folder_hash is None:
            log.error("Failed to update thumb folder pin: ipfs_thumb_folder_hash is yet to be resolved!")
        async for status in self.__ipfs_client.pin.add(self.__ipfs_thumb_folder_hash, recursive=True, progress=True):
            try:
                if status['Progress'] != current_prog:
                    current_prog = status['Progress']
                    log.debug(f"Thumb folder pin adding progress: Fetched/Processed {current_prog} nodes.")
            except (IndexError, KeyError):
                continue
        log.info("Completed adding thumb folder to IPFS client pins.")
        pinned = await self.__ipfs_client.pin.ls()
        log.debug(f"Pins: {pinned}")

    async def start_ipns_checker(self):
        await self.__update_pins()  # make sure cached file is pinned
        while True:
            try:
                # Resolve for the root folder
                root_folder = await self.__ipfs_client.core.resolve("/ipns/" + self.__ipns_hash)
                log.debug(f"Resolved to {root_folder.get('Path')}")
                # Now get the hash for the ETC_DATABASE_THUMBNAILS folder
                thumb_folder = await self.__ipfs_client.core.resolve(root_folder.get('Path') + "/ETC_DATABASE_THUMBNAILS")
                log.debug(f"Resolved thumbnail folder {thumb_folder}")
                self.__ipfs_thumb_folder_hash = thumb_folder.get('Path')
                await self.__save_thumb_folder_hash(thumb_folder.get('Path'))
                await self.__update_pins()
            except aioipfs.APIError:
                log.critical("Failed to get latest thumbnail folder IPFS hash.")
            await asyncio.sleep(RECHECK_IPNS_TIME_S)

    @staticmethod
    async def get_random_gateway():
        return random.choice(TRUSTED_PUBLIC_IPFS_GATEWAYS)

    async def get_thumb_url(self, video_id):
        gateway = await self.get_random_gateway()
        try:
            data = await asyncio.wait_for(self.__ipfs_client.core.resolve(self.__ipfs_thumb_folder_hash + f"/{video_id[0]}/{video_id}.jpg"), timeout=IPFS_THUMBNAIL_GET_TIMEOUT)
            log.debug(f"Resolved thumbnail to {data['Path']}")
        except aioipfs.APIError:
            log.critical(f"Failed to get IPFS hash for thumbnail {video_id}.jpg (doesn't exist?)")
            return None
        except asyncio.TimeoutError:
            log.error(f"Failed to get IPFS hash for thumbnail {video_id}.jpg (timed out). Returning file path instead.")
            return gateway + self.__ipfs_thumb_folder_hash + f"/{video_id[0]}/{video_id}.jpg"
        except (aiohttp.ServerDisconnectedError, aiohttp.ClientConnectionError):
            log.error(f"Failed to get IPFS hash for thumbnail {video_id}.jpg (cannot connect to IPFS client)."
                      f" Returning file path instead.")
            return gateway + self.__ipfs_thumb_folder_hash + f"/{video_id[0]}/{video_id}.jpg"
        except TypeError:
            log.error("ipfs_thumb_folder_hash has yet to be resolved!")
            return None
        return gateway + data['Path']

    async def get_thumb_folder(self):
        gateway = await self.get_random_gateway()
        return gateway + self.__ipfs_thumb_folder_hash
