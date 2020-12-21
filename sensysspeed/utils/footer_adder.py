# -*- coding: utf-8 -*-

# This work is licensed under the MIT License.
# To view a copy of this license, visit https://opensource.org/licenses/MIT

# Written by Taher Abbasi
# Email: abbasi.taher@gmail.com

import arabic_reshaper
import cv2 
import ..core.execptions
import numpy as np

from bidi.algorithm import get_display
from PIL import ImageFont, ImageDraw, Image
from types import SimpleNamespace
from typing import Tuple

SIDES = SimpleNamespace(TOP = 'TOP',
                        BOTTOM = 'BOTTOM',
                        LEFT = 'LEFT',
                        RIGHT = 'RIGHT')

class TextAdder():
    """This is used to add footer or header to cv images.
    A class for adding persian to as a header or footer for images.
    """

    def __init__(self, font_path: str, font_size: int = 16) -> None:
        """This is the TextAdder constructor.
        :font_path: the path of font file.
        :font_size: size of the font.
        """
        self.font = ImageFont.truetype(font_path, font_size)

    def add_text(self, image, text, position):
        """adds footer or header to the image
        :image: a cv image
        :text: it will be added to the image
        :position: position of the text on the image
        """
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text) 
        pil_image = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_image)
        draw.text(position, bidi_text, font = self.font)
        text_image = np.array(pil_image)
        return text_image
    
    def add_margin(self, image, margin_size: int, margine_side: str,
                   margin_color: Tuple(int, int, int)):
        """This module adds a colored margin to the image.
        :image: a cv image
        :mrgin_size: If the side is right or left size is the width. If the
         margine_side is top or bottom size is the height.
        :margine_side: it determines whether the margin is added to right,
        left, top, or bottom.
        :color: It determines background color od the margin
        """
        height, width, channels = image.shape
        if margine_side in (SIDES.TOP, SIDES.BOTTOM):
            height = margin_size
            axis = 0
        elif margine_side in (SIDES.RIGHT, SIDES.LEFT):
            width = margin_size
            axis = 1
        else:
            raise execptions.WrongSide('Side is wrong')
        
        blank_image = np.zeros((height, width, channels), np.uint8)
        if margine_side in (SIDES.TOP, SIDES.LEFT):
            first_image = blank_image
            second_image = image
        elif margine_side in (SIDES.BOTTOM, SIDES.LEFT):
            first_image = image
            second_image = blank_image
        else:
            raise execptions.WrongSide('Side is wrong')

        return np.concatenate((first_image, second_image), axis=axis)
