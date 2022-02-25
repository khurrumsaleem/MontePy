from abc import ABC, abstractmethod
from .block_type import BlockType
import math
from mcnpy.errors import *
import re


class MCNP_Input(ABC):
    """
    Object to represent a single coherent MCNP input, such as a card.
    """

    def __init__(self, input_lines):
        """
        :param input_lines: the lines read straight from the input file.
        :type input_lins: list
        """
        assert isinstance(input_lines, list)
        for line in input_lines:
            assert isinstance(line, str)
        self._input_lines = input_lines
        self._mutated = False

    @property
    def input_lines(self):
        """The lines of the input read straight from the input file

        :rtype: list
        """
        return self._input_lines

    @property
    def mutated(self):
        """If true this input has been mutated by the user, and needs to be formatted"""
        return self._mutated

    @abstractmethod
    def format_for_mcnp_input(self, mcnp_version):
        """
        Creates a string representation of this card that can be
        written to file.

        :param mcnp_version: The tuple for the MCNP version that must be exported to.
        :type mcnp_version: tuple
        :return: a list of strings for the lines that this card will occupy.
        :rtype: list
        """
        pass


class Card(MCNP_Input):
    """
    Represents a single MCNP "card" e.g. a single cell definition.
    """

    def __init__(self, input_lines, block_type, words):
        """
        :param block_type: An enum showing which of three MCNP blocks this was inside of.
        :type block_type: BlockType
        :param words: a list of the string representation of the words for the card definition
                        for example a material definition may contain: 'M10', '10001.70c', '0.1'
        :type words: list
        """
        super().__init__(input_lines)
        assert isinstance(block_type, BlockType)
        # setting twice so if error is found in parsing for convenient errors
        self._words = words
        self._block_type = block_type
        self._words = parse_card_shortcuts(words, self)

    def __str__(self):
        return f"CARD: {self._block_type}: {self._words}"

    @property
    def words(self):
        """
        A list of the string representation of the words for the card definition.

        For example a material definition may contain: 'M10', '10001.70c', '0.1'
        """
        return self._words

    @property
    def block_type(self):
        """
        Enum representing which block of the MCNP input this came from
        """
        return self._block_type

    def format_for_mcnp_input(self, mcnp_version):
        pass


def parse_card_shortcuts(words, card=None):
    number_parser = re.compile("(\d+\.*\d*[e\+\-]*\d*)")
    ret = []
    for i, word in enumerate(words):
        if i == 0:
            ret.append(word)
            continue
        letters = "".join(c for c in word if c.isalpha()).lower()
        if len(letters) >= 1:
            number = number_parser.search(word)
            if number:
                number = float(number.group(1))
            if letters == "r":
                try:
                    last_val = ret[-1]
                    if last_val is None:
                        raise IndexError
                    if number:
                        number = int(number)
                    else:
                        number = 1
                    ret += [last_val] * number
                except IndexError:
                    raise MalformedInputError(
                        card, "The repeat shortcut must come after a value"
                    )
            elif letters == "i":
                try:

                    begin = float(number_parser.search(ret[-1]).group(1))
                    for char in ["i", "m", "r", "i", "log"]:
                        if char in words[i + 1].lower():
                            raise IndexError

                    end = float(number_parser.search(words[i + 1]).group(1))
                    if number:
                        number = int(number)
                    else:
                        number = 1
                    spacing = (end - begin) / (number + 1)
                    for i in range(number):
                        new_val = begin + spacing * (i + 1)
                        ret.append(f"{new_val:g}")
                except (IndexError, TypeError, ValueError, AttributeError) as e:
                    raise MalformedInputError(
                        card,
                        "The interpolate shortcut must come between two values",
                    )
            elif letters == "m":
                try:
                    last_val = float(number_parser.search(ret[-1]).group(1))
                    if number is None:
                        raise MalformedInputError(
                            card,
                            "The multiply shortcut must have a multiplying value",
                        )
                    new_val = number * last_val
                    ret.append(f"{new_val:g}")

                except (IndexError, TypeError, ValueError, AttributeError) as e:
                    raise MalformedInputError(
                        card, "The multiply shortcut must come after a value"
                    )

            elif letters == "j":
                if number:
                    number = int(number)
                else:
                    number = 1
                ret += [None] * number
            elif letters in {"ilog", "log"}:
                try:
                    begin = math.log(float(number_parser.search(ret[-1]).group(1)), 10)
                    end = math.log(
                        float(number_parser.search(words[i + 1]).group(1)), 10
                    )
                    if number:
                        number = int(number)
                    else:
                        number = 1
                    spacing = (end - begin) / (number + 1)
                    for i in range(number):
                        new_val = 10 ** (begin + spacing * (i + 1))
                        ret.append(f"{new_val:g}")

                except (IndexError, TypeError, ValueError, AttributeError) as e:
                    raise MalformedInputError(
                        card,
                        "The log interpolation shortcut must come between two values",
                    )
            else:
                ret.append(word)
        else:
            ret.append(word)
    return ret


