from enum import Enum

class Headers(Enum):
    TRANSACTION_ID = "x-fapi-transaction-id"
    CUSTOMER_IP_ADDR = "x-fapi-customer-ip-address"