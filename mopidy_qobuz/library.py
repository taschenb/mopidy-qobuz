from __future__ import unicode_literals

import logging
import qobuz
from collections import namedtuple
from mopidy import backend, models
from mopidy.models import Image, SearchResult
from mopidy_qobuz import translator
from mopidy_qobuz import browse

try:
    from functools import lru_cache
except ImportError:
    # python2
    from backports.functools_lru_cache import lru_cache


logger = logging.getLogger(__name__)


class QobuzLibraryProvider(backend.LibraryProvider):
    root_directory = models.Ref.directory(uri="qobuz:directory", name="Qobuz")

    def __init__(self, *args, **kwargs):
        super(QobuzLibraryProvider, self).__init__(*args, **kwargs)

    def browse(self, uri):
        if uri.startswith(self.root_directory.uri):
            return browse.browse_directory(uri, self.backend._session)
        else:
            return browse.browse_details(uri, self.backend._session)

    def search(self, query=None, uris=None, exact=False):
        field = query.keys()[0]
        value = query.values()[0]

        if field == "artist":
            artists = [
                translator.to_artist(a) for a in qobuz.Artist.search(value)
            ]
            return SearchResult(artists=artists)
        elif field == "album":
            albums = [
                translator.to_album(a) for a in qobuz.Album.search(value)
            ]
            return SearchResult(albums=albums)
        elif field == "track":
            tracks = [
                translator.to_track(t) for t in qobuz.Track.search(value)
            ]
            return SearchResult(tracks=tracks)

        artists = [translator.to_artist(a) for a in qobuz.Artist.search(value)]
        albums = [translator.to_album(a) for a in qobuz.Album.search(value)]
        tracks = [translator.to_track(t) for t in qobuz.Track.search(value)]
        return SearchResult(artists=artists, albums=albums, tracks=tracks)

    @lru_cache(maxsize=2048)
    def lookup(self, uri):
        parts = uri.split(":")

        if uri.startswith("qobuz:artist"):
            # qobuz:artist:artist_id
            return [
                translator.to_track(t)
                for t in qobuz.Artist.from_id(parts[2]).get_all_tracks(
                    limit=150
                )
            ]

        if uri.startswith("qobuz:track:"):
            # qobuz:track:artist_id:album_id:track_id
            return [translator.to_track(qobuz.Track.from_id(parts[4]))]

        if uri.startswith("qobuz:album"):
            # qobuz:album:album:id
            qobuz_album = qobuz.Album.from_id(parts[2])

            return [
                translator.to_track(t, qobuz_album) for t in qobuz_album.tracks
            ]

        logger.warning('Failed to lookup "%s"', uri)
