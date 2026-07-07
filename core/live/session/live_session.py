from core.logger import log


class LiveSession:

    def __init__(self):

        self.current_high = None
        self.current_low = None
        self.current_ltp = None

    def update(self, ltp):

        self.current_ltp = ltp

        if self.current_high is None:
            self.current_high = ltp

        if self.current_low is None:
            self.current_low = ltp

        changed = False

        if ltp > self.current_high:
            self.current_high = ltp
            changed = True

        if ltp < self.current_low:
            self.current_low = ltp
            changed = True

        return changed

    def get_range(self):

        return (
            self.current_low,
            self.current_high
        )

    def reset(self):

        log.info(
            "Resetting live session."
        )

        self.current_high = None
        self.current_low = None
        self.current_ltp = None