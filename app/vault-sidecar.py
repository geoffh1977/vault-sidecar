#!/usr/bin/env python3

# Needed For Main
import os
import logging
import sys
import shelve
import time
from vault import Vault
from encrypt import AESCipher, generate_random_string

# Configure Default Variables
VAULT_ADDR = os.getenv('VAULT_ADDR', 'http://127.0.0.1:8200')
VAULT_SHARES = os.getenv('VAULT_SHARES', '5')
VAULT_THRESHOLD = os.getenv('VAULT_THRESHOLD', '3')
MASTER_PASSWORD = os.getenv('MASTER_PASSWORD')
SECRETS_FILE = os.getenv('SECRETS_FILE', '/output/secrets.enc')

# Configure Logging
logging.basicConfig(level=os.getenv('LOGLEVEL','DEBUG'))

# Other Global Variables
secretData = {}

# Connect To Vault And Determine State
vault = Vault(VAULT_ADDR)
if not vault.is_ready():

  # Check If Vault Is Initialized
  if not vault.is_initialized():
    if vault.initialize(shares=int(VAULT_SHARES), threshold=int(VAULT_THRESHOLD)):
      if MASTER_PASSWORD is None:
        MASTER_PASSWORD = generate_random_string(32)
        logging.info('')
        logging.info('No MASTER_PASSWORD Has Been Provided. Password Has Been Generated.')
        logging.info('MASTER_PASSWORD: %s', MASTER_PASSWORD)
        logging.info('This Will Be Required To Start This Vault Instance.')
      
      logging.info('Encrypting Data And Writing Out Vault Details')
      aes = AESCipher(MASTER_PASSWORD)
      secretData['masterPassword'] = aes.encrypt(MASTER_PASSWORD)
      secretData['rootToken'] = aes.encrypt(vault.rootToken)
      secretData['unsealKey'] = {}
      for num, key in enumerate(vault.keys, start=1):
        secretData['unsealKey'][num] = aes.encrypt(key)

      outputFile = shelve.open(SECRETS_FILE)
      outputFile['secretData'] = secretData
      outputFile.close()
    else:
      logging.error('An Error Has Occured During Initialization! Exiting...')
  
  # Check Master Password Is Set
  logging.info('')
  logging.info('Attempting To Unseal Vault')
  if MASTER_PASSWORD is None:
    logging.error('MASTER_PASSWORD Variable Is Not Set. Password Is Needed to Decrypt Vault Details. Exiting...')
  else:

    aes = AESCipher(MASTER_PASSWORD)
    if os.path.exists(SECRETS_FILE):

      # Load Secret Data From File
      inputFile = shelve.open(SECRETS_FILE)
      secretData = inputFile['secretData']
      inputFile.close()
      if MASTER_PASSWORD == aes.decrypt(secretData['masterPassword']):
        logging.info('MASTER_PASSWORD Has Been Confirmed.')
        unsealKeys=[]
        for key in secretData['unsealKey']:
          unsealKeys.append(aes.decrypt(secretData['unsealKey'][key]))

        # Unseal Vault
        vault.unseal(unsealKeys)
        if vault.is_sealed():
          logging.error('Vault Cannot Be Unsealed. Exiting...')
        
      else:
        logging.error('MASTER_PASSWORD Is Incorrect. Exiting...')

    else:
      logging.error('SECRETS_FILE Is Set Incorrectly Or File Does Not Exist. Exiting...')

else:
  logging.info('Vault Is Already Initialized And Unsealed.')

# Final Check Of Availability
if vault.is_ready():
  logging.info('Vault Is Ready For Operations.')
else:
  logging.error('Vault Is Not Unsealed. Something Has Gone Wrong!')
  sys.exit(1)

# Fall Into Infinate Loop
while True:
  if vault.is_sealed():
    logging.warn('Vault Has Been Sealed. Unsealing...')
    vault.unseal(unsealKeys)
    if vault.is_sealed:
      logging.error('Failed To Unseal Vault. Exiting...')
      sys.exit(1)
    else:
      logging.info('Vault Successfully Unsealed. Resuming Operations.')
  
  time.sleep(30)
