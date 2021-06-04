from subprocess import PIPE, Popen
import socket
import json

def initialize_mrubis():
    # Put your command line here (In Eclipse: Run -> Run Configurations... -> Show Command Line)

    with open('path.json', 'r') as f:
        launch_args = json.load(f)

    args = [
        'cd',
        '/Users/paul/Documents/Control/MachineLearningControl/mRUBiS/ML_based_Control/src/mRUBiS_Tasks/',
        '&&',
        launch_args['java_path'],
        '-DFile.encoding=UTF-8',
        '-classpath',
        launch_args['dependency_paths'],
        '-XX:+ShowCodeDetailsInExceptionMessages',
        launch_args['class_to_run'],
        '&&'
        'cd',
        '/Users/paul/Documents/Control/MachineLearningControl/py'
    ]

    pipe = Popen(
        args, 
        stdin=PIPE, 
        stdout=PIPE, 
        shell=False
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
    pipe = initialize_mrubis()
    if pipe.returncode is None:
        print('MRUBIS is running')
    HOST = "localhost"
    PORT = 8080

    print(pipe.stdin)
    print(pipe.stdout)
    print(pipe.stderr)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    sock.sendall("get_all\n".encode("utf-8"))
    data = sock.recv(64000)

    # Program flow:
    print(data)
    sock.sendall("exit\n".encode("utf-8"))
    sock.close()
    print("Socket closed")

    pipe.terminate()

    #Run EITHER of the two code blocks below
    #This doesnt work.
    #for i in range(10):
    #    mrubis.stdin.write("Test\r\n".encode("utf-8"))
    #    ans = mrubis.stdout.readline()
    #    print(ans)

    # This works but enforces connection close.
    #ans = mrubis.communicate(input="Test\r\n".encode("utf-8"))
    #print(ans)


if __name__ == "__main__":
    main()
