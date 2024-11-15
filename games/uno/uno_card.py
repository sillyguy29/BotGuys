"""
This module contains the definition of an uno card. An uno card has __eq__, __lt__ and __gt__
methods that different from a normal card and have a different __str__ method.
"""

from util import Card

class UnoCard(Card):
    """
    This class represents an Uno card. On construction, it uses its
    name and value to establish a priority, used for sorting in a list.
    """

    def __str__(self):
        return f"{self.name} {self.value}"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        if self.name != other.name:
            return False
        if self.value != other.value:
            return False
        return True

    def __lt__(self, other):
        if self.name != other.name:
            return self.name < other.name
        return self.value < other.value

    def __gt__(self, other):
        #return self.priority > other.priority
        if self.name != other.name:
            return self.name > other.name
        return self.value > other.value
