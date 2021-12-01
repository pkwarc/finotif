import logging
import coreapi
from rest_framework.schemas.coreapi import (
    AutoSchema,
    coreschema
)
from .models import (
    TickerProperty,
    NotificationType
)

_logger = logging.getLogger(__name__)


class AppSchema(AutoSchema):

    def get_manual_fields(self, path, method):
        custom_fields = []
        property_choices = coreapi.Field(
            name='property',
            required=True,
            location='form',
            schema=coreschema.Enum(
                enum=[label for _, label in TickerProperty.choices],
                title='Property',
                description='The property to observe e.g. price.'
            )
        )
        type_choices = coreapi.Field(
            name='type',
            required=True,
            location='form',
            schema=coreschema.Enum(
                enum=[label for _, label in NotificationType.choices],
                title='Type',
                description='The type of message to send.'
            )
        )
        custom_fields.append(property_choices)
        custom_fields.append(type_choices)
        return self._manual_fields + custom_fields
