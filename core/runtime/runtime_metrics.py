from datetime import datetime

from core.utils.time_utils import (
    now_ist
)


class RuntimeMetrics:

    _instance = None

    def __new__(cls):

        if cls._instance is None:

            cls._instance = super().__new__(
                cls
            )

            cls._instance.reset()

        return cls._instance

    def reset(self):

        self.start_time = now_ist()

        self.connected = False

        self.reconnects = 0

        self.last_tick = None

        self.total_ticks = 0

        self.spot_ticks = 0

        self.future_ticks = 0

        self.option_ticks = 0

        self.rows_written = 0

        self.files_written = 0

        self.disk_writes = 0

        self.buffer_size = 0

        self.subscribed = 0

        self.shutdown = False

    def websocket_connected(self):

        self.connected = True

    def websocket_disconnected(self):

        self.connected = False

    def reconnect(self):

        self.reconnects += 1

    def tick_received(
        self,
        segment
    ):

        self.last_tick = now_ist()

        self.total_ticks += 1

        segment = segment.upper()

        if segment == "INDICES":

            self.spot_ticks += 1

        elif segment == "NFO-FUT":

            self.future_ticks += 1

        elif segment == "NFO-OPT":

            self.option_ticks += 1

    def rows_added(
        self,
        rows
    ):

        self.rows_written += rows

    def file_written(self):

        self.files_written += 1

        self.disk_writes += 1

    def update_buffer(
        self,
        size
    ):

        self.buffer_size = size

    def update_subscriptions(
        self,
        count
    ):

        self.subscribed = count

    def graceful_shutdown(self):

        self.shutdown = True