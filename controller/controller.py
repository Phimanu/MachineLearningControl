import json
import random
import socket
from pathlib import Path
from json.decoder import JSONDecodeError
from subprocess import PIPE, Popen
from time import sleep

import pandas as pd
import numpy as np


class MRubisController():

    def __init__(self, host='localhost', port=8080, json_path='path.json', rule_approach='lowest') -> None:

        # Put your command line here (In Eclipse: Run -> Run Configurations... -> Show Command Line)
        with open(json_path, 'r') as f:
            variable_paths = json.load(f)

        self.host=host
        self.port=port

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
        self.socket = None
        self.mrubis_process = None
        self.output_path = Path(__file__).parent.resolve() / 'output'

    def _start_mrubis(self):
        self.mrubis_process = Popen(
            self.launch_args, 
            stdin=PIPE, 
            stdout=PIPE,
            shell=False,
            cwd="../mRUBiS/ML_based_Control"
        )

    def _stop_mrubis(self):
        self.mrubis_process.terminate()

    def _connect_to_java(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sleep(1)
        self.socket.connect((self.host, self.port))
        print('Connected to the Java side.')

    def _get_initial_state(self):
        self.number_of_shops = self._get_from_mrubis('get_number_of_shops').get('number_of_shops')
        print(f'Number of mRUBIS shops: {self.number_of_shops}')
        for _ in range(self.number_of_shops):
            shop_state = self._get_from_mrubis('get_initial_state')
            shop_name = next(iter(shop_state))
            self.mrubis_state[shop_name] = shop_state[shop_name]

    def _update_number_of_issues_in_run(self):
        self.number_of_issues_in_run = self._get_from_mrubis('get_number_of_issues_in_run').get('number_of_issues_in_run')
        print(f'Total number of issues to handle in current run: {self.number_of_issues_in_run}')

    def _get_from_mrubis(self, message):

        self.socket.send(f"{message}\n".encode("utf-8"))
        print(f'Waiting for mRUBIS to answer to message {message}')
        data = self.socket.recv(64000)

        try:
            mrubis_state = json.loads(data.decode("utf-8"))
        except JSONDecodeError:
            print("Could not decode JSON input, received this:")
            print(data)
            mrubis_state = "not available"

        return mrubis_state

    @staticmethod
    def _get_info_from_issue(issue):
        shop_name = next(iter(issue))
        component_name = next(iter(issue[shop_name]))
        component_params = issue.get(shop_name).get(component_name)
        issue_name = component_params.get('failure_name')
        rules = [rule.strip() for rule in component_params['rule_names'].strip('[]').split(',')]
        rule_costs = [float(costs) for costs in component_params['rule_costs'].strip('[]').split(',')]
        return shop_name, component_name, component_params, issue_name, rules, rule_costs

    @staticmethod
    def _pick_rule(component_name, rules, rule_costs, method='lowest'):
        # ReplaceComponent can only be used on Authentication Service
        if component_name != 'Authentication Service':
            rule_costs = [cost for idx, cost in enumerate(rule_costs) if rules[idx] != 'ReplaceComponent']
            rules = [rule for rule in rules if rule != 'ReplaceComponent']

        if method == 'random':
            return random.choice(rules)
        if method == 'lowest':
            return rules[rule_costs.index(min(rule_costs))]
        if method == 'highest':
            return rules[rule_costs.index(max(rule_costs))]

    def _send_rule_to_execute(self, issue, rule):
        shop_name, component_name, _, issue_name, _, _ = self._get_info_from_issue(issue)
        picked_rule_message = {shop_name: {issue_name: {component_name: rule}}}
        print(f"{shop_name}: Handling {issue_name} on {component_name} with {rule}")
        print('Sending selected rule to mRUBIS...')
        self.socket.send((json.dumps(picked_rule_message)  + '\n').encode("utf-8"))
        print("Waiting for mRUBIS to answer with 'rule_received'...")
        data = self.socket.recv(64000)
        if data.decode('utf-8').strip() == 'rule_received':
            print('Rule transmitted successfully.')

    def _send_exit_message(self):
        self.socket.send("exit\n".encode("utf-8"))
        _ = self.socket.recv(64000)

    def _close_socket(self):
        self.socket.close()

    def _append_current_state_to_history(self, fix_status):
        mrubis_df = pd.DataFrame.from_dict({
            (fix_status, shop, component): self.mrubis_state[shop][component] 
                for shop in self.mrubis_state.keys() 
                for component in self.mrubis_state[shop].keys()},
            orient='index')

        self.mrubis_state_history.append(mrubis_df)

    def _write_state_history_to_disk(self, filename='mrubis'):
        mrubis_df = pd.concat(self.mrubis_state_history, keys=np.repeat(np.arange(1, len(self.mrubis_state_history)+1), 2)).reset_index()
        mrubis_df.columns = ['run', 'fix_status', 'shop', 'component'] + list(mrubis_df.columns)[4:]
        self.output_path.mkdir(exist_ok=True)
        mrubis_df.to_csv(self.output_path / f'{filename}.csv', index=False)
        mrubis_df.to_excel(self.output_path / f'{filename}.xls', index=False)

    def _update_current_state(self, incoming_state):
        for shop, shop_components in incoming_state.items():
            for component_type, component_params in shop_components.items():
                if shop not in self.mrubis_state.keys():
                    self.mrubis_state[shop] = {}
                if component_type not in self.mrubis_state[shop].keys():
                    self.mrubis_state[shop][component_type] = {}
                for param, value in component_params.items():
                    self.mrubis_state[shop][component_type][param] = value

    def _get_system_utility(self):
        '''Calculates the utility for the entire system (across shops)'''
        total_utility = 0
        for shop_attributes in self.mrubis_state.values():
            for comp_attributes in shop_attributes.values():
                total_utility += float(comp_attributes['component_utility'])
        return total_utility

    def _write_system_utility_into_state(self):
        system_utility = self._get_system_utility()
        for shop, shop_components in self.mrubis_state.items():
            for component_type, _ in shop_components.items():
                self.mrubis_state[shop][component_type]['sys_utility'] = system_utility

    def _remove_replaced_authentication_service(self):
        for shop, shop_components in self.mrubis_state.copy().items():
            if len([comp for comp in list(shop_components.keys()) if 'Authentication Service' in comp]) > 1:
                for component_type, component_params in shop_components.copy().items():
                    if 'Authentication Service' in component_type and np.isclose(float(component_params['component_utility']), 0):
                        del self.mrubis_state[shop][component_type]

    def run(self, external_start=False, max_runs=100, rule_picking_method='lowest'):

        if not external_start:
            self._start_mrubis()
            if self.mrubis_process.poll() is None:
                print('MRUBIS is running')

        sleep(0.5)

        self._connect_to_java()

        # TODO: explain design decisions in comments

        while self.run_counter < max_runs:
            self.run_counter += 1
            self.mrubis_state = {}

            print(f"Getting state {self.run_counter}/{max_runs}...")

            if self.run_counter == 1:
                self._get_initial_state()

            components_fixed_in_this_run = {}
            number_of_issues_handled_in_this_run = 0
            self.number_of_issues_in_run = 1 # make sure that the loop runs at least once
            while number_of_issues_handled_in_this_run < self.number_of_issues_in_run:

                self._update_number_of_issues_in_run()

                # Get the current issue to handle
                current_issue = self._get_from_mrubis('get_issue')
                self._update_current_state(current_issue)

                # Get available rules, pick rule, send it to mRUBiS
                shop_name, component_name, _, _, rules, rule_costs = self._get_info_from_issue(current_issue)
                picked_rule = self._pick_rule(component_name, rules, rule_costs, method=rule_picking_method)
                self._send_rule_to_execute(current_issue, picked_rule)

                # Remember components that have been fixed in this run
                if components_fixed_in_this_run.get(shop_name) is None:
                    components_fixed_in_this_run[shop_name] = []
                components_fixed_in_this_run[shop_name].append(component_name)
                number_of_issues_handled_in_this_run += 1

            print(f'System utility before taking action: {self._get_system_utility()}')
            self._write_system_utility_into_state()
            self._append_current_state_to_history(fix_status='before')

            print(f'Applied actions to these components in this run: {components_fixed_in_this_run}')
            print("Getting state of affected components after taking action...")
            state_after_action = self._get_from_mrubis(message=json.dumps(components_fixed_in_this_run))
            self._update_current_state(state_after_action)
            self._remove_replaced_authentication_service()

            print(f'System utility after taking action: {self._get_system_utility()}')
            self._write_system_utility_into_state()
            self._append_current_state_to_history(fix_status='after')

        self._send_exit_message()
        self._close_socket()

        if not external_start:
            self._stop_mrubis()

        self._write_state_history_to_disk(filename=f'{max_runs}_runs_{rule_picking_method}')

if __name__ == "__main__":
    controller = MRubisController()
    controller.run(external_start=True, max_runs=100, rule_picking_method='lowest')
