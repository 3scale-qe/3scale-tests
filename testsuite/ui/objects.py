"""File contains objects that store various information for UI testing"""
from typing import NamedTuple


class BillingAddress(NamedTuple):
    """Billing address info"""

    name: str
    address: str
    city: str
    country: str
    state: str
    phone: str
    zip: str


class CreditCard(NamedTuple):
    """Credit card details"""

    number: str
    cvc: int
    exp_month: int
    exp_year: int
