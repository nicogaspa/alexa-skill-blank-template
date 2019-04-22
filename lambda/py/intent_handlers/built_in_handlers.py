# -*- coding: utf-8 -*-
import os
import logging
from ask_sdk_model.ui import LinkAccountCard, SimpleCard
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from . import BaseRequestHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DEBUG = os.environ.get("DEBUG", False) == 'True'


class LaunchRequestHandler(BaseRequestHandler):
    """ Handler for Skill Launch """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        if DEBUG:
            logger.info("REQUEST CALLED - LaunchRequest")
        super().handle(handler_input)
        _ = handler_input.attributes_manager.request_attributes["_"]  # Translator
        
        # ---------- Reading from Dynamo user data
        user_attr = self.dynamo_client.get_attributes(request_envelope=handler_input.request_envelope)

        if 'first_use' in user_attr:    # User not saved
            if DEBUG:
                logger.info("User not present in DynamoDB")
            speech_text = _("WELCOME")
        else:                           # User saved
            if DEBUG:
                logger.info("User already present in DynamoDB")
            speech_text = _("WELCOME_BACK")

        handler_input.response_builder.speak(speech_text).ask(speech_text)
        return handler_input.response_builder.response


class HelpIntentHandler(BaseRequestHandler):
    """ Handler for help intent """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("IntentRequest")(handler_input) and \
               (is_intent_name("AMAZON.HelpIntent")(handler_input) or
                is_intent_name("HelpIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        if DEBUG:
            logger.info("INTENT CALLED: HelpIntent")
        super().handle(handler_input)
        _ = handler_input.attributes_manager.request_attributes["_"]  # Translator

        speech_text = _("HELP")
        handler_input.response_builder.speak(speech_text).ask(speech_text)
        return handler_input.response_builder.response


class ExitIntentHandler(BaseRequestHandler):
    """Single Handler for Cancel, Stop and Pause intents."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input) or \
               (is_request_type("IntentRequest")(handler_input) and
                (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                 is_intent_name("AMAZON.StopIntent")(handler_input) or
                 is_intent_name("AMAZON.PauseIntent")(handler_input) or
                 is_intent_name("CancelIntent")(handler_input) or
                 is_intent_name("StopIntent")(handler_input) or
                 is_intent_name("PauseIntent")(handler_input)))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        if DEBUG:
            logger.info("INTENT CALLED: ExitIntent")
            if hasattr(handler_input.request_envelope.request, "reason"):
                logger.info("REASON: {}".format(handler_input.request_envelope.request.reason))
            else:
                logger.info("NO REASON SPECIFIED")
        super().handle(handler_input)
        _ = handler_input.attributes_manager.request_attributes["_"]  # Translator

        speech_text = _("STOP")
        handler_input.response_builder.speak(speech_text)
        return handler_input.response_builder.response


class FallbackIntentHandler(BaseRequestHandler):
    """ Handler for fallback intent, requests to this skill out of scope"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("IntentRequest")(handler_input) and \
                is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        if DEBUG:
            logger.info("INTENT CALLED: FallbackIntent")
        super().handle(handler_input)
        _ = handler_input.attributes_manager.request_attributes["_"]  # Translator

        speech_text = _("FALLBACK")
        handler_input.response_builder.speak(speech_text)
        return handler_input.response_builder.response
