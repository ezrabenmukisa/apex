from decimal import Decimal
from typing import Annotated
from pydantic import PlainSerializer

# Decimals are sent to Flutter as JSON numbers instead of strings ("5000.00")
Money = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]
