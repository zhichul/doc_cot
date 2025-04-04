from abc import ABC, abstractmethod

class Lookup(ABC):

    @abstractmethod
    def get_doc(self, id: any):
        pass