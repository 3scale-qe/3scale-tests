"testsuite helpers"

import secrets


def randomize(name):
    "To avoid conflicts returns modified name with random sufffix"
    return "%s-%s" % (name, secrets.token_urlsafe(8).lower())
