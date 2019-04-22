# -*- coding: utf-8 -*-
import logging
from html.parser import HTMLParser

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# This file should collect every util function used throughout the skill project


class SSMLStripper(HTMLParser):
    """ ----------- Convert SSML to Card text -----------
    This is for automatic conversion of ssml to text content on simple card
    You can create your own simple cards for each response, if this is not
    what you want to use.
    """

    def error(self, message):
        raise NotImplementedError

    def __init__(self):
        super().__init__()
        self.reset()
        self.full_str_list = []
        self.strict = False
        self.convert_charrefs = True

    def handle_data(self, d):
        self.full_str_list.append(d)

    def get_data(self):
        return ''.join(self.full_str_list)


def convert_speech_to_text(ssml_speech):
    """convert ssml speech to text, by removing html tags."""
    s = SSMLStripper()
    s.feed(ssml_speech)
    return s.get_data()
