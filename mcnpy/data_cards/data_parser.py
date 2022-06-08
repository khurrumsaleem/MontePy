from mcnpy.data_cards import data_card, material, thermal_scattering
from mcnpy.data_cards import transform
import re

PREFIX_MATCHES = {
    "m": material.Material,
    "mt": thermal_scattering.ThermalScatteringLaw,
    "tr": transform.Transform,
}


def parse_data(input_card, comment=None):
    """
    Parses the data card as the appropriate object if it is supported.

    :param input_card: the Card object for this Data card
    :type input_card: Card
    :param comment: the Comment that may proceed this.
    :type comment: Comment
    :return: the parsed DataCard object
    :rtype: DataCard
    """

    base_card = data_card.DataCard(input_card, comment)
    prefix, number = base_card.__split_name__()
    prefix = prefix.lower()

    for match, data_class in PREFIX_MATCHES.items():
        if prefix == match:
            return data_class(input_card, comment)
    return base_card
