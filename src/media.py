from abc import ABC, abstractmethod


class Media(ABC):
    async def rip(self):
        await self.preprocess()
        await self.download()
        await self.postprocess()

    @abstractmethod
    async def preprocess(self):
        """Create directories, download cover art, etc."""
        raise NotImplemented

    @abstractmethod
    async def download(self):
        """Download and tag the actual audio files in the correct directories."""
        raise NotImplemented

    @abstractmethod
    async def postprocess(self):
        """Update database, run conversion, delete garbage files etc."""
        raise NotImplemented


class Pending(ABC):
    """A request to download a `Media` whose metadata has not been fetched."""

    @abstractmethod
    async def resolve(self) -> Media:
        """Fetch metadata and resolve into a downloadable `Media` object."""
        raise NotImplemented