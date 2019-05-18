from __future__ import unicode_literals

import collections
import logging
import qobuz
from mopidy import models

try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache


logger = logging.getLogger(__name__)


def to_artist(qobuz_artist):
    if qobuz_artist is None:
        return

    return models.Artist(
        uri="qobuz:artist:" + str(qobuz_artist.id), name=qobuz_artist.name
    )


def to_artist_ref(qobuz_artist):
    if qobuz_artist is None:
        return

    return models.Ref.artist(
        uri="qobuz:artist:" + str(qobuz_artist.id), name=qobuz_artist.name
    )


def to_album(qobuz_album):
    if qobuz_album is None:
        return

    artist = to_artist(qobuz_album.artist)

    return models.Album(
        uri="qobuz:album:" + str(qobuz_album.id),
        name=qobuz_album.title,
        artists=[artist],
    )


def to_album_ref(qobuz_album):
    if qobuz_album is None:
        return

    return models.Ref.album(
        uri="qobuz:album:" + str(qobuz_album.id),
        name="{} - {}".format(qobuz_album.artist.name, qobuz_album.title),
    )


@lru_cache(maxsize=1024)
def qobuz_track_artist_lookup(qobuz_performer_id):
    if qobuz_performer_id is not None:
        return qobuz.Artist.from_id(qobuz_performer_id)


def to_track(qobuz_track, qobuz_album=None):
    if qobuz_track is None:
        return
    if qobuz_album is None:
        # Make an API call to request the album
        qobuz_album = qobuz_track.album

    album = to_album(qobuz_album)
    artist = to_artist(qobuz_track_artist_lookup(qobuz_track._performer_id))
    if artist is None or album is None:
        return

    return models.Track(
        uri="qobuz:track:{0}:{1}:{2}".format(
            qobuz_album.artist.id, qobuz_album.id, qobuz_track.id
        ),
        name=qobuz_track.title,
        artists=[artist],
        album=album,
        length=qobuz_track.duration * 1000,  # s -> ms
        disc_no=qobuz_track.media_number,
        track_no=qobuz_track.track_number,
    )


def to_track_ref(qobuz_track):
    if qobuz_track is None:
        return

    return models.Ref.track(
        uri="qobuz:track:{0}:{1}:{2}".format(
            qobuz_track_artist_lookup(qobuz_track._performer_id),
            qobuz_track.album.id,
            qobuz_track.id,
        ),
        name=qobuz_track.title,
    )


def to_playlist(qobuz_playlist):
    if qobuz_playlist is None:
        return

    return models.Playlist(
        uri="qobuz:playlist:{}".format(qobuz_playlist.id),
        name=qobuz_playlist.name,
        tracks=qobuz_playlist.get_tracks(limit=500),
    )


def to_playlist_ref(qobuz_playlist):
    if qobuz_playlist is None:
        return

    return models.Ref.playlist(
        uri="qobuz:playlist:{}".format(qobuz_playlist.id),
        name=qobuz_playlist.name,
    )
