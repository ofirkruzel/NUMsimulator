
import random
import math
import matplotlib.pyplot as plt
import copy
import heapq
import numpy as np
import ipywidgets as widgets
from IPython.display import display
import time

N = 6  # num of vertex
M = 10  # network radius
R = 2  # neighbors radius
K = 1  # num of channels
F = 10  # number of flows
FLOW_MAX_DATA = 1000
calc_inter_face = False

CONSTANT_POWER = 1
CONSTANT_BW = 1
down_Ri = 41e5
K_B = 1.38e-23  # Boltzmann constant in Joules/Kelvin
T = 290       # Temperature in Kelvin


def set_global_params(k=None, n=None, m=None, r=None, f=None):
    global K, N, M, R, F
    K = k or 1
    N = n or 5
    M = m or 10
    R = r or 2
    F = f or 10

def PrintRateResults(xAxis, yAxis, users, alpha, Algorithm):
    plt.figure()
    print(f"-------------------------")
    print(f"{Algorithm} Algorithm, alpha={str(alpha)} Results:")
    sum_rate = 0
    for user in users:
        sum_rate += user.rate
        print(f"user {user.Uid} rate : {round(user.rate,2)}")
    print(f"sum_rate={round(sum_rate,2)}\n")
    for i in range(len(xAxis)):
        plt.plot(xAxis[i], yAxis[i], label=f"user {i+1}")
    plt.title(f"{Algorithm} Algorithm, alpha={str(alpha)}")
    plt.xlabel("Iteration Number")
    plt.ylabel("Rate")
    plt.legend()
    plt.grid()
    plt.show(block=False)

def CalcDualRate(user, users, alpha, x_r, stepSize=0.0001):
    """ this function calculates the next rate of a given user for the dual algorithm """

    if alpha == float("inf"):
        # Adjusting based on the max constraint violation
        max_excess = max((sum(u.rate for u in users if link in u.links) - link.total_capacity) for link in user.links)
        return max(0, min(1, x_r - stepSize * max_excess))

    Q_l = 0
    for link in user.links:  # calculate the payment of the user
        rateSum = sum(u.rate for u in users if link in u.links) # Y_l
        L_delta = (rateSum - link.total_capacity) * stepSize
        link.LagrangianMultiplier = max(0, link.LagrangianMultiplier + L_delta)
        Q_l += link.LagrangianMultiplier
    if Q_l == 0:
        print("Ql is zero!")
    return pow(Q_l, -1/alpha) if Q_l != 0 else 0 # the inverse function of the utilization function


def penaltyFunction(rate, capacity):
    if rate < capacity:
        return rate * capacity
    else:
        try:
            return pow(rate, 3) * 2
        except OverflowError: # TODO: check why it is overflow error
            return 0

def CalcPrimalRate(user, users, alpha, x_r, stepSize=0.0001):
    if alpha == float("inf"):
        avg_rate = sum(u.rate for u in users) / len(users)
        new_rate = max(0, min(1, avg_rate + stepSize)) if user.rate < avg_rate else max(0, user.rate - stepSize)
        return min(new_rate, 1)  # Ensure the rate does not exceed 1

    payment = 0
    for link in user.links:  # calculate the payment of the user
        rateSum = 0
        for u in users:  # calculate the sum of the rates of all the users on the link
            if link in u.links:
                rateSum += u.rate
        payment += penaltyFunction(rateSum, link.total_capacity)

    new_rate = stepSize * (pow(user.rate, -1 * alpha) - payment) + x_r  # calculate the next rate of the user
    return min(max(new_rate, 0), 1)  # Ensure the rate is within [0, 1]


