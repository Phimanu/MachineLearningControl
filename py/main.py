import json
import socket
from json.decoder import JSONDecodeError
from subprocess import PIPE, Popen
from time import sleep
import pandas as pd

'''
def components_status():
    #Map<Shop_id, Component_type, CF_x> # does the ID change upon restarting? # issues lists seem to be empty / no comp_utility of 0

def components_utility():
    #Map<Component_type, Map<Param_1, ..., Param_N, Utility, shop_id>

def component_actions_costs():
    #Map<Component_type, CF_x, Action, cost, shop_id>

def get_environment_type():
    #Environment_type

def fix_component():

    #input: Map<Shop_id, Component_type, CF, action>
    #bool
    #[This will transition mRuBis to the next RUN]

def load_model():
    #
'''

def system_utility(mrubis_state):
    '''Calculates the utility for the entire system (across shops)'''
    total_utility = 0
    for shop_attrs in mrubis_state.values():
        for comp_attrs in shop_attrs.values():
            total_utility += float(comp_attrs['component_utility'])
    return total_utility

def components_utility(mrubis_state, shop_id):
    component_utilities = {}
    for comp_attrs in mrubis_state[shop_id].values():
        component_utilities[comp_attrs['name']] = float(comp_attrs['component_utility'])
    return component_utilities

def get_shop_id(mrubis_state):
    return list(mrubis_state.keys())[0]

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
        self.mrubis_state = {}
        self.mrubis_state_history = []
        self.available_rules = {}
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

    def _get_mrubis_state(self):

        self.socket.send("get_all\n".encode("utf-8"))
        data = self.socket.recv(64000)

        try:
            mrubis_state = json.loads(data.decode("utf-8"))
        except JSONDecodeError:
            print("Could not decode JSON input, received this:")
            print(data)
            mrubis_state = "not available"

        return mrubis_state

    def _identify_available_rules(self):
        for shop, shop_components in self.mrubis_state.items():
            self.available_rules[shop] = {}
            for component_uid, component_params in shop_components.items():
                if component_params.get('failure_names'):
                    comp = shop_components[component_uid]
                    issue = comp['failure_names']
                    rules = comp['rule_names'].strip('[]').split(',')
                    costs = comp['rule_costs'].strip('[]').split(',')
                    self.available_rules[shop][issue] = {rule:cost for rule, cost in zip(rules, costs)}
    
    def _print_rules(self, rules_map=None):
        if rules_map is None:
            rules_map = self.available_rules
        for shop, issue_to_rule_map in rules_map.items():
            print(f"Shop: {shop}:")
            if isinstance(issue_to_rule_map, dict):
                for issue, rule_to_cost_map in issue_to_rule_map.items():
                    print(f"    Issue: {issue}")
                    if isinstance(rule_to_cost_map, dict):
                        for rule, cost in rule_to_cost_map.items():
                            print(f"        Rule: {rule} (cost: {cost})")
                    else:
                        print(f"        Rule: {rule_to_cost_map}")
            else:
                print(f"     {rules_map[shop]}")

    def _pick_first_available_rule(self):
        rules_to_execute = {}
        for shop, issue_to_rule_map in self.available_rules.items():
            rules_to_execute[shop] = {}
            if issue_to_rule_map:
                for issue, rule_to_cost_map in issue_to_rule_map.items():
                    picked_rule_name = list(rule_to_cost_map.keys())[0]
                    rules_to_execute[shop][issue] = picked_rule_name
            else:
                rules_to_execute[shop] = 'No issues'
        return rules_to_execute

    def _send_rules_to_execute(self, issue_to_rule_map):
        self.socket.send((json.dumps(issue_to_rule_map)  + '\n').encode("utf-8"))
        data = self.socket.recv(64000)
        if data.decode('utf-8').strip() == 'rules_received':
            print('Rules transmitted successfully')

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

    def _parse_initial_state(self, initial_state):
        for shop, shop_components in initial_state.items():
            self.mrubis_state[shop] = {}
            for component_uid, component_params in shop_components.items():
                self.mrubis_state[shop][component_uid] = {}
                for param, value in component_params.items():
                    self.mrubis_state[shop][component_uid][param] = value

    def _update_current_state_with_new_issues(self, incoming_state):
        for shop, shop_components in incoming_state.items():
            for component_uid, component_params in shop_components.items():
                if component_uid not in self.mrubis_state[shop].keys():
                    self.mrubis_state[shop][component_uid] = {}
                for param, value in component_params.items():
                    self.mrubis_state[shop][component_uid][param] = value

    def run(self, external_start=False, max_runs=100):

        if not external_start:
            self._start_mrubis()
            if self.mrubis_process.poll is None:
                print('MRUBIS is running')

        self._connect_to_java()
        
        while self.run_counter < max_runs:
            self.run_counter += 1
            sleep(0.1)

            print(f"Getting state {self.run_counter}/{max_runs}...")
            incoming_state = self._get_mrubis_state()

            if self.run_counter == 1:
                self._parse_initial_state(incoming_state)
                print('Received the initial mRUBIS state.')
                print(incoming_state)
            else:
                self._update_current_state_with_new_issues(incoming_state)
            
            self._identify_available_rules()
            print("Available rules:")
            self._print_rules()
            picked_rules = self._pick_first_available_rule()
            print(f"Chosen rule:")
            self._print_rules(picked_rules)
            self._send_rules_to_execute(picked_rules)

            
            self._append_current_state_to_history()

        self._send_exit_message()
        self._close_socket()

        if not external_start:
            self._stop_mrubis()

        self._write_state_history_to_disk()

if __name__ == "__main__":
    controller = MRubisController()
    controller.run(external_start=False, max_runs=100)