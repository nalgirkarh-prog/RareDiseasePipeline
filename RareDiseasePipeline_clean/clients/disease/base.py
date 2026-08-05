from abc import ABC, abstractmethod


class DiseaseDatabase(ABC):

    @abstractmethod
    def search(self, disease_name):
        pass
