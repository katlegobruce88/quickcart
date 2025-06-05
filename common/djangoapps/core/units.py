"""
Measurement units definitions for the EMS application.

This module provides standardized
measurement units for various physical quantities
such as distance, area, volume, and weight.
Each class defines constants for specific
units along with human-readable labels for UI display.

Example:
    >>> from ems.djangoapps.core.units import DistanceUnits
    >>> DistanceUnits.M
    'm'
    >>> dict(DistanceUnits.CHOICES)
    {'mm': 'Millimeter', 'cm': 'Centimeter', ...}
"""


class DistanceUnits:
    """
    Distance measurement units.

    This class defines standard units for measuring distance/length.

    Attributes:
        MM (str): Millimeter unit.
        CM (str): Centimeter unit.
        DM (str): Decimeter unit.
        M (str): Meter unit.
        KM (str): Kilometer unit.
        FT (str): Feet unit.
        YD (str): Yard unit.
        INCH (str): Inch unit.
        CHOICES (list): List of tuples containing
        (unit_value, display_name) pairs
            for use in Django form fields and model choices.
    """
    MM = "mm"
    CM = "cm"
    DM = "dm"
    M = "m"
    KM = "km"
    FT = "ft"
    YD = "yd"
    INCH = "inch"

    CHOICES = [
        (MM, "Millimeter"),
        (CM, "Centimeter"),
        (DM, "Decimeter"),
        (M, "Meter"),
        (KM, "Kilometers"),
        (FT, "Feet"),
        (YD, "Yard"),
        (INCH, "Inch"),
    ]


class AreaUnits:
    """
    Area measurement units.

    This class defines standard units for measuring area.

    Attributes:
        SQ_MM (str): Square millimeter unit.
        SQ_CM (str): Square centimeter unit.
        SQ_DM (str): Square decimeter unit.
        SQ_M (str): Square meter unit.
        SQ_KM (str): Square kilometer unit.
        SQ_FT (str): Square feet unit.
        SQ_YD (str): Square yard unit.
        SQ_INCH (str): Square inch unit.
        CHOICES (list): List of tuples containing
        (unit_value, display_name) pairs
            for use in Django form fields and model choices.
    """
    SQ_MM = "sq_mm"
    SQ_CM = "sq_cm"
    SQ_DM = "sq_dm"
    SQ_M = "sq_m"
    SQ_KM = "sq_km"
    SQ_FT = "sq_ft"
    SQ_YD = "sq_yd"
    SQ_INCH = "sq_inch"

    CHOICES = [
        (SQ_MM, "Square millimeter"),
        (SQ_CM, "Square centimeters"),
        (SQ_DM, "Square decimeter"),
        (SQ_M, "Square meters"),
        (SQ_KM, "Square kilometers"),
        (SQ_FT, "Square feet"),
        (SQ_YD, "Square yards"),
        (SQ_INCH, "Square inches"),
    ]


class VolumeUnits:
    """
    Volume measurement units.

    This class defines standard units for measuring volume.

    Attributes:
        CUBIC_MILLIMETER (str): Cubic millimeter unit.
        CUBIC_CENTIMETER (str): Cubic centimeter unit.
        CUBIC_DECIMETER (str): Cubic decimeter unit.
        CUBIC_METER (str): Cubic meter unit.
        LITER (str): Liter unit.
        CUBIC_FOOT (str): Cubic foot unit.
        CUBIC_INCH (str): Cubic inch unit.
        CUBIC_YARD (str): Cubic yard unit.
        QT (str): Quart unit.
        PINT (str): Pint unit.
        FL_OZ (str): Fluid ounce unit.
        ACRE_IN (str): Acre inch unit.
        ACRE_FT (str): Acre feet unit.
        CHOICES (list): List of tuples containing
        (unit_value, display_name) pairs
            for use in Django form fields and model choices.
    """
    CUBIC_MILLIMETER = "cubic_millimeter"
    CUBIC_CENTIMETER = "cubic_centimeter"
    CUBIC_DECIMETER = "cubic_decimeter"
    CUBIC_METER = "cubic_meter"
    LITER = "liter"
    CUBIC_FOOT = "cubic_foot"
    CUBIC_INCH = "cubic_inch"
    CUBIC_YARD = "cubic_yard"
    QT = "qt"
    PINT = "pint"
    FL_OZ = "fl_oz"
    ACRE_IN = "acre_in"
    ACRE_FT = "acre_ft"

    CHOICES = [
        (CUBIC_MILLIMETER, "Cubic millimeter"),
        (CUBIC_CENTIMETER, "Cubic centimeter"),
        (CUBIC_DECIMETER, "Cubic decimeter"),
        (CUBIC_METER, "Cubic meter"),
        (LITER, "Liter"),
        (CUBIC_FOOT, "Cubic foot"),
        (CUBIC_INCH, "Cubic inch"),
        (CUBIC_YARD, "Cubic yard"),
        (QT, "Quart"),
        (PINT, "Pint"),
        (FL_OZ, "Fluid ounce"),
        (ACRE_IN, "Acre inch"),
        (ACRE_FT, "Acre feet"),
    ]


class WeightUnits:
    """
    Weight measurement units.

    This class defines standard units for measuring weight/mass.

    Attributes:
        G (str): Gram unit.
        LB (str): Pound unit.
        OZ (str): Ounce unit.
        KG (str): Kilogram unit.
        TONNE (str): Tonne (metric ton) unit.
        CHOICES (list): List of tuples containing
        (unit_value, display_name) pairs
            for use in Django form fields and model choices.
    """
    G = "g"
    LB = "lb"
    OZ = "oz"
    KG = "kg"
    TONNE = "tonne"

    CHOICES = [
        (G, "Gram"),
        (LB, "Pound"),
        (OZ, "Ounce"),
        (KG, "kg"),
        (TONNE, "Tonne"),
    ]


def prepare_all_units_dict():
    """
    Prepare a consolidated dictionary of all measurement units.

    This function collects all unit choices from the various unit classes
    and creates a unified dictionary. It also adds a CHOICES attribute that
    contains all available units for selection in forms.

    Returns:
        dict: A dictionary containing all measurement units with uppercase keys
            mapped to their string values, plus a CHOICES key containing a list
            of (value, value) tuples for all units.

    Example:
        >>> result = prepare_all_units_dict()
        >>> 'MM' in result
        True
        >>> 'CHOICES' in result
        True
    """
    measurement_dict = {
        unit.upper(): unit
        for unit_choices in [
            DistanceUnits.CHOICES,
            AreaUnits.CHOICES,
            VolumeUnits.CHOICES,
            WeightUnits.CHOICES,
        ]
        for unit, _ in unit_choices
    }
    choices = [(v, v) for v in measurement_dict.values()]
    return dict(measurement_dict, CHOICES=choices)


# Create a dynamic class that contains all measurement units
MeasurementUnits = type(
    "MeasurementUnits",
    (object,),
    prepare_all_units_dict()
)