def CalcNetworkRate(network, alpha, Algorithm, N=1e5):
    network.initial_users_rates()
    algorithm_functions = {"Primal": CalcPrimalRate, "Dual": CalcDualRate}
    CalcRate = algorithm_functions.get(Algorithm)
    users = network.users

    xAxis = []
    yAxis = []
    for _ in users:  # initialize the graph
        xAxis.append([])
        yAxis.append([])

    for i in range(int(N)):
        curUser = random.choice(users)
        id = curUser.Uid-1
        x_r = curUser.rate
        curUser.rate = CalcRate(curUser, users, alpha, x_r)
        xAxis[id].append(i)
        yAxis[id].append(curUser.rate)

    PrintRateResults(xAxis, yAxis, users, alpha, Algorithm)

def dijkstra_algorithm(network, start_vertex):
    # Initialize distances to all vertices in the network as infinity, except for the start vertex set to 0
    distances = {vertex: float('inf') for vertex in network.vertices}
    previous_nodes = {vertex: None for vertex in network.vertices}
    distances[start_vertex] = 0
    priority_queue = [(0, start_vertex)]  # Priority queue to manage the exploration of vertices

    # The main loop continues until there are no more vertices to explore
    while priority_queue:
        current_distance, current_vertex = heapq.heappop(priority_queue)  # Pop the vertex with the lowest distance
        if current_distance > distances[current_vertex]:  # If the popped distance is greater then known stop explore
            continue

        for neighbor, link in current_vertex.neighbors.items(): # Explore each neighbor of the current vertex
            distance = current_distance + link.weight

            if distance < distances[neighbor]:  # If the new distance is less than the previous update route
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_vertex
                heapq.heappush(priority_queue, (distance, neighbor))  # Push the updated distance for further explore

    return distances, previous_nodes


def bellman_ford_algorithm(network, start_vertex):
    # Initialize distances to all vertices in the network as infinity, except for the start vertex set to 0
    distances = {vertex: float('inf') for vertex in network.vertices}
    previous_nodes = {vertex: None for vertex in network.vertices}
    distances[start_vertex] = 0

    # Relax edges repeatedly
    for _ in range(len(network.vertices) - 1):
        for vertex in network.vertices:
            for neighbor, link in vertex.neighbors.items():
                if distances[vertex] + link.weight < distances[neighbor]:
                    distances[neighbor] = distances[vertex] + link.weight
                    previous_nodes[neighbor] = vertex

    # Check for negative-weight cycles
    for vertex in network.vertices:
        for neighbor, link in vertex.neighbors.items():
            if distances[vertex] + link.weight < distances[neighbor]:
                raise ValueError("Graph contains a negative-weight cycle")

    return distances, previous_nodes


def visualize_flow_rates_and_link_utilization(network, K):
    # Data for Flow Rates vs. Data Amounts
    data_amounts = [flow.data_amount for flow in network.flows]
    flow_rates = [flow.rate for flow in network.flows]
    link_ids = [link.Lid for link in network.links]

    average_utilities = []
    channel_data = {}  # Dict to hold data per channel per link

    # Collecting data
    for link in network.links:
        channel_data[link] = [0] * K  # Initialize with zero flow rate for each channel
        for user in network.users:
            if link in user.links:
                for flow in user.flows:
                    channel_data[link][flow.channel] += flow.rate

    for i, link in enumerate(network.links):
        rates = channel_data[link]
        utilities = [(rate / link.total_capacity) * 100 for rate in rates]  # Calculate utility as a percentage
        average_utility = sum(utilities)
        rounded_average_utility = int(round(average_utility))
        average_utilities.append(rounded_average_utility)

    # Calculate the overall average utility
    overall_average_utility = sum(average_utilities) / len(average_utilities)

    # Create a figure with 2 subplots
    fig, axs = plt.subplots(2, 1, figsize=(15, 7))  # 2 rows, 1 column

    # Subplot 1: Flow Rates vs. Data Amounts
    axs[0].scatter(data_amounts, flow_rates, color='red')
    axs[0].set_title('Flow Rates vs. Data Amounts')
    axs[0].set_xlabel('Data Amount')
    axs[0].set_ylabel('Flow Rate (bps)')
    axs[0].grid(True)

    # Subplot 2: Link Capacity Utilization
    colors = ['green' if percent == 100 else 'red' for percent in average_utilities]
    axs[1].bar(link_ids, average_utilities, color=colors, width=0.4)  # Adjust bar width to 0.4 for thinner bars
    axs[1].set_title('Link Capacity Utilization (%)')
    axs[1].set_xlabel('Link ID')
    axs[1].set_ylabel('Utilization (%)')
    axs[1].set_ylim(0, 100)
    axs[1].set_xticks(link_ids)
    axs[1].tick_params(axis='x', rotation=45)  # Rotate x-tick labels to prevent overlap
    axs[1].grid(True)

    # Adding a horizontal line for the overall average utility
    axs[1].axhline(y=overall_average_utility, color='blue', linestyle='--', label=f'Average Utility: {overall_average_utility:.2f}%')
    axs[1].legend(loc='upper left')

    # Display the combined plot
    plt.tight_layout()
    plt.show(block=False)


