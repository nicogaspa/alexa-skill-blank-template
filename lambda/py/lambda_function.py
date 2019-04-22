# -*- coding: utf-8 -*-
import logging
import os
import gettext
from ask_sdk_core.dispatch_components import AbstractRequestInterceptor, \
    AbstractResponseInterceptor
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_model.ui import SimpleCard

# necessary for local tests
os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
os.environ["ASK_DEFAULT_DEVICE_LOCALE"] = "it-IT"
os.environ["DEBUG"] = 'True'  # Debug variable, set to False once in production to avoid excessive logging

from alexa.utils import convert_speech_to_text
from intent_handlers import \
    LaunchRequestHandler, HelpIntentHandler, ExitIntentHandler, \
    BaseRequestInterceptor, BaseRequestHandler, CatchAllExceptionHandler, FallbackIntentHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DEBUG = os.environ.get("DEBUG", False) == 'True'

sb = SkillBuilder()


class AddCardInterceptor(AbstractResponseInterceptor):
    """ Add a card to every response by translating ssml text to card content """
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None

        _ = handler_input.attributes_manager.request_attributes["_"]  # Translator
        # the attribute is always present but set to None withouth a card
        if getattr(handler_input.response_builder.response, 'card', None) is None:
            # Card was not set hard-coded in response
            try:
                response.card = SimpleCard(title=convert_speech_to_text(_("SKILL_NAME")),
                                           content=convert_speech_to_text(response.output_speech.ssml))
            except AttributeError:
                pass
        else:
            # Card was set hard-coded in response, converting ssml to clean text anyway
            try:
                response.card = SimpleCard(title=convert_speech_to_text(response.card.title),
                                           content=convert_speech_to_text(response.card.content))
            except AttributeError:
                pass


# Request and Response loggers
class RequestLogger(AbstractRequestInterceptor):
    """ Log the alexa requests """
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.info("ALEXA REQUEST: {}".format(handler_input.request_envelope).replace('\n', '\r'))


class ResponseLogger(AbstractResponseInterceptor):
    """ Log the alexa responses """
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.info("ALEXA RESPONSE: {}".format(response).replace('\n', '\r'))


# localizations support: https://github.com/alexa/skill-sample-python-city-guide/blob/master/instructions
# /localization.md
class LocalizationInterceptor(AbstractRequestInterceptor):
    """ Add function to request attributes, that can load locale specific data."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        locale = handler_input.request_envelope.request.locale
        if DEBUG:
            logger.info("LOCALE = {}".format(locale))
        i18n = gettext.translation('data', localedir='locales', languages=[locale], fallback=True)
        handler_input.attributes_manager.request_attributes["_"] = i18n.gettext


# Add locale interceptor to the skill
sb.add_global_request_interceptor(LocalizationInterceptor())

# Register built-in handlers
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(ExitIntentHandler())
sb.add_request_handler(FallbackIntentHandler())

# Register intent handlers
# TODO

# Register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# Add card interceptor to the skill
sb.add_global_response_interceptor(AddCardInterceptor())

# Add log interceptors to the skill
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())


# Handler name that is used on AWS lambda
lambda_handler = sb.lambda_handler()
