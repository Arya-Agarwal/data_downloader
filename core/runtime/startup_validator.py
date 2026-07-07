from pathlib import Path
import shutil

from config import (
    DATA_DIR,
    TRACKER_FILE,
    INSTRUMENT_MASTER_FILE
)

from core.logger import log

from core.runtime.runtime_metrics import (
    RuntimeMetrics
)


class StartupValidator:

    MIN_FREE_SPACE_GB = 5

    def __init__(self):

        self.metrics = RuntimeMetrics()

    def validate(self):

        log.info(
            "========== STARTUP VALIDATION =========="
        )

        self.metrics.reset()

        self.check_directory(
            DATA_DIR
        )

        self.check_file(
            TRACKER_FILE,
            "Tracker"
        )

        self.check_file(
            INSTRUMENT_MASTER_FILE,
            "Instrument Master"
        )

        self.check_disk()

        log.info(
            "Startup validation passed."
        )

    def check_directory(
        self,
        path
    ):

        Path(path).mkdir(
            parents=True,
            exist_ok=True
        )

        test_file = (
            Path(path)
            / ".write_test"
        )

        try:

            test_file.write_text(
                "ok"
            )

            test_file.unlink()

        except Exception:

            raise RuntimeError(
                f"Directory not writable: {path}"
            )

    def check_file(
        self,
        path,
        name
    ):

        if not Path(path).exists():

            raise RuntimeError(
                f"{name} missing: {path}"
            )

    def check_disk(self):

        usage = shutil.disk_usage(
            DATA_DIR
        )

        free_gb = (
            usage.free
            / 1024
            / 1024
            / 1024
        )

        log.info(
            f"Free disk: "
            f"{free_gb:.2f} GB"
        )

        if free_gb < self.MIN_FREE_SPACE_GB:

            raise RuntimeError(
                "Insufficient disk space."
            )