def set_flows_rate_based_on_tdma(network, K):
    for link in network.links:
        flows = []
        total_data = [0] * K
        users_using_link = [user for user in network.users if link in user.links]
        for user in users_using_link:
            for flow in user.flows:
                flows.append(flow)
                total_data[flow.channel] += flow.data_amount

        for flow in flows:
            flow.rate_by_links[link] = link.channels_capacities[flow.channel] * flow.data_amount / total_data[flow.channel]

    for flow in network.flows:
        flow.set_rate_2_min_of_rate_by_links()

    visualize_flow_rates_and_link_utilization(network, K)



def calculate_path_loss(distance, path_loss_exponent=3.5, PL0=-30):
    if distance <= 0:
        raise ValueError("Distance must be greater than 0")
    path_loss = PL0 + 10 * path_loss_exponent * np.log10(distance)
    return path_loss

def rayleigh_fading():
    """
    Simulate small scale fading using Rayleigh distribution.
    :return: A random fading coefficient sampled from a Rayleigh distribution.
    """
    return np.random.rayleigh()

class Vertex:
    """ this class represent a (represent a node in a graph) vertex in the network """

    def __init__(self, Vid):
        self.Vid = Vid #Unique identifier for the vertex.
        self.location = self.generate_location() #method to assign a location to the vertex.
        self.neighbors = {} #A dictionary to store neighboring vertices and the links connecting them.
        self.ShortestPath = {}  # Dictionary to store shortest paths to other vertices
        self.power = 0
        self.bw = 0 #bandwidth

    def __str__(self):
        return str(self.Vid)

    def __lt__(self, other):
        return self.Vid < other.Vid

    def __eq__(self, other):
        return self.Vid == other.Vid

    def __hash__(self):
        return hash(self.Vid)

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        result.Vid = self.Vid
        result.location = copy.deepcopy(self.location, memo)
        result.power = self.power
        result.bw = self.bw
        result.neighbors = {copy.deepcopy(key, memo): copy.deepcopy(value, memo) for key, value in
                            self.neighbors.items()}
        result.ShortestPath = {copy.deepcopy(key, memo): copy.deepcopy(value, memo) for key, value in
                               self.ShortestPath.items()}
        return result

    def generate_location(self):
        """
        Generates a random location within a circle of radius M centered at the origin.
        """
        theta = random.uniform(0, 2 * math.pi)  # Angle for circular distribution
        r = M * math.sqrt(random.uniform(0, 1))  # Distance from the center, sqrt for uniform distribution within the circle
        x = round(r * math.cos(theta), 2)
        y = round(r * math.sin(theta), 2)
        return x, y

    def distance_to(self, other):
        """
        Calculates the Euclidean distance between two vertices.
        """
        x1, y1 = self.location
        x2, y2 = other.location
        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        return distance

    def calc_neighbors(self, others, r):
        neighbors = []
        for other in others:
            distance = self.distance_to(other)
            if 0 < distance <= r:
                neighbors.append((other, distance))

        return neighbors

    def add_neighbors(self, neighbor_vertex, connected_link):
        self.neighbors[neighbor_vertex] = connected_link



