import time
import matplotlib.pyplot as plt
import num_interface

def print_simulation_options():
    print(f"2: solving NUM problem with primal or dual algorithm with specific alpha")
    print(f"4: solving NUM problem with Primal and dual and diffrent alpha values ")
    print(f"5: solving NUM problem with Primal and dual and dijkastra distance")
    print(f"6: solving NUM problem with Primal and dual and bellman ford distance")
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


def get_algorithm_input():
    while True:
        try:
            algo_input = int(input("Enter 1 for Primal algorithm or 2 for Dual algorithm: "))
            if algo_input == 1:
                return "Primal"
            elif algo_input == 2:
                return "Dual"
            else:
                print("Invalid input. Please enter either 1 or 2.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_valid_input(prompt, input_type, condition=lambda x: True, error_message="Invalid input."):
    while True:
        try:
            value = input_type(input(prompt))
            if condition(value):
                return value
            else:
                print(error_message)
        except ValueError:
            print(error_message)

def input_pram():
    num_of_users = get_valid_input("Enter the number of users (N): ", int, condition=lambda x: x > 0,error_message="Number of users must be a positive integer.")

    radius = get_valid_input("Enter the radius (M): ",float,condition=lambda x: x > 0,error_message="Radius must be a positive number.")

    neighbors_radius = get_valid_input("Enter the neighbors' radius (R): ",float,condition=lambda x: x > 0,error_message="Neighbors' radius must be a positive number.")

    return num_of_users,radius, neighbors_radius



def active_Q2_Q3():
    Algo = get_algorithm_input()
    alpha = get_alpha_input()
    N,M,R=input_pram()
    num_interface.num(alpha,num_of_users=N, radius=M, neighbors_radius=R,Algo=Algo )

def active_Q4():
    Algo = get_algorithm_input()
    alpha = [1,2,float("inf")]
    N,M,R=input_pram()
    for a in alpha:
        num_interface.num(a,num_of_users=N, radius=M, neighbors_radius=R,Algo=Algo )
    
def active_Q5():
    Algo = get_algorithm_input()
    alpha = get_alpha_input()
    N,M,R=input_pram()
    num_interface.dijkastra(alpha,num_of_users=N, radius=M, neighbors_radius=R,Algo=Algo )

def active_Q6():
    Algo = get_algorithm_input()
    alpha = get_alpha_input()
    N,M,R=input_pram()
    num_interface.bellman_ford(alpha,num_of_users=N, radius=M, neighbors_radius=R,Algo=Algo )

Q_active_functions_dict = {2: active_Q2_Q3, 4: active_Q4, 5: active_Q5, 6: active_Q6}

if __name__ == "__main__":
    print(f"Welcome to NUM simulator")
    user_seletion=selection()
    while user_seletion != 99:
        Q_active_function = Q_active_functions_dict.get(user_seletion)
        Q_active_function()
        user_seletion = selection()
    print(f"Thank you for using NUM simulator")
    time.sleep(1.5)