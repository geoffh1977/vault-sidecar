#!/usr/bin/env python3

# Needed For Main
import os
import sys
import logging
import time
import socket
import hvac

class Vault:
  shares = 5
  threshold = 3

  def __init__(self, addr=None, keys=None):
    if addr:
      self.connect(addr)
    if keys:
      self.unseal(keys)

  def wait_for_port(self,port, host='127.0.0.1', timeout=5.0):
    logging.info('Checking If Vault Service Is Available...')
    start_time = time.perf_counter()
    while True:
      try:
        with socket.create_connection((host, port), timeout=timeout):
          break
      except OSError as ex:
        time.sleep(0.01)
        if time.perf_counter() - start_time >= timeout:
          raise TimeoutError('Waited too long for the port {} on host {} to start accepting connections.'.format(port, host)) from ex
    logging.info('Vault Service Found.')

  def connect(self, addr=None):
    urlSplit = addr.replace('/','').split(':')
    self.protocol = urlSplit[0]
    self.host = urlSplit[1]
    if len(urlSplit) > 1:
      self.port = urlSplit[2]
    else:
      self.port = '8200'
    os.environ['no_proxy'] = self.host

    self.wait_for_port(host=self.host, port=self.port)

    logging.info('Connecting To Vault Client...')
    self.client = hvac.Client(url=addr)
    logging.info('Connected Successfully!')
    
  def initialize(self, shares=5, threshold=3):
    if self.client.sys.is_initialized():
      logging.info('Vault Has Already Been Initialized.')
    else:
      logging.info('Vault Is Not Initialized. Initializing Now...')
      result = self.client.sys.initialize(shares, threshold)
      self.rootToken = result['root_token']
      self.keys = result['keys']
      logging.info('Vault Has Been Successfully Initialized.')
      logging.info('ROOT TOKEN: %s', self.rootToken)
      for num, key in enumerate(self.keys, start=1):
        logging.info('UNSEAL KEY %s: %s', num, key)
      logging.info('')
      logging.info('WARNING: LOOSING THESE DETAILS WILL RESULT IN LOSS OF ACCESS TO SECURE DATA!')
      return True

  def unseal(self, keys=None):
    if self.client.sys.is_sealed():
      if keys:
        logging.info('Vault Is Currently Sealed. Unsealing Vault...')
        self.client.sys.submit_unseal_keys(keys)
        if self.client.sys.is_sealed():
          logging.error('The Vault Is Still Sealed. An Error Occured During Unsealing Process!')
          return False
        else:
          logging.info('Vault Has Been Successfully Unsealed.')
      else:
        logging.error('Keys Have Not Been Supplied To Unseal Vault!')
        return False
    else:
      logging.info('Vault Is Already Unsealed.')
    return True

  def setup(self):
    if not self.initialize():
      return False
    if not self.unseal(self.keys):
      return False
    return True