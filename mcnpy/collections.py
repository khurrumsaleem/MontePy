from abc import ABC, abstractmethod


class Collection(ABC):
    """A collections of cells."""

    def __init__(self, obj_class, objects=None):
        """
        :param cells: the list of cells to start with if needed
        :type cells: list
        """
        if objects:
            assert isinstance(objects, list)
            for obj in objects:
                assert isinstance(obj, obj_class)
            self._objects = objects
        else:
            self._objects = []

    @abstractmethod
    def numbers(self):
        """
        A generator of the numbers being used.

        This should be a property
        """
        pass

    def check_redundant_numbers(self):
        """
        Checks if there are any redundant  numbers.
        :returns: true if there are collisions of numbers
        :rtype: bool
        """
        return len(self._objects) != len(set(self.numbers))

    def remove(self, delete):
        self._objects.remove(delete)

    def __iter__(self):
        self._iter = self._objects.__iter__()
        return self._iter

    def __next__(self):
        return self._iter.__next__()

    @abstractmethod
    def append(self, cell):
        pass

    def __getitem__(self, i):
        return self._objects[i]

    def __len__(self):
        return len(self._objects)

    @abstractmethod
    def __iadd__(self, other):
        pass
