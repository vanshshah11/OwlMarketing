#!/usr/bin/env python3
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def load_config(config_file='config.json'):
    config_path = os.path.join(os.path.dirname(__file__), config_file)
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logging.info("Configuration loaded from %s", config_file)
        return config
    except Exception as e:
        logging.error("Failed to load configuration: %s", e)
        return None

def load_accounts(accounts_file='accounts.json'):
    accounts_path = os.path.join(os.path.dirname(__file__), accounts_file)
    try:
        with open(accounts_path, 'r') as f:
            accounts = json.load(f)
        logging.info("Accounts loaded from %s", accounts_file)
        return accounts
    except Exception as e:
        logging.error("Failed to load accounts: %s", e)
        return None

if __name__ == "__main__":
    config = load_config()
    accounts = load_accounts()
    logging.info("Config: %s", config)
    logging.info("Accounts: %s", accounts)
