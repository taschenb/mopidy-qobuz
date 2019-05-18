from __future__ import unicode_literals

import logging
import qobuz
from mopidy import models
from mopidy_qobuz import translator


def browse_favorite_artists(session):
    return [
        translator.to_artist_ref(a)
        for a in session.favorites_get(fav_type="artists")
    ]


def browse_favorite_albums(session):
    return [
        translator.to_album_ref(a)
        for a in session.favorites_get(fav_type="albums")
    ]


def browse_new_albums(session):
    return [
        translator.to_album_ref(a)
        for a in qobuz.Album.get_featured(type="new-releases")
    ]


def browse_most_streamed_albums(session):
    return [
        translator.to_album_ref(a)
        for a in qobuz.Album.get_featured(type="most-streamed")
    ]


def browse_press_awards_albums(session):
    return [
        translator.to_album_ref(a)
        for a in qobuz.Album.get_featured(type="press-awards")
    ]


def browse_editor_picks_albums(session):
    return [
        translator.to_album_ref(a)
        for a in qobuz.Album.get_featured(type="editor-picks")
    ]


def browse_favorite_tracks(session):
    return [
        translator.to_track_ref(t)
        for t in session.favorites_get(fav_type="tracks")
    ]


def browse_favorite_playlists(session):
    return [translator.to_playlist_ref(p) for p in session.playlists_get()]


def browse_artist(artist_id):
    return [
        translator.to_album_ref(a)
        for a in qobuz.Artist.from_id(uri_item.id).get_all_albums()
    ]


def browse_album(album_id):
    return [
        translator.to_track_ref(t)
        for t in qobuz.Album.from_id(album_id).tracks
    ]


def browse_playlist(playlist_id):
    return []
    return [
        translator.to_track_ref(t)
        for t in qobuz.Playlist.from_id(
            playlist_id, self.backend._session
        ).get_tracks(limit=500)
    ]


def browse_details(uri, session):
    lookup_directly = {
        "artist": browse_artist,
        "album": browse_album,
        "playlist": browse_playlist,
    }

    parts = uri.split(":")

    if parts[1] in lookup_directly:
        return lookup_directly[parts[1]](parts[2])


def browse(uri, session):
    if uri.startswith("qobuz:directory:"):
        return browse_directory(uri, session)
    else:
        return browse_details(uri, session)


def browse_directory(uri, session):
    tree = {
        "qobuz": {
            "name": "Qobuz",
            "sub": {
                "favorites": {
                    "name": "Favorites",
                    "sub": {
                        "artists": {
                            "name": "Artists",
                            "browse": browse_favorite_artists,
                        },
                        "albums": {
                            "name": "Albums",
                            "browse": browse_favorite_albums,
                        },
                        "tracks": {
                            "name": "Tracks",
                            "browse": browse_favorite_tracks,
                        },
                        "playlists": {
                            "name": "Playlists",
                            "browse": browse_favorite_playlists,
                        },
                    },
                },
                "featured": {
                    "name": "Featured",
                    "sub": {
                        "newReleases": {
                            "name": "New Releases",
                            "browse": browse_new_albums,
                        },
                        "mostStreamed": {
                            "name": "Most streamed",
                            "browse": browse_most_streamed_albums,
                        },
                        "pressAwards": {
                            "name": "Press Awards",
                            "browse": browse_press_awards_albums,
                        },
                        "editorPicks": {
                            "name": "Editor Picks",
                            "browse": browse_editor_picks_albums,
                        },
                    },
                },
            },
        }
    }

    parts = uri.split(":")

    if len(parts) < 2 or parts[0] != "qobuz":
        logger.error("Not able to browse %s", uri)
        return []

    for p in parts:
        if p == "directory":
            pass
        elif p in tree:
            tree = tree[p]
        elif p in tree.get("sub"):
            tree = tree["sub"][p]
        else:
            break

    if "browse" in tree:
        return tree["browse"](session)
    if "sub" in tree:
        return [
            models.Ref.directory(uri=uri + ":" + u, name=i["name"])
            for u, i in tree["sub"].items()
        ]

    logger.error("Not able to browse %s", uri)
    return []
