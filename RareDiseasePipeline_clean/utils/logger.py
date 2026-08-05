import logging
import os

os.makedirs("logs", exist_ok=True)


class PipelineLogger:
    def __init__(self):
        self.logger = logging.getLogger("RareDiseasePipeline")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s"
            )

            console = logging.StreamHandler()
            console.setFormatter(formatter)

            logfile = logging.FileHandler("logs/pipeline.log")
            logfile.setFormatter(formatter)

            self.logger.addHandler(console)
            self.logger.addHandler(logfile)

    # Standard logging
    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    # Custom helpers
    def section(self, title):
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info(f"📂 {title}")
        self.logger.info("=" * 70)

    def stage(self, number, title):
        self.logger.info("")
        self.logger.info(f"[Stage {number}] {title}")

    def success(self, message):
        self.logger.info(f"✅ {message}")

    def failed(self, message):
        self.logger.error(f"❌ {message}")


logger = PipelineLogger()
