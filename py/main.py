import json
import socket
from json.decoder import JSONDecodeError
from subprocess import PIPE, Popen
from time import sleep
import pandas as pd

class MRubisController():

    def __init__(self, host='localhost', port=8080, json_path='path.json') -> None:

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
        rules = component_params['rule_names'].strip('[]').split(',')
        rule_costs = component_params['rule_costs'].strip('[]').split(',')
        return shop_name, component_name, component_params, issue_name, rules, rule_costs

    @staticmethod
    def _pick_rule(issue, rules, rule_costs):
        return rules[0]

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
        data = self.socket.recv(64000)

    def _close_socket(self):
        self.socket.close()

    def _append_current_state_to_history(self):
        mrubis_df = pd.DataFrame.from_dict({
            (i,j): self.mrubis_state[i][j] 
                for i in self.mrubis_state.keys() 
                for j in self.mrubis_state[i].keys()},
            orient='index')

        self.mrubis_state_history.append(mrubis_df)

    def _write_state_history_to_disk(self, filename='mrubis'):
        mrubis_df = pd.concat(self.mrubis_state_history, keys=range(len(self.mrubis_state_history)))
        mrubis_df.to_csv(f'{filename}.csv')
        mrubis_df.to_excel(f'{filename}.xls')

    def _update_current_state(self, incoming_state):
        for shop, shop_components in incoming_state.items():
            for component_type, component_params in shop_components.items():
                if component_type not in self.mrubis_state[shop].keys():
                    self.mrubis_state[shop][component_type] = {}
                for param, value in component_params.items():
                    self.mrubis_state[shop][component_type][param] = value

    def run(self, external_start=False, max_runs=100):

        if not external_start:
            self._start_mrubis()
            if self.mrubis_process.poll() is None:
                print('MRUBIS is running')

        sleep(0.5)

        self._connect_to_java()

        # TODO: explain design decisions in comments

        while self.run_counter < max_runs:
            self.run_counter += 1

            print(f"Getting state {self.run_counter}/{max_runs}...")

            if self.run_counter == 1:
                self._get_initial_state()

            components_fixed_in_this_run = {}
            number_of_issues_handled_in_this_run = 0
            self.number_of_issues_in_run = 1 # make sure that the loop runs at least once
            while number_of_issues_handled_in_this_run < self.number_of_issues_in_run:

                self._update_number_of_issues_in_run()

                current_issue = self._get_from_mrubis('get_issue')
                self._update_current_state(current_issue)

                shop_name, component_name, _, _, rules, rule_costs = self._get_info_from_issue(current_issue)
                picked_rule = self._pick_rule(current_issue, rules, rule_costs)
                self._send_rule_to_execute(current_issue, picked_rule)

                if components_fixed_in_this_run.get(shop_name) is None:
                    components_fixed_in_this_run[shop_name] = []
                components_fixed_in_this_run[shop_name].append(component_name)
                number_of_issues_handled_in_this_run += 1

            print(f'Applied actions to these components in this run: {components_fixed_in_this_run}')
            self._append_current_state_to_history()

            print("Getting state of affected components after taking action...")
            state_after_action = self._get_from_mrubis(message=json.dumps(components_fixed_in_this_run))
            self._update_current_state(state_after_action)
            self._append_current_state_to_history()

        self._send_exit_message()
        self._close_socket()

        if not external_start:
            self._stop_mrubis()

        self._write_state_history_to_disk()

if __name__ == "__main__":
    controller = MRubisController()
    controller.run(external_start=True, max_runs=100)