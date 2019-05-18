from __future__ import unicode_literals

import binascii
import logging
import os
import threading
import pykka
import qobuz
from itertools import cycle
from mopidy import backend, httpclient
from mopidy_qobuz import library, playback, playlists


logger = logging.getLogger(__name__)


class QobuzBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, config, audio):
        super(QobuzBackend, self).__init__()

        self._config = config
        self._session = None

        self.library = library.QobuzLibraryProvider(backend=self)
        self.playback = playback.QobuzPlaybackProvider(
            audio=audio, backend=self
        )
        self.playlists = playlists.QobuzPlaylistsProvider(backend=self)
        self.uri_schemes = ["qobuz"]

    def on_start(self):
        self._actor_proxy = self.actor_ref.proxy()

        # Kodi
        app_id = "285473059"
        s3b = "Bg8HAA5XAFBYV15UAlVVBAZYCw0MVwcKUVRaVlpWUQ8="
        qobuz.api.register_app(
            app_id=app_id, app_secret=self.get_s4(app_id, s3b)
        )

        self._session = qobuz.User(
            self._config["qobuz"]["username"],
            self._config["qobuz"]["password"],
        )

    def get_s4(self, app_id, s3b):
        """Return the obfuscated secret.

        This is based on the way the Kodi-plugin handles the secret.

        While this is just a useless security through obscurity measurement and
        could just be calculated once, this functions allows to store the secret
        in a not plain text format. Which might be a requirement by Qobuz.
        Until the API-team feels like answering any of the mails, this uses the
        same obfuscation as Kodi.

        Parameters
        ----------
        app_id: str
            The ID of the APP, issued by api@qobuz.com
        s3b: str
            Secret encoded for security through obscurity.
        """
        s3s = binascii.a2b_base64(s3b)

        try:
            return "".join(
                chr(x ^ ord(y)) for (x, y) in zip(s3s, cycle(app_id))
            )
        except TypeError:
            # python2
            return "".join(
                chr(ord(x) ^ ord(y)) for (x, y) in zip(s3s, cycle(app_id))
            )