class Link:
    """ this class represent a link in the network """

    def __init__(self, Lid, vertex1: Vertex = None, vertex2: Vertex = None, LagrangianMultiplier=0.5, distance=None):
        self.Lid = Lid
        self.connected_vertices = (vertex1, vertex2)
        self.distance = distance
        self.LagrangianMultiplier = LagrangianMultiplier
        self.gain = self.calculate_gain()
        self.power = self.calculate_link_power()
        self.interference_gain = self.calculate_interference_gain()
        self.interference_power = 0
        self.total_capacity = self.calculate_capacity()
        self.channels_capacities = [self.total_capacity / K for _ in range(K)]
        self.weight = self.calculate_link_weight()


    def __str__(self):
        return str(self.Lid)

    def calculate_gain(self):
        distance = self.distance
        path_loss_db = calculate_path_loss(distance)
        fading_coefficient = rayleigh_fading()
        attenuation_factor = 10 ** (path_loss_db / 10)
        gain = attenuation_factor * fading_coefficient
        return gain

    def calculate_interference_gain(self):
        distance = self.distance
        path_loss_db = calculate_path_loss(distance)
        fading_coefficient = rayleigh_fading()
        attenuation_factor = 10 ** (path_loss_db / 10)
        gain = attenuation_factor * fading_coefficient*1e-23
        return gain

    def calculate_link_power(self):
        min_vertex_power = min(self.connected_vertices[0].power, self.connected_vertices[1].power)
        power = min_vertex_power * (self.gain ** 2)
        return power

    def calculate_capacity(self):
        bw = min(self.connected_vertices[0].bw, self.connected_vertices[1].bw)
        noise_power = K_B * T * bw
        SINR = self.power / (noise_power + self.interference_power)  # Simplified SINR calculation
        capacity = bw * math.log2(1 + SINR)
        if capacity <= 0:
            raise ValueError(f"Invalid capacity {capacity} for link {self.Lid}. Capacity must be greater than zero.")
        return capacity

    def calculate_link_weight(self):
        if self.total_capacity == 0:
            return float('inf')
        return 1 / self.total_capacity

    def update_total_capacity(self):
        self.total_capacity = sum(self.channels_capacities)

class User:
    def __init__(self, Uid, links=[], startVertex=None, endVertex=None, rate=0.001):
        self.Uid = Uid
        self.links = links
        self.defualtLinks = []
        self.rate = rate
        self.startVertex = startVertex
        self.endVertex = endVertex
        self.flows = []

    def __str__(self):
        string = f"\nUser({self.Uid}) connect {self.startVertex.Vid} to {self.endVertex.Vid} through: "
        for link in self.links:
            string += f"{link} "
        string += f", and sends {len(self.flows)} flow with {sum(flow.data_amount for flow in self.flows)} data"
        return string

    def add_flow(self,flow):
        self.flows.append(flow)
        

class Flow:
    def __init__(self, source=None, destination=None, data_amount=0, rate=0):
        self.source = source
        self.destination = destination
        self.data_amount = data_amount
        self.generate_flow()
        self.rate_by_links = {}
        self.rate = rate
        self.channel = random.randint(0, K-1)

    def __str__(self):
        string = f"{self.source} send to {self.destination} {self.data_amount}"
        return string

    def generate_flow(self):
        """Generates F random information flows."""
        source, destination = random.sample(range(1, N + 1), 2)
        data_amount = random.randint(1, FLOW_MAX_DATA)  # random data amount between 1 and 1000 units
        self.source = self.source or source
        self.destination = self.destination or destination
        self.data_amount = self.data_amount or data_amount

    def set_rate_2_min_of_rate_by_links(self):
        self.rate = min(self.rate_by_links.values())


