from typing import Annotated

from fastapi import Path
from pydantic import StringConstraints

from app.core.constants import UUID_PATTERN

UuidStr = Annotated[str, StringConstraints(pattern=UUID_PATTERN)]
PathUuid = Annotated[str, Path(pattern=UUID_PATTERN)]
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Za-z]{3}$", to_upper=True)]
