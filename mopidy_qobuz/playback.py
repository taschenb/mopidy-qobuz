from __future__ import unicode_literals

import logging
import pykka
import qobuz

from mopidy import audio, backend

logger = logging.getLogger(__name__)


class QobuzPlaybackProvider(backend.PlaybackProvider):
    def __init__(self, audio, backend):
        super(QobuzPlaybackProvider, self).__init__(audio, backend)

        self.delta = 0
        self._current_event = None

    def report_current_ending(self):
        """Report to Qobuz the duration of the playback.

        Qobuz requires a report when a song ends, containing the duration of how
        long the track was actually listend to. Not including pauses or skipped
        sections. And including parts playing multiple times.
        """
        if self._current_event is None:
            logger.debug("Nothing to report")
            return

        duration = self.get_time_position() + self.delta
        duration = int(duration / 1000)  # ms -> s
        logger.info(
            "Report ending of {} (played for {}s)".format(
                self._current_event.track_id, duration
            )
        )
        self._current_event.report_end(duration)

        # Make sure to not report twice
        self._current_event = None

    def update_event(self, new_track_id):
        """Update the event in order to report its start/end to Qobuz.

        Parameters
        ----------
        new_track_id: int
            ID for the next track
        """
        self.report_current_ending()

        self._current_event = qobuz.Event(
            user=self.backend._session, track_id=new_track_id, format_id=27
        )

    def translate_uri(self, uri):
        """Get file-URL for a track-uri in mopidy.

        Parameters
        ----------
        uri: str
            Mopidy URI of a track
        """
        parts = uri.split(":")
        track_id = int(parts[4])

        newurl = self.backend._session.get_file_url(track_id, intent="stream")

        self.update_event(track_id)

        return newurl

    def seek(self, time_position):
        """Keep track of how long we listened to the song.

        Qobuz requires a report of how long each song played. So each time we
        seek, a delta is recorded that will be added to the duration.
        """
        self.delta = self.get_time_position() - time_position

        return super(QobuzPlaybackProvider, self).seek(time_position)

    def stop(self):
        """Report to Qobuz the duration of the playback and stop."""
        self.report_current_ending()

        return super(QobuzPlaybackProvider, self).stop()

    def play(self):
        """Report to Qobuz the start of the playback and start."""
        logger.info(
            "Report starting of {}".format(self._current_event.track_id)
        )
        self._current_event.report_start()

        return super(QobuzPlaybackProvider, self).play()