class Network:
    """this class represent a network"""

    def __init__(self, num_of_users=N, radius=M, neighbors_radius=R, create_network_type="Random"):
        self.num_of_users = num_of_users
        self.radius = radius
        self.neighbors_radius = neighbors_radius
        self.users = []
        self.links = []
        self.vertices = []
        self.cluster = []
        self.flows = []
        self.PtUpLink = 24e-3
        self.PtDownLink = 46e-3
        self.systemBandwidth = 20e6
        self.network_type = create_network_type
        if create_network_type == "Random":
            self.create_network()
            self.generate_random_flows_and_users()
            self.calculate_interference_power()
        elif create_network_type == "NUM":
            self.create_NUM_network()
        else:
            raise ValueError(f"no network of type {create_network_type}, only: Random, NUM")

    def __str__(self):
        string_to_print = ""
        vertices_to_print = self.vertices
        string_to_print += f"\n{self.network_type} network general params:\n"
        string_to_print += f"num of users= {self.num_of_users}, network radius= {self.radius}, neighbors radius={self.neighbors_radius}\n"
        string_to_print += f"\nUSERS:"
        for user in self.users:
            string_to_print += f"{user}"
        string_to_print += f"\n\nFLOWS:\n"
        for flow in self.flows:
            string_to_print += f"{flow}\n"
        return string_to_print

    def create_NUM_network(self):
        previous_vertex = None
        for i in range(self.num_of_users):
            new_vertex = self.create_new_vertex(i)
            if previous_vertex is not None:  # If there's a previous vertex, connect it to the current one
                distance = previous_vertex.distance_to(new_vertex)
                new_link = self.create_new_link(previous_vertex, new_vertex, distance)
                self.create_neighbors(previous_vertex, new_vertex, new_link)
            previous_vertex = new_vertex
        self.generate_flows_and_users_NUM()
        for link in self.links :
            link.total_capacity = 1

    
    def create_network(self):
        for i in range(self.num_of_users):
            self.create_new_vertex(i)
        for vertex in self.vertices:
            neighbors = vertex.calc_neighbors(self.vertices, self.neighbors_radius)
            for neighbor in neighbors:
                if neighbor[0] in vertex.neighbors:
                    continue
                link = self.create_new_link(vertex, neighbor[0], neighbor[1])
                self.create_neighbors(vertex, neighbor[0], link)

        if not self.check_network_connectivity():
            global R
            R += 1
            self.initial_network()
    

    def initial_network(self):
        self.neighbors_radius = R
        self.links = []
        self.vertices = []
        self.users = []
        self.create_network()

    def initial_users_rates(self):
        for user in self.users:
            user.rate = 0.001

    def initial_users(self):
        self.initial_users_rates()
        for user in self.users:
            user.links = user.defualtLinks

    def check_network_connectivity(self):
        remaining_vertices = self.vertices.copy()
        current_vertex = remaining_vertices[0]
        remaining_vertices = self.delete_neighbors(current_vertex, remaining_vertices)

        return remaining_vertices == []

    def delete_neighbors(self, vertex, remaining_vertices):
        remaining_vertices.remove(vertex)
        for neighbor in vertex.neighbors.keys():
            if neighbor not in remaining_vertices:
                continue
            self.delete_neighbors(neighbor, remaining_vertices)
        return remaining_vertices

    def calculateUserLinks(self, vertex, destVertex, visited=None):
        links = []
        if visited is None:
            visited = []
        visited.append(vertex)
        if destVertex in vertex.neighbors:
            links.append(vertex.neighbors[destVertex])
        else:
            for neighbor in vertex.neighbors:
                if neighbor in visited:
                    continue
                sub_links = self.calculateUserLinks(neighbor, destVertex, visited)
                if sub_links:
                    links.append(vertex.neighbors[neighbor])
                    links.extend(sub_links)
                    break
        return links

    def get_active_links(self):
        active_links = set()  # Use a set to avoid duplicates

        # Loop through all users to check their links
        for user in self.users:
            for link in user.links:
                active_links.add(link)  # Add each link to the set

        return list(active_links)

    def create_new_user(self, start_vertex, end_vertex):
        if start_vertex == end_vertex:
            raise ValueError(f"start vertex {start_vertex} cant be equal to end vertex {end_vertex}")
        userLinks = self.calculateUserLinks(start_vertex, end_vertex)
        Uid = len(self.users)+1
        user = User(Uid, links=userLinks, startVertex=start_vertex, endVertex=end_vertex)
        user.defualtLinks = userLinks
        self.users.append(user)
        return user

    def create_new_vertex(self, id):
        new_vertex = Vertex(Vid=id + 1)
        self.power_allocation(new_vertex)
        self.bw_aloocation(new_vertex)
        self.vertices.append(new_vertex)
        return new_vertex

    def create_new_link(self, vertex1, vertex2, distance):
        new_link = Link(Lid=f"{vertex1.Vid}-{vertex2.Vid}", vertex1=vertex1, vertex2=vertex2,
                        distance=distance)
        self.links.append(new_link)
        return new_link

    def create_neighbors(self, vertex1, vertex2, link):
        vertex1.add_neighbors(vertex2, link)
        vertex2.add_neighbors(vertex1, link)

    def sort_links_by_distance(self):
        self.links.sort(key=lambda x: x.distance)

    def power_allocation(self, vertex):  # TODO: maybe do a more sophisticated power allocation
        vertex.power = CONSTANT_POWER

    def bw_aloocation(self, vertex):  # TODO: maybe do a more sophisticated bw allocation
        vertex.bw = CONSTANT_BW

    def get_user(self, start_vertex, end_vertex):
        users = [user for user in self.users if user.startVertex == start_vertex and user.endVertex == end_vertex]
        if len(users) > 1:
            raise ValueError(f"there is unique user connect 2 vertex but got {len(users)} for vertx {start_vertex.Vid}")
        return users[0] if users else None

    def get_vertex(self, Vid):
        """Retrieve a vertex by its Vid."""
        for vertex in self.vertices:
            if vertex.Vid == Vid:
                return vertex
        raise ValueError(f"No vertex found with Vid {Vid}. vertices are from 1 to {N}")

    def create_Flow_and_User(self, idx1=None, idx2=None):
        flow = Flow(source=idx1, destination=idx2)
        source = self.get_vertex(flow.source)
        dest = self.get_vertex(flow.destination)
        self.flows.append(flow)
        user = self.get_user(source, dest) or self.create_new_user(source, dest)
        user.add_flow(flow)

    def generate_flows_and_users_NUM(self):
        self.flows, self.users = [], []

        # Connect first vertex to the last
        self.create_Flow_and_User(1, len(self.vertices)) # Assume min(Vid) == 1, there is no Vid == 0

        for i in range(1, len(self.vertices)):  # Connect each vertex to his follower expect for the first
            self.create_Flow_and_User(i, i+1)

    def generate_random_flows_and_users(self):
        self.flows, self.users = [], []
        for _ in range(F):
            self.create_Flow_and_User()

    def draw_network(self):
        fig, ax = plt.subplots()

        for vertex in self.vertices:
            x, y = vertex.location
            ax.plot(x, y, 'o', label=f'Vertex {vertex.Vid}')
            ax.text(x, y, f' {vertex.Vid}', verticalalignment='bottom', horizontalalignment='right')

        # Draw links
        for link in self.links:
            v1, v2 = link.connected_vertices
            x_values = [v1.location[0], v2.location[0]]
            y_values = [v1.location[1], v2.location[1]]
            ax.plot(x_values, y_values, 'k-', linewidth=0.5)  # 'k-' for black line

        ax.set_aspect('equal', 'box')
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')
        plt.title(f'{self.network_type} Network Visualization')
        plt.show(block=False)

    def update_network_paths_using_Dijkstra(self, debug_prints=False):
        """Updates shortest paths for all vertices using Dijkstra's algorithm."""
        for v in self.vertices:
            v.ShortestPath = {}
        for start_vertex in self.vertices:
            distances, previous_nodes = dijkstra_algorithm(self, start_vertex)#####################################
            for vertex in self.vertices:
                user = self.get_user(start_vertex, vertex)
                path, link_path = [], []
                current = vertex
                while current != start_vertex:
                    if current is None:
                        path, link_path = [], []
                        break
                    next_vertex = previous_nodes[current]
                    connected_link = current.neighbors[next_vertex]
                    link_path.append(connected_link)
                    path.append(current)
                    current = next_vertex
                path.reverse()
                link_path.reverse()
                start_vertex.ShortestPath[vertex] = path
                if user is not None:
                    if debug_prints and user.links != link_path:
                        print(f"\nupdate user({user.Uid}) links:")
                        print("from:", *[str(vertex) for vertex in user.links])
                        print("to  :", *[str(vertex) for vertex in link_path])
                    user.links = link_path

    def update_network_paths_using_bellman_ford(self, debug_prints=False):
        """Updates shortest paths for all vertices using Dijkstra's algorithm."""
        for v in self.vertices:
            v.ShortestPath = {}
        for start_vertex in self.vertices:
            distances, previous_nodes = bellman_ford_algorithm(self, start_vertex)#####################################
            for vertex in self.vertices:
                user = self.get_user(start_vertex, vertex)
                path, link_path = [], []
                current = vertex
                while current != start_vertex:
                    if current is None:
                        path, link_path = [], []
                        break
                    next_vertex = previous_nodes[current]
                    connected_link = current.neighbors[next_vertex]
                    link_path.append(connected_link)
                    path.append(current)
                    current = next_vertex
                path.reverse()
                link_path.reverse()
                start_vertex.ShortestPath[vertex] = path
                if user is not None:
                    if debug_prints and user.links != link_path:
                        print(f"\nupdate user({user.Uid}) links:")
                        print("from:", *[str(vertex) for vertex in user.links])
                        print("to  :", *[str(vertex) for vertex in link_path])
                    user.links = link_path


    def calculate_interference_power(self):
        if not calc_inter_face:
            return
        active_links = set()
        for user in self.users:
            for link in user.links:
                active_links.add(link)
        for link in self.links:
            total_interference_power = 0
            for other_link in self.links:
                if other_link == link or other_link not in active_links:
                    continue

                interference_contribution = other_link.power * other_link.interference_gain
                total_interference_power += interference_contribution

            link.interference_power = total_interference_power
            link.total_capacity = link.calculate_capacity()


