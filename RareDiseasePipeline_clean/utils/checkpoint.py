"""
RareDiseasePipeline
Checkpoint Manager

Author: Harsh Nalgirkar
"""

from pathlib import Path
import json
from datetime import datetime


class CheckpointManager:

    def __init__(self, checkpoint_file="cache/checkpoint.json"):

        self.checkpoint_file = Path(checkpoint_file)

        self.checkpoint_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.checkpoint_file.exists():

            self.reset()

    # ----------------------------------------------------------

    def reset(self):

        data = {
            "completed_stages": {},
            "context": {},
            "last_stage": None,
            "timestamp": None
        }

        self.save(data)

    # ----------------------------------------------------------

    def load(self):

        with open(self.checkpoint_file) as f:

            return json.load(f)

    # ----------------------------------------------------------

    def save(self, data):

        with open(self.checkpoint_file, "w") as f:

            json.dump(
                data,
                f,
                indent=4
            )

    # ----------------------------------------------------------

    def mark_completed(
        self,
        stage_number,
        stage_name,
        context
    ):

        data = self.load()

        data["completed_stages"][str(stage_number)] = {

            "name": stage_name,

            "completed": True

        }

        data["last_stage"] = stage_number

        data["timestamp"] = datetime.now().isoformat()

        data["context"] = context

        self.save(data)

    # ----------------------------------------------------------

    def is_completed(self, stage_number):

        data = self.load()

        return str(stage_number) in data["completed_stages"]

    # ----------------------------------------------------------

    def get_context(self):

        return self.load()["context"]

    # ----------------------------------------------------------

    def get_last_stage(self):

        return self.load()["last_stage"]

    # ----------------------------------------------------------

    def clear(self):

        if self.checkpoint_file.exists():

            self.checkpoint_file.unlink()

        self.reset()