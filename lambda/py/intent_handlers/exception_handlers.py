# -*- coding: utf-8 -*-
import os
import logging
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DEBUG = os.environ.get("DEBUG", False) == 'True'


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """
    Catch all exceptions, logs and respond with custom message
    """

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        if DEBUG:
            logger.info("EVERY EXCEPTIONS HANDLER")
        logger.error(str(exception).replace("\n", "\r"), exc_info=True)

        _ = handler_input.attributes_manager.request_attributes["_"]  # Translator

        speech_text = _("ERROR")
        card = SimpleCard(title=_("ERROR_CARD_TITLE"),
                          content=_("ERROR"))
        handler_input.response_builder.speak(speech_text).set_card(card)

        return handler_input.response_builder.response
