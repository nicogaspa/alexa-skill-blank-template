# -*- coding: utf-8 -*-
import logging
import six
import os
import boto3
from ask_sdk_dynamodb.adapter import DynamoDbAdapter
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractRequestInterceptor
from abc import abstractmethod
from ask_sdk_model.slu.entityresolution import StatusCode
from ask_sdk_core.exceptions import PersistenceException
from ask_sdk_dynamodb.adapter import user_id_partition_keygen
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DEBUG = os.environ.get("DEBUG", False) == 'True'

# Here we can create a custom base handler that the others will inherit from


class BaseRequestHandler(AbstractRequestHandler):
    """
    This is the Base request handler the other handlers will inherit from.
    It contains basic functions such as the saving and access data from and to DynamoDB,
    using the DynamoDB persistence adaptor.
    This data can be both user data and analytics data
    """
    SLOTS = []  # Filled in every handler

    def __init__(self):
        super().__init__()
        self.slot_values = {}
        # Initializing an empty dict, to read slots later
        for slot_key in self.SLOTS:
            self.slot_values[slot_key] = {
                "synonym": None,
                "resolved": None,
                "is_validated": False,
            }
        self.dynamodb = boto3.resource('dynamodb',
                                       region_name="eu-west-1",
                                       aws_access_key_id="",
                                       aws_secret_access_key="")  # TODO add here AWS keys
        # Default partition keygen uses user_id in request_envelope as ID
        table_name = None  # TODO user attributes table name
        self.dynamo_client = DynamoDbAdapter(table_name=table_name,
                                             partition_key_name="user_id",
                                             partition_keygen=user_id_partition_keygen,  # default
                                             create_table=False,  # default
                                             dynamodb_resource=self.dynamodb)

    @abstractmethod
    def can_handle(self, handler_input):
        """ Base method, not implemented here """
        raise NotImplementedError

    def handle(self, handler_input):
        """ Super handler, called by every intent that wants to save request data """
        BaseRequestInterceptor().process(handler_input=handler_input, request_handler=self)

    def get_attributes(self, handler_input):
        """ Gets user attributes from DynamoDB """
        user_attr = self.dynamo_client.get_attributes(request_envelope=handler_input.request_envelope)
        if len(user_attr) == 0:
            # If the user didn't exist, we create a default set of attributes with the key 'first_use' to signal it
            default_attr = self.set_default_attributes(handler_input)
            default_attr['first_use'] = True
            return default_attr
        return user_attr

    def set_default_attributes(self, handler_input):
        """ Sets default user attributes to DynamoDB """
        attr = {
            'custom_attr': 'TODO',
        }
        self.dynamo_client.save_attributes(request_envelope=handler_input.request_envelope, attributes=attr)
        return attr

    def set_attributes(self, handler_input, attr):
        """ Overwrite user attributes to DynamoDB """
        user_attr = self.dynamo_client.get_attributes(request_envelope=handler_input.request_envelope)
        for changed_attr in attr:
            user_attr[changed_attr] = attr[changed_attr]
        self.dynamo_client.save_attributes(request_envelope=handler_input.request_envelope,
                                           attributes=user_attr)

    # --------- Other methods

    def get_slot_values(self, filled_slots):
        """ Return slot values with additional info, to understand if the slots were filled """
        if DEBUG:
            logger.info("Filled slots: {}".format(filled_slots).replace("\n", "\r"))

        if filled_slots is None:
            return {}

        for key, slot_item in six.iteritems(filled_slots):
            name = slot_item.name
            try:
                status_code = slot_item.resolutions.resolutions_per_authority[0].status.code

                if status_code == StatusCode.ER_SUCCESS_MATCH:
                    self.slot_values[name] = {
                        "synonym": slot_item.value,
                        "resolved": slot_item.resolutions.resolutions_per_authority[0].values[0].value.__dict__,
                        "is_validated": True,
                    }
                elif status_code == StatusCode.ER_SUCCESS_NO_MATCH:
                    self.slot_values[name] = {
                        "synonym": slot_item.value,
                        "resolved": slot_item.value,
                        "is_validated": False,
                    }
                else:
                    pass
            except (AttributeError, ValueError, KeyError, IndexError, TypeError) as e:
                # for BUILT-IN intents, there are no resolutions, but the value is specified
                if slot_item.value is not None and slot_item.value != 'NONE':
                    self.slot_values[name] = {
                        "synonym": slot_item.value,
                        "resolved": slot_item.value,
                        "is_validated": True,
                    }
                else:
                    if DEBUG:
                        logger.info("SLOT {} UNRESOLVED".format(name))
                    self.slot_values[name] = {
                        "synonym": slot_item.value,
                        "resolved": slot_item.value,
                        "is_validated": False,
                    }
        return self.slot_values


def request_id_partition_keygen(request_envelope):
    """ Retrieve request id from request envelope, to use as partition key. """
    try:
        request_id = request_envelope.request.request_id
        return request_id
    except AttributeError:
        raise PersistenceException("Couldn't retrieve request id from "
                                   "request envelope, for partition key use")


class BaseRequestInterceptor(AbstractRequestInterceptor):
    def __init__(self):
        super().__init__()
        table_name = ""  # TODO add request analysis dynamodb table name
        self.dynamodb = boto3.resource('dynamodb',
                                       region_name="eu-west-1",
                                       aws_access_key_id="",
                                       aws_secret_access_key="")  # TODO add aws keys
        self.dynamo_client = DynamoDbAdapter(
            table_name,
            partition_key_name="request_id",
            partition_keygen=request_id_partition_keygen,
            create_table=False,
            dynamodb_resource=self.dynamodb
        )

    def save_request(self, handler_input, payload):
        self.dynamo_client.save_attributes(
            request_envelope=handler_input.request_envelope,
            attributes=payload)
        return True

    def process(self, handler_input, request_handler=None):
        try:
            if hasattr(handler_input.request_envelope.request, 'intent'):
                slots = request_handler.get_slot_values(handler_input.request_envelope.request.intent.slots)

                analytics_payload = {
                    "request_id": handler_input.request_envelope.request.request_id,
                    "user_id": handler_input.request_envelope.session.user.user_id,
                    "device_id": handler_input.request_envelope.context.system.device.device_id,
                    "datetime": str(time.time()),
                    "display": handler_input.request_envelope.context.display,
                    "locale": handler_input.request_envelope.request.locale,
                    'request': handler_input.request_envelope.request.object_type,
                    'intent': handler_input.request_envelope.request.intent.name,
                }

                for slot in slots:
                    analytics_resolved_key = "slot_{}_resolved_id".format(slot)
                    analytics_synonym_key = "slot_{}_synonym".format(slot)
                    analytics_is_valid_key = "slot_{}_is_validated".format(slot)

                    analytics_payload.update({
                        analytics_resolved_key: slots[slot]["resolved"]["id"] if isinstance(slots[slot]["resolved"], dict) and 'id' in slots[slot]["resolved"] else slots[slot]["resolved"],
                        analytics_synonym_key: slots[slot]["synonym"],
                        analytics_is_valid_key: slots[slot]["is_validated"]
                    })

                self.save_request(handler_input, analytics_payload)
        except Exception as e:
            logger.error(str(e).replace("\n", "\r"))
            if DEBUG:
                raise e
            else:
                pass  # In production we can skip saving analytics if it fails
