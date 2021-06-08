import json
import socket
from json.decoder import JSONDecodeError
from subprocess import PIPE, Popen
from time import sleep

def initialize_mrubis():
    # Put your command line here (In Eclipse: Run -> Run Configurations... -> Show Command Line)

    with open('path.json', 'r') as f:
        launch_args = json.load(f)

    args = [
        launch_args['java_path'],
        '-DFile.encoding=UTF-8',
        '-classpath',
        launch_args['dependency_paths'],
        '-XX:+ShowCodeDetailsInExceptionMessages',
        launch_args['class_to_run'],
    ]

    pipe = Popen(
         args, 
         stdin=PIPE, 
         stdout=PIPE, 
         shell=False,
         cwd=launch_args['ML_based_control_dir']
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


def main():

    proc = initialize_mrubis()

    if proc.poll is None:
        print('MRUBIS is running')

    sleep(2)

    HOST = "localhost"
    PORT = 8080

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    sock.sendall("get_all\n".encode("utf-8"))
    data = sock.recv(64000)

    # Program flow:
    try:
        mrubis_state = json.loads(data.decode("utf-8"))
        print(mrubis_state)
    except JSONDecodeError:
        print("Could not decode JSON input, received this:")
        print(data)

    sock.sendall("exit\n".encode("utf-8"))
    sock.close()
    print("Socket closed")

    proc.terminate()

if __name__ == "__main__":
    main()