import json
import logging
import random
import socket
from pathlib import Path
from json.decoder import JSONDecodeError
from subprocess import PIPE, Popen
from time import sleep

from component_utility_predictor import RidgeUtilityPredictor
from component_dependencies import ComponentDependencyModel

import pandas as pd
from mrubis_controller.failure_propagator.messages import Messages
import numpy as np

logging.basicConfig()
logger = logging.getLogger('controller')
logger.setLevel(logging.INFO)

class FailureProgagator():
    def __init__(self, host='localhost', port=8080, json_path='path.json') -> None:
        '''Create a new instance of the mRubisController class'''

        # Put your command line here (In Eclipse: Run -> Run Configurations... -> Show Command Line)
        with open(json_path, 'r') as f:
            variable_paths = json.load(f)

        self.host = host
        self.port = port

        self.launch_args = [
            variable_paths['java_path'],
            '-DFile.encoding=UTF-8',
            '-classpath',
            variable_paths['dependency_paths'],
            '-XX:+ShowCodeDetailsInExceptionMessages',
            'mRUBiS_Tasks.Task_1',
        ]

        self.run_counter = 0
        self.number_of_shops = 0
        self.number_of_issues_per_shop = {}
        self.current_issue = {}
        self.mrubis_state = {}
        self.mrubis_state_history = []
        self.fix_history = []
        self.current_fixes = None
        self.socket = None
        self.mrubis_process = None
        self.utility_model = RidgeUtilityPredictor()
        self.output_path = Path(__file__).parent.resolve() / 'output'
        self.component_dependency_model = ComponentDependencyModel()

    def connect_to_java(self):
        '''Connect to the socket opened on the java side'''
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sleep(1)
        self.socket.connect((self.host, self.port))
        logger.info('Connected to the Java side.')

    def get_from_mrubis(self, message):
        '''Send a message to mRUBiS and return the response as a dictionary'''
        self.socket.send(f"{message}\n".encode("utf-8"))
        logger.debug(f'Waiting for mRUBIS to answer to message {message}')
        data = self.socket.recv(64000)

        try:
            mrubis_state = json.loads(data.decode("utf-8"))
        except JSONDecodeError:
            logger.error("Could not decode JSON input, received this:")
            logger.error(data)
            mrubis_state = "not available"

        return mrubis_state

    def get_number_of_shops(self):
        return self.get_from_mrubis(Messages.GET_NUMBER_OF_SHOPS).get('number_of_shops')

    def get_initial_state(self):
        shop_state = self.get_from_mrubis(Messages.GET_INITIAL_STATE)

    def send_rule_to_execute(self, shop_name, issue_name, component_name, rule):
        '''Send a rule to apply to an issue to mRUBiS'''

        picked_rule_message = {shop_name: {issue_name: {component_name: rule}}}
        logger.info(
            f"{shop_name}: Handling {issue_name} on {component_name} with {rule}")
        logger.debug('Sending selected rule to mRUBIS...')
        self.socket.send(
            (json.dumps(picked_rule_message) + '\n').encode("utf-8"))
        logger.debug("Waiting for mRUBIS to answer with 'rule_received'...")
        data = self.socket.recv(64000)
        if data.decode('utf-8').strip() == 'rule_received':
            logger.debug('Rule transmitted successfully.')
        # Remember components that have been fixed in this run

    def send_order_in_which_to_apply_fixes(self, order_tuples):
        '''Send the order in which to apply the fixes to mRUBiS'''
        logger.debug('Sending order in which to apply fixes to mRUBIS...')
        order_dict = {idx: {
            'shop': fix_tuple[0],
            'issue': fix_tuple[1],
            'component': fix_tuple[2]
        } for idx, fix_tuple in enumerate(order_tuples)}
        '''
        for issueComponent in order_dict:
            self.socket.send(json.dumps(issueComponent))
            data = self.socket.recv(64000)
        '''
        self.socket.send((json.dumps(order_dict) + '\n').encode("utf-8"))
        logger.debug(
            "Waiting for mRUBIS to answer with 'fix_order_received'...")
        data = self.socket.recv(64000)
        if data.decode('utf-8').strip() == 'fix_order_received':
            logger.debug('Order transmitted successfully.')

    def send_exit_message(self):
        '''Tell mRUBiS to stop its main loop'''
        self.socket.send("exit\n".encode("utf-8"))
        _ = self.socket.recv(64000)

    def close_socket(self):
        '''Close the socket'''
        self.socket.close()