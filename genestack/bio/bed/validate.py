# -*- coding: utf-8 -*-

"""
Validators for fields.
Single validator structure:
    Validators for single fields.
    Args:
        txt text for validation
        name name to display
    Returns:
        Always None
    Raises:
        Exception if fail.
"""

import re
from genestack import GenestackException


text_regexp = re.compile('[-\w]*')


def no_validate(text, name):
    """
    Not validate
    """
    pass


def text_validator(txt, name):
    if not text_regexp.match(txt):
        raise GenestackException('Field %s: "%s" is not allowed' % (name, txt))


def number_validator(txt, name):
    try:
        int(txt)
    except ValueError:
        raise GenestackException('Field %s: "%s" is not number' % (name, txt))


def float_validator(txt, name):
    try:
        float(txt)
    except ValueError:
        raise GenestackException('Field %s: "%s" is not float number' % (name, txt))


def strand_validator(txt, name):
    if txt not in '+-':
        raise GenestackException('Field %s: "%s" is not in [ + - ]' % (name, txt))


def rgb_validator(txt, name):
    if txt == '0':  # hack to support blank color value.
        return

    items = txt.split(',')
    if len(items) != 3:
        raise GenestackException('Field %s: "%s" is not valid color' % (name, txt))
    for item in items:
        try:
            num = int(item)
        except ValueError:
            raise GenestackException('Field %s: "%s" is not valid color' % (name, txt))
        if num > 255:
            raise GenestackException('Field %s: "%s" is not valid color' % (name, txt))


def block_validator(txt, name):
    try:
        map(int, txt.split(','))
    except ValueError:
        raise GenestackException('Field %s: "%s" is not valid block' % (name, txt))
