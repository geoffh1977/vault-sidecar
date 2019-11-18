#!/usr/bin/env python3

# Needed For Main
from vault import Vault
import logging
import os

# Configure Default Variables
VAULT_ADDR = os.getenv('VAULT_ADDR', 'http://127.0.0.1:8200')

# Configure Logging
logging.basicConfig(level=os.getenv('LOGLEVEL','DEBUG'))

# Connect To Vault
vault = Vault(VAULT_ADDR)
vault.setup()
