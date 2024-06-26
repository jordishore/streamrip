from dataclasses import dataclass

from ..client import Client
from ..config import Config
from ..db import Database
from ..metadata import LabelMetadata
from .album import PendingAlbum
from .album_list import AlbumList
from .media import Pending


class Label(AlbumList):
    pass


@dataclass(slots=True)
class PendingLabel(Pending):
    id: str
    client: Client
    config: Config
    db: Database

    async def resolve(self) -> Label:
        resp = await self.client.get_metadata(self.id, "label")
        meta = LabelMetadata.from_resp(resp, self.client.source)
        albums = [
            PendingAlbum(album_id, self.client, self.config, self.db)
            for album_id in meta.album_ids()
        ]
        return Label(meta.name, albums, self.client, self.config)
