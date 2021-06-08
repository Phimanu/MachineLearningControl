import json
import socket
from json.decoder import JSONDecodeError
from subprocess import PIPE, Popen
from time import sleep

def initialize_mrubis():
    # Put your command line here (In Eclipse: Run -> Run Configurations... -> Show Command Line)

    with open('path.json', 'r') as f:
        variable_paths = json.load(f)

    args = [
        variable_paths['java_path'],
        '-DFile.encoding=UTF-8',
        '-classpath',
        variable_paths['dependency_paths'],
        '-XX:+ShowCodeDetailsInExceptionMessages',
        'mRUBiS_Tasks.Task_1',
    ]

    pipe = Popen(
         args, 
         stdin=PIPE, 
         stdout=PIPE, 
         shell=False,
         cwd="../mRUBiS/ML_based_Control"
    )

    return pipe

'''
def components_status():
    #Map<Shop_id, Component_type, CF_x, shop_id>

def components_utility():
    #Map<Component_type, Map<Param_1, ..., Param_N, Utility, shop_id>

def component_actions_costs():
    #Map<Component_type, CF_x, Action, cost, shop_id>

def system_utility():
    #like SUM(components_utility()

def get_shop_id():
    #shop_id

def get_environment_type():
    #Environment_type

def fix_component():

    #input: Map<Shop_id, Component_type, CF, action>
    #bool
    #[This will transition mRuBis to the next RUN]

def load_model():
    #
'''

def get_json_from_java():
    HOST = "localhost"
    PORT = 8080

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    sock.sendall("get_all\n".encode("utf-8"))
    data = sock.recv(64000)

    # Program flow:
    try:
        mrubis_state = json.loads(data.decode("utf-8"))
    except JSONDecodeError:
        print("Could not decode JSON input, received this:")
        print(data)
        mrubis_state = "not available"

    sock.sendall("exit\n".encode("utf-8"))
    sock.close()
    print("Socket closed")

    return mrubis_state


def main():

    proc = initialize_mrubis()

    if proc.poll is None:
        print('MRUBIS is running')

    sleep(2)

    print("Getting first state...")
    mrubis_state = get_json_from_java()
    print(mrubis_state)

    print("Getting second state...")
    mrubis_state = get_json_from_java()
    print(mrubis_state)

    proc.terminate()

if __name__ == "__main__":
    main()