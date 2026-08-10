import json
from pathlib import Path


class DiseaseCache:

    def __init__(self):

        self.file = Path("cache/disease_cache.json")

        self.file.parent.mkdir(parents=True, exist_ok=True)

        if not self.file.exists():
            self.file.write_text("{}", encoding="utf-8")

    def _get_name(self, disease):
        """
        Accepts either:
            - "Rett Syndrome"
            - Disease(name="Rett Syndrome", ...)
        """

        if isinstance(disease, str):
            return disease.lower().strip()

        if hasattr(disease, "name"):
            return str(disease.name).lower().strip()

        raise TypeError(
            f"Unsupported disease type: {type(disease)}"
        )

    def _load(self):

        with open(self.file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data):

        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def get(self, disease):

        name = self._get_name(disease)

        data = self._load()

        return data.get(name)

    def save(self, disease, value):

        name = self._get_name(disease)

        data = self._load()

        data[name] = value

        self._save(data)

    def clear(self):

        self._save({})
