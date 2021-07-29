import json
import logging
import random
import socket
from pathlib import Path
from json.decoder import JSONDecodeError
from subprocess import PIPE, Popen
from time import sleep

from component_utility_predictor import RidgeUtilityPredictor

import pandas as pd
import numpy as np

logging.basicConfig()
logger = logging.getLogger('controller')
logger.setLevel(logging.INFO)

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
        self.utility_model = RidgeUtilityPredictor()
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
        logger.info('Connected to the Java side.')

    def _get_initial_state(self):
        self.number_of_shops = self._get_from_mrubis('get_number_of_shops').get('number_of_shops')
        logger.info(f'Number of mRUBIS shops: {self.number_of_shops}')
        for _ in range(self.number_of_shops):
            shop_state = self._get_from_mrubis('get_initial_state')
            shop_name = next(iter(shop_state))
            self.mrubis_state[shop_name] = shop_state[shop_name]

    def _update_number_of_issues_in_run(self):
        self.number_of_issues_in_run = self._get_from_mrubis('get_number_of_issues_in_run').get('number_of_issues_in_run')

    def _get_from_mrubis(self, message):

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

    @staticmethod
    def _get_info_from_issue(issue):
        shop_name = next(iter(issue))
        component_name = next(iter(issue[shop_name]))
        component_params = issue.get(shop_name).get(component_name)
        issue_name = component_params.get('failure_name')
        rules = [rule.strip() for rule in component_params['rule_names'].strip('[]').split(',')]
        rule_costs = [float(costs) for costs in component_params['rule_costs'].strip('[]').split(',')]
        return shop_name, component_name, component_params, issue_name, rules, rule_costs

    def _pick_rule(self, issue, method='lowest'):
        _, component_name, _, _, rules, rule_costs = self._get_info_from_issue(issue)

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
        logger.info(f"{shop_name}: Handling {issue_name} on {component_name} with {rule}")
        logger.debug('Sending selected rule to mRUBIS...')
        self.socket.send((json.dumps(picked_rule_message)  + '\n').encode("utf-8"))
        logger.debug("Waiting for mRUBIS to answer with 'rule_received'...")
        data = self.socket.recv(64000)
        if data.decode('utf-8').strip() == 'rule_received':
            logger.debug('Rule transmitted successfully.')
        # Remember components that have been fixed in this run
        if self.components_fixed_in_this_run.get(shop_name) is None:
            self.components_fixed_in_this_run[shop_name] = []
        self.components_fixed_in_this_run[shop_name].append((issue_name, component_name))

    def _predict_optimal_utility_of_fixed_components(self):
        for shop, fixed_components in self.components_fixed_in_this_run.items():
            for issue_name, component in fixed_components:
                component_params = self.mrubis_state[shop][component]
                predicted_utility = self.utility_model.predict_on_mrubis_output(
                    pd.DataFrame(component_params, index=[0])
                )[0]
                self.mrubis_state[shop][component]['predicted_optimal_utility'] = predicted_utility

    def _get_component_fixing_order(self, state_df_before):
        fix_order_tuples = state_df_before.dropna(subset=['predicted_optimal_utility'])\
                              .sort_values(by='predicted_optimal_utility', ascending=False)\
                              .reset_index(level=0)\
                              .set_index('failure_name', append=True)\
                              .reorder_levels([0,2,1])\
                              .index\
                              .tolist()
        fix_order_dicts = {shop: (issue, comp) for shop, issue, comp in fix_order_tuples}
        all_fix_order_tuples = []
        for shop, _ in fix_order_dicts.items():
            for i_c_tuple in self.components_fixed_in_this_run[shop]:
                all_fix_order_tuples.append((shop, i_c_tuple[0], i_c_tuple[1]))
        return all_fix_order_tuples

    def _send_order_in_which_to_apply_fixes(self, order_tuples):
        logger.debug('Sending order in which to apply fixes to mRUBIS...')
        order_dict = {idx: {
                'shop': fix_tuple[0],
                'issue': fix_tuple[1],
                'component': fix_tuple[2]
            } for idx, fix_tuple in enumerate(order_tuples)}
        self.socket.send((json.dumps(order_dict)  + '\n').encode("utf-8"))
        logger.debug("Waiting for mRUBIS to answer with 'fix_order_received'...")
        data = self.socket.recv(64000)
        if data.decode('utf-8').strip() == 'fix_order_received':
            logger.debug('Order transmitted successfully.')

    def _send_exit_message(self):
        self.socket.send("exit\n".encode("utf-8"))
        _ = self.socket.recv(64000)

    def _close_socket(self):
        self.socket.close()

    def _state_to_df(self, fix_status):
        state_df = pd.DataFrame.from_dict({
            (fix_status, shop, component): self.mrubis_state[shop][component] 
                for shop in self.mrubis_state.keys() 
                for component in self.mrubis_state[shop].keys()},
            orient='index')
        self._set_shop_and_system_utility(state_df, fix_status)
        return state_df

    def _set_shop_and_system_utility(self, state_df, fix_status):
        if fix_status == 'before':
            state_df['system_utility'] = state_df['system_utility'].min()
            state_df['shop_utility'] = state_df.groupby(level=[1])['shop_utility'].transform('min')
        if fix_status == 'after':
            state_df['system_utility'] = state_df['system_utility'].max()
            state_df['shop_utility'] = state_df.groupby(level=[1])['shop_utility'].transform('max')

    def _write_state_history_to_disk(self, filename='mrubis'):
        history_df = pd.concat(self.mrubis_state_history, keys=np.repeat(np.arange(1, len(self.mrubis_state_history)+1), 2)).reset_index()
        history_df.columns = ['run', 'fix_status', 'shop', 'component'] + list(history_df.columns)[4:]
        self.output_path.mkdir(exist_ok=True)
        logger.info('Writing run history to disk...')
        history_df.to_csv(self.output_path / f'{filename}.csv', index=False)
        #history_df.to_excel(self.output_path / f'{filename}.xls', index=False)

    def _update_current_state(self, incoming_state):
        for shop, shop_components in incoming_state.items():
            for component_type, component_params in shop_components.items():
                if shop not in self.mrubis_state.keys():
                    self.mrubis_state[shop] = {}
                if component_type not in self.mrubis_state[shop].keys():
                    self.mrubis_state[shop][component_type] = {}
                for param, value in component_params.items():
                    self.mrubis_state[shop][component_type][param] = value
    
    def _reset_predicted_utility(self):
        for shop, shop_components in self.mrubis_state.items():
            for component, _ in shop_components.items():
                self.mrubis_state[shop][component]['predicted_optimal_utility'] = np.nan


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
                logger.info('MRUBIS is running')

        sleep(0.5)

        self._connect_to_java()

        # Train the model on the provided batch file
        self.utility_model.load_train_data()
        self.utility_model.train_on_batch_file()

        # TODO: explain design decisions in comments

        while self.run_counter < max_runs:
            self.run_counter += 1
            self.components_fixed_in_this_run = {}
            self.number_of_issues_handled_in_this_run = 0
            self.number_of_issues_in_run = 1 # make sure that the loop runs at least once

            logger.info(f"Getting state {self.run_counter}/{max_runs}...")

            if self.run_counter == 1:
                self._get_initial_state()

            while self.number_of_issues_handled_in_this_run < self.number_of_issues_in_run:

                # Check how many issues there are (equals # of queries to send)
                self._update_number_of_issues_in_run()

                # Get the current issue to handle
                current_issue = self._get_from_mrubis('get_issue')
                self._update_current_state(current_issue)

                # Pick rule, send it to mRUBiS
                picked_rule = self._pick_rule(current_issue, method=rule_picking_method)
                self._send_rule_to_execute(current_issue, picked_rule)

                self.number_of_issues_handled_in_this_run += 1

            logger.info(f'Total number of issues to handle in current run: {self.number_of_issues_in_run}')
            logger.info(f'Total number of issues handled: {self.number_of_issues_handled_in_this_run}')

            self._predict_optimal_utility_of_fixed_components()
            state_df_before = self._state_to_df(fix_status='before')
            self.mrubis_state_history.append(state_df_before)

            component_fixing_order = self._get_component_fixing_order(state_df_before)
            if len(component_fixing_order) != self.number_of_issues_handled_in_this_run:
                logger.error(f'Lost track of a fix somewhere')
            logger.info(f'Fixing in this order: {component_fixing_order}')
            self._send_order_in_which_to_apply_fixes(component_fixing_order)

            logger.info("Getting state of affected components after taking action...")
            state_after_action = self._get_from_mrubis(
                message=json.dumps(
                    {shop_name: [i_c_tuple[1] for i_c_tuple in i_c_tuples] for shop_name, i_c_tuples in self.components_fixed_in_this_run.items()}
                )
            )
            self._update_current_state(state_after_action)
            self._remove_replaced_authentication_service()
            self._reset_predicted_utility()

            state_df_after = self._state_to_df(fix_status='after')
            self.mrubis_state_history.append(state_df_after)

        self._send_exit_message()
        self._close_socket()

        if not external_start:
            self._stop_mrubis()

        self._write_state_history_to_disk(filename=f'{max_runs}_runs_{rule_picking_method}')

if __name__ == "__main__":
    
    controller = MRubisController()
    controller.run(external_start=True, max_runs=100, rule_picking_method='highest')
