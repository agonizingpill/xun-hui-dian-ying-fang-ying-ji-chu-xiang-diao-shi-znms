from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Code = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r'^[A-Z0-9][A-Z0-9-]{2,23}$')]
Card = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=36)]
Ratio = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Outlet(Input):
    circuit: Code
    voltage: Annotated[float, Field(ge=150, le=290, allow_inf_nan=False)]
    earth: bool
    breakers: Annotated[int, Field(ge=0, le=100)]


class CardReading(Input):
    card: Card
    source_measurement: Code | None = None
    edge_loss: Ratio
    color_error: Ratio
    flicker_index: Ratio
    frame_var: Ratio


class SaveCard(Input):
    code: Code
    token: Annotated[str, StringConstraints(pattern=r'^[0-9a-f]{32}$')]


class Loan(Input):
    code: Code
    booth_code: Code
    lens_code: Code
    measurement_code: Code


class LensReturn(Input):
    case_tag: Code


class Clearance(Input):
    measurement_code: Code
