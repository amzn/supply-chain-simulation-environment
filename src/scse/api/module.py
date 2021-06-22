import abc


class Module(abc.ABC):
    """
    The unit of pluggability for miniSCOT is a called an 'module'.

    In Python, an agent module is implemented by means of a Python module
    containing a Python class that implements the Agent protocol, as defined here.
    """
    @abc.abstractmethod
    def __init__(self, config):
        """
        Agents are initialized with a config `dict`.
        """
    @abc.abstractmethod
    def get_name(self):
        """
        Return the Agent's unique name.
        """


class Env(Module):
    """
    Env provide (static) context and the initial values of the state
    """
    def get_context(self):
        """
        Return module's contribution to the environment's static context or None.
        """
        return None

    def get_initial_state(self, context):
        """
        Return module's contribution to the environment's initial state or None.
        """
        return None

class Service(Module):

    def reset(self, context):
        """
        Reset any internal state and/or variables.
        `context` provides static information about the environment.
        """

class Agent(Module):
    """
    Agents provide actions as they react to state changes in the Environment.
    """
    def reset(self, context, state):
        """
        Reset any internal state and/or variables.
        `context` provides static information about the environment.
        `state` provides the initial state of the environment.
        """

    def compute_actions(self, state):
        """
        Compute new actions taken by the Agent given the most recent `state`.

        `state` are values and deterministically define the Environment
        (hosting the agent). `state` is mutable, but can only be changed by the
        Environment as the Environment reacts to actions returned by Agents.

        Note that as `context` hasn't changed since `reset()`, it is therefore
        not provided again as an argument.

        Return a list of actions, or an empty list if no actions are to be taken.

        """
        return []
