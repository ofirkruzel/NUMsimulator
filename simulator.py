import time
import matplotlib.pyplot as plt

def print_simulation_options():
    print(f"2: solving NUM problem with primal algorithm with different alpha-fairness values")
    print(f"3: solving NUM problem with dual algorithm with different alpha-fairness values")
    print(f"4")
    print(f"5")
    print(f"6")
    print(f"99: stop simulating")


def selection():
    print_simulation_options()
    selection = input(f"\nplease choose from above:")
    while selection not in ["2", "3", "4", "5", "6", "99"]:
        print(f"\n\nyour input can only be from below options, please select again:")
        print_simulation_options()
        selection = input(f"\nselection:")
    return int(selection)

def get_alpha_input():
    while True:
        try:
            alpha_input = int(input("Enter choise for alpha = 1,2,3 for infinity: "))
            if alpha_input == 1:
                return 1
            elif alpha_input == 2:
                return 2
            elif alpha_input == 3:
                return float('inf')
            else:
                print("Invalid input. Please enter either 1, 2, or 3.")
        except ValueError:
            print("Invalid input. Please enter a number.")



def active_Q2():
    #primal algorithm
    N = 5
    Algo ="Primal"
    alpha = get_alpha_input()
    set_global_params(n=N)
    Fun.calc_inter_face = False
    network = Fun.Network(create_network_type="NUM")
    network.draw_network()
    print(network)
    fun_function.CalcNetworkRate(network, alpha, Algo)
    plt.show()  # to stop the code so we can analyze the graph showing the rates


Q_active_functions_dict = {2: active_Q2, 3: active_Q3, 4: active_Q4, 5: active_Q5, 6: active_Q6}

if __name__ == "__main__":
    print(f"Welcome to NUM simulator")
    user_seletion=selection()
    while user_seletion != 99:
        Q_active_function = Q_active_functions_dict.get(user_seletion)
        Q_active_function()
        user_seletion = selection()
    print(f"Thank you for using NUM simulator")
    time.sleep(1.5)