def num(alpha,num_of_users=N, radius=M, neighbors_radius=R,Algo="Primal" ):
    #primal algorithm
    #alpha = 1
    set_global_params( n=num_of_users, m=radius, r=neighbors_radius, f=None)
    calc_inter_face = False
    network = Network(num_of_users, radius, neighbors_radius,create_network_type="NUM")
    network.draw_network()
    print(network)
    CalcNetworkRate(network, alpha, Algo)
    plt.show()  # to stop the code so we can analyze the graph showing the rates



# <h2>question 5- primal algoritem with Dijkatra

def dijkastra(alpha,num_of_users=N, radius=M, neighbors_radius=R,Algo="Primal"):
    calc_inter_face = False
    network = Network(num_of_users, radius, neighbors_radius,create_network_type="NUM")
    network.draw_network()
    print(f'\nResult before Dijkstra\n')
    CalcNetworkRate(network, alpha, Algo)
    print(f'\nResult after Dijkstra\n')
    network.update_network_paths_using_Dijkstra()
    CalcNetworkRate(network, alpha, Algo)
    plt.show()

# <h2>question 6- primal algoritem with bellman ford

def bellman_ford(alpha,num_of_users=N, radius=M, neighbors_radius=R,Algo="Primal"):
    calc_inter_face = False
    network = Network(num_of_users, radius, neighbors_radius,create_network_type="NUM")
    network.draw_network()
    print(f'\nResult before bellman ford\n')
    CalcNetworkRate(network, alpha, Algo)
    print(f'\nResult after bellman ford\n')
    network.update_network_paths_using_bellman_ford()
    CalcNetworkRate(network, alpha, Algo)
    plt.show()