class ReadCard(Card):
    """
    A card for the read card that reads another input file
    """

    def __init__(self, input_lines, block_type, words):
        super().__init__(input_lines, block_type, words)
        file_finder = re.compile("file=(?P<file>[\S]+)", re.IGNORECASE)
        for word in words[1:]:
            match = file_finder.match(word)
            if match:
                self._file_name = match.group("file")

    @property
    def file_name(self):
        return self._file_name


class Comment(MCNP_Input):
    """
    Object to represent a full line comment in an MCNP problem.
    """

    def __init__(self, input_lines, lines):
        """
        :param lines: the strings of each line in this comment block
        :type lines: list
        """
        super().__init__(input_lines)
        assert isinstance(lines, list)
        buff = []
        for line in lines:
            buff.append(line.rstrip())
        self._lines = buff

    def __str__(self):
        ret = "COMMENT:\n"
        for line in self._lines:
            ret += line + "\n"
        return ret

    @property
    def lines(self):
        """
        The lines of input in this comment block.

        Each entry is a string of that line in the message block.
        The comment beginning "C " has been stripped out
        """
        return self._lines

    def format_for_mcnp_input(self, mcnp_version):
        line_length = 0
        if mcnp_version[0] == 6.2:
            line_length = 128
        ret = []
        for line in self.lines:
            ret.append("C " + line[0 : line_length - 3])
        return ret


class Message(MCNP_Input):
    """
    Object to represent an MCNP message.

    These are blocks at the beginning of an input that are printed in the output.
    """

    def __init__(self, input_lines, lines):
        """
        :param lines: the strings of each line in the message block
        :type lines: list
        """
        super().__init__(input_lines)
        assert isinstance(lines, list)
        buff = []
        for line in lines:
            buff.append(line.rstrip())
        self._lines = buff

    def __str__(self):
        ret = "MESSAGE:\n"
        for line in self._lines:
            ret += line + "\n"
        return ret

    @property
    def lines(self):
        """
        The lines of input for the message block.

        Each entry is a string of that line in the message block
        """
        return self._lines

    def format_for_mcnp_input(self, mcnp_version):
        ret = []
        line_length = 0
        if mcnp_version[0] == 6.2:
            line_length = 128
        for i, line in enumerate(self.lines):
            if i == 0:
                ret.append("MESSAGE: " + line[0 : line_length - 10])
            else:
                ret.append(line[0 : line_length - 1])
        ret.append("")
        return ret


class Title(MCNP_Input):
    """
    Object to represent the title for an MCNP problem
    """

    def __init__(self, input_lines, title):
        super().__init__(input_lines)
        assert isinstance(title, str)
        self._title = title.rstrip()

    @property
    def title(self):
        "The string of the title set for this problem"
        return self._title

    def __str__(self):
        return f"TITLE: {self._title}"

    def format_for_mcnp_input(self, mcnp_version):
        line_length = 0
        if mcnp_version[0] == 6.2:
            line_length = 128
        return [self.title[0 : line_length - 1]]
