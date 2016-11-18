#!/usr/bin/env python
# -*- coding: utf-8 -*-

client_started = False
wsclients = []

# @staticmethod
def send_to_allws(message, binary=False):
    for client in wsclients:
        if client.legal == True:
            client.write_message(message, binary)

