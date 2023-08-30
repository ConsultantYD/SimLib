# type: ignore
# flake8: noqa
from graphviz import Digraph


class Node:
    def __init__(self, state, reward=0):
        self.state = state
        self.reward = reward
        self.children = {}  # {action: [(probability, Node)]}

    def add_child(self, action, child_node, probability):
        if action not in self.children:
            self.children[action] = []

        self.children[action].append((probability, child_node))

    def get_child(self, action):
        return self.children.get(action, [])

    def __str__(self):
        return f"State: {self.state}, Reward: {self.reward}"


class ScenarioTree:
    def __init__(self, initial_state):
        self.root = Node(initial_state)

    def find_node(self, node, state_to_find):
        """Helper function to search for a node recursively."""
        if node.state == state_to_find:
            return node
        for _, children in node.children.items():
            for _, child in children:
                found_node = self.find_node(child, state_to_find)
                if found_node:
                    return found_node
        return None

    def insert(
        self, current_state, action, next_states, rewards, probabilities
    ):
        """Inserts possible states and their probabilities for a given action."""
        if len(next_states) != len(rewards) or len(next_states) != len(
            probabilities
        ):
            raise ValueError(
                "next_states, rewards, and probabilities lists should have the same length"
            )

        current = self.find_node(self.root, current_state)
        if current is None:
            raise ValueError("Specified current_state not found in the tree")

        for i in range(len(next_states)):
            # Check if the child state node already exists
            child = self.find_node(self.root, next_states[i])
            if child is None:
                child = Node(next_states[i], rewards[i])

            current.add_child(action, child, probabilities[i])

    def optimal_path(self, node=None, accumulated_reward=0):
        """Finds the optimal path in the tree with the maximum reward using depth-first search."""
        if node is None:
            node = self.root

        if not node.children:  # if the node is a leaf
            return accumulated_reward, [node.state]

        # Recurse on the children
        best_reward = float("-inf")
        best_path = []

        for action, children in node.children.items():
            for probability, child in children:
                adjusted_reward = (
                    child.reward * probability
                )  # Weight by probability
                reward, path = self.optimal_path(
                    child, accumulated_reward + adjusted_reward
                )
                if reward > best_reward:
                    best_reward = reward
                    best_path = [node.state] + path

        return best_reward, best_path

    def to_graphviz(self, filename="tree", highlight_optimal=True):
        """Converts the scenario tree to a Graphviz dot representation and renders it."""

        dot = Digraph(comment="Scenario Tree")

        optimal_states = []
        optimal_actions = set()
        if highlight_optimal:
            _, optimal_states = self.optimal_path()

            # Determine optimal actions based on the optimal states
            for i in range(len(optimal_states) - 1):
                current_state = optimal_states[i]
                next_state = optimal_states[i + 1]
                current_node = self.find_node(self.root, current_state)

                for action, children in current_node.children.items():
                    for probability, child in children:
                        if child.state == next_state:
                            optimal_actions.add((current_state, action))

        # Recursive helper function to add nodes and edges
        def add_nodes_edges(node):
            node_name = str(id(node))
            color = "red" if node.state in optimal_states else "lightgrey"

            dot.node(
                node_name,
                f"{node.state}\nReward: {node.reward}",
                color=color,
                style="filled",
            )

            for action, children in node.children.items():
                action_node_name = f"{node_name}_{action}"
                dot.node(action_node_name, action, color="black", shape="box")

                # Adjust edge color based on whether the (state, action) pair is part of the optimal path
                edge_color = (
                    "red"
                    if (node.state, action) in optimal_actions
                    else "black"
                )
                dot.edge(
                    node_name, action_node_name, label="", color=edge_color
                )

                for probability, child in children:
                    child_name = str(id(child))
                    edge_color = (
                        "red"
                        if node.state in optimal_states
                        and child.state in optimal_states
                        else "black"
                    )
                    dot.edge(
                        action_node_name,
                        child_name,
                        label=f"{probability:.2f}",
                        color=edge_color,
                    )
                    add_nodes_edges(child)

        add_nodes_edges(self.root)
        dot.render(filename, view=True)

    def __str__(self, node=None, prefix="", tree_str=[]):
        """Recursive method to print the tree."""
        if node is None:
            node = self.root

        tree_str.append(f"{prefix}{node}")

        for action, children in node.children.items():
            for probability, child in children:
                tree_str = self.__str__(
                    child,
                    prefix + f"--{action}[{probability:.2f}]-->",
                    tree_str,
                )

        return tree_str

    def display(self):
        for line in self.__str__():
            print(line)


# Example usage:
# TODO: Ensure sum of probabilities = 1 from a given action
tree = ScenarioTree("initial")
tree.insert("initial", "action1", ["state1", "state2"], [5, 10], [0.8, 0.2])
tree.insert("state1", "action2", ["state3", "state4"], [15, 20], [0.7, 0.3])
tree.insert("state1", "action3", ["state3", "state4"], [15, 20], [0.7, 0.3])
tree.insert("state2", "action3", ["state5", "state6"], [15, 20], [0.5, 0.5])
tree.insert("state5", "action4", ["state7"], [100], [0.01])
tree.to_graphviz()
