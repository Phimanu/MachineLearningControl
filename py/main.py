from subprocess import PIPE, Popen


def initialize_mrubis():
    # Put your command line here (In Eclipse: Run -> Run Configurations... -> Show Command Line)
    path = open("path.txt").read()
    args = fr'{path}'

    return Popen(args, stdin=PIPE, stdout=PIPE, shell=False)

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
    mrubis = initialize_mrubis()

    #Run EITHER of the two code blocks below
    #This doesnt work.
    for i in range(10):
        mrubis.stdin.write("Test\r\n".encode("utf-8"))
        ans = mrubis.stdout.readline()
        print(ans)

    # This works but enforces connection close.
    ans = mrubis.communicate(input="Test\r\n".encode("utf-8"))
    print(ans)

main()
