"""
Naive Supply Chain environment/controller.
"""

import logging
import networkx as nx
import datetime
import time
from scse.api.module import Agent
from scse.api.module import Env
from scse.utils.printer import red
from scse.utils.uuid import short_uuid
from scse.services.service_registry import singleton as registry
from scse.profiles.profile import load_profile, instantiate_class

# TODO Right now, let's log all by setting DEBUG at the root level...
# Later remove and let it be configured.
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class SupplyChainEnvironment:

    # Rather than using a dict, let's expand the arguments to keywords.
    # This makes it easier to document and to establish default values.
    # We should also consider if it is worthwhile to move any of the
    #  'run parameters' to be specified directly in the profiles.
    # The trade-off is that profile values are not meant to change (per run).
    def __init__(self,
                 profile = 'newsvendor_demo_profile',       # defines the set of modules to use
                 simulation_seed = 12345,   # controls randomness throughout simulation
                 start_date = '2019-01-01', # simulation start date
                 time_increment = 'daily',  # timestep increment
                 time_horizon = 100,        # timestep horizon
                 asin_selection = 1):       # how many / which asins to simulate

        self._program_start_time = time.time()
        self._miniscot_time_profile = {}

        self._start_date = start_date
        self._time_increment = time_increment
        self._time_horizon = time_horizon

        profile_config = load_profile(profile)

        # Invariant: order should not be relevant.
        self._metrics = [instantiate_class(class_name,
                                           simulation_seed = simulation_seed,
                                           start_date = start_date,
                                           time_increment = time_increment,
                                           time_horizon = time_horizon,
                                           asin_selection = asin_selection)
                         for class_name in profile_config['metrics']]

        # TODO For now, only a single metric module is supported.
        if len(self._metrics) != 1:
            raise ValueError("miniSCOT supports only a single metric. " +
                             "{} were specified.".format(len(self._metrics)))
        self._metrics = self._metrics[0]

        self._modules = [instantiate_class(class_name,
                                           simulation_seed = simulation_seed,
                                           start_date = start_date,
                                           time_increment = time_increment,
                                           time_horizon = time_horizon,
                                           asin_selection = asin_selection)
                         for class_name in profile_config['modules']]

        current_program_time = time.time()
        self._miniscot_time_profile['miniscot_init'] = current_program_time - self._program_start_time

    def get_initial_env_values(self):
        module_start_time = time.time()
        self._context = {}
        context = {}
        state = {}
        state['clock'] = 0
        start_year = int(self._start_date[0:4])
        start_month = int(self._start_date[5:7])
        start_day = int(self._start_date[-2:])
        state['date_time'] = datetime.datetime(start_year, start_month, start_day)
        self.episode_reward = 0

        # TODO Should we treat this as context or state?
        state['customer_orders'] = []
        state['purchase_orders'] = []

        # The final Env is made of contributions from Env-modules. Each
        # Env-module can provide (static) context and the initial values for
        # the (dynamic) state. As the initial state may depend on info from the
        # context, we first collect the latter and then collect the former
        # (passing the latter as argument).
        for module in self._modules:
            if isinstance(module, Env):
                logger.debug("Getting context from Env: {}.".format(
                    module.get_name()))

                module_context = module.get_context()
                if module_context:
                    context[module.get_name()] = module_context
                    self._context[module.get_name()] = module_context

        for module in self._modules:
            if isinstance(module, Env):
                logger.debug("Getting initial state from Env: {}.".format(
                    module.get_name()))

                module_state = module.get_initial_state(context)
                if module_state:
                    state[module.get_name()] = module_state

        module_end_time = time.time()
        self._miniscot_time_profile['initial_env_values'] = module_end_time - module_start_time

        return context, state

    def reset_agents(self, context, state):
        # Reset all agents
        # Do not use comprehensions to make it explicit that we are mutating variables
        # Invariant: run_parameters do not change across resets; if they were to change, we should
        #  handle them as a parameter to reset() instead of passing them along to __init__
        for module in self._modules:
            if isinstance(module, Agent):
                module_start_time = time.time()

                logger.debug("Resetting Agent: {}.".format(module.get_name()))

                module_state = module.reset(context, state)
                if module_state:
                    state[module.get_name()] = module_state

                module_end_time = time.time()
                self._miniscot_time_profile[module.get_name()+" reset"] = module_end_time - module_start_time
                self._miniscot_time_profile[module.get_name()+" compute_actions"] = 0
        self._metrics.reset(context, state)
        logger.debug("trying to reset signed-in services")
        registry.reset_signed_in_services(context)

        self._miniscot_time_profile["miniscot_action_execution"] = 0
        self._miniscot_time_profile["miniscot_advance_time"] = 0
        self._miniscot_time_profile["miniscot_metrics_time"] = 0


    def step(self, state, actions):
        # TODO we should clone the state to make clear that it must NOT be
        # modified by the modules directly. Not sure yet if info should likewise be immutable.
        state = self._transfer_shipments(state)
        timestep_reward = 0
        timestep_reward_by_asin = {k:0 for k in self._context['asin_list']}
        for module in self._modules:
            if isinstance(module, Agent):
                module_start_time = time.time()
                logger.debug("Getting actions from Agent: {}." .format(module.get_name()))
                actions.extend(module.compute_actions(state))
                module_end_time = time.time()
                self._miniscot_time_profile[module.get_name()+" compute_actions"] += module_end_time - module_start_time
                
                miniscot_execute_actions_start_time = time.time()
                state, actions, reward = self._execute_actions(actions, state)
                miniscot_execute_actions_end_time = time.time()
                self._miniscot_time_profile["miniscot_action_execution"] += miniscot_execute_actions_end_time - miniscot_execute_actions_start_time

                timestep_reward_by_asin = {k: timestep_reward_by_asin.get(k, 0) + reward['by_asin'].get(k, 0) for k in set(timestep_reward_by_asin)}
                timestep_reward += reward['total']

        # Invariant: only the following statements below are allowed to update the state.

        # Actions will typically create entities in the state space.
        # Next, we must update these entities to account for the movement of time.
        # When we are done, the clock is updated to the next time-step.
        miniscot_advance_time_start_time = time.time()
        state, reward = self._advance_time(state)
        miniscot_advance_time_end_time = time.time()
        self._miniscot_time_profile["miniscot_advance_time"] += miniscot_advance_time_end_time - miniscot_advance_time_start_time
        if state['clock'] == self._time_horizon:
            program_end_time = time.time()
            total_measured_time = sum(self._miniscot_time_profile.values())
            self._miniscot_time_profile["total_measured_time"] = total_measured_time
            self._miniscot_time_profile["miniscot_total_time"] = program_end_time - self._program_start_time
            profile_time = str(self._miniscot_time_profile)
            logger.info("Measured simulation time: {}".format(profile_time))


        timestep_reward += reward['total']
        timestep_reward_by_asin = {k: timestep_reward_by_asin.get(k, 0) + reward['by_asin'].get(k, 0) for k in set(timestep_reward_by_asin)}
        self.episode_reward += timestep_reward
        
        logger.info(red("timestep is = " + str(state['clock'])))
        logger.info(red("datetime is = " + str(state['date_time'])))
        logger.info(red("Timestep Reward = " + str(timestep_reward)))
        logger.info(red("Episode Reward = " +str(self.episode_reward)))

        rewards = {}
        rewards["timestep_reward"] = {}
        rewards["episode_reward"] = {}

        rewards["timestep_reward"]["total"] = timestep_reward
        rewards["timestep_reward"]["by_asin"] = timestep_reward_by_asin
        rewards["episode_reward"]["total"] = self.episode_reward

        return state, actions, rewards

    def _execute_actions(self, actions, state):
        # Execute all completed actions that are scheduled for this timestep
        unexecuted_actions = []
        reward = 0
        reward_by_asin = {k:0 for k in self._context['asin_list']}
        for action in actions:
            if action['quantity'] < 0:
                raise ValueError ("Action quantity is negative, which is not possible!")
            if isinstance(action['quantity'], int) == False:
                raise ValueError ("Action quantity is not integer, which is not possible!")
            if action['schedule'] <= state['clock']:
                if action['type'] in ['purchase_order', 'customer_order']:
                    state = self._create_order_entity(state, action)
                # we only compute rewards upon executing complete action forms
                elif action['type'] in ['inbound_shipment', 'outbound_shipment', 'transfer']:
                    state = self._create_shipment_entity(state, action)
                    metrics_start_time = time.time()
                    action_reward = self._metrics.compute_reward(state, action)
                    metrics_end_time = time.time()
                    self._miniscot_time_profile["miniscot_metrics_time"] += metrics_end_time - metrics_start_time
                    reward += action_reward
                    reward_by_asin[action['asin']] += action_reward
                else:
                    raise ValueError("Unknown action type ".format(action['type']))
            else:
                unexecuted_actions.append(action)

        # this allows us to return rewards by asin, instead of just total reward
        rewards = {}
        rewards["total"] = reward
        rewards["by_asin"] = reward_by_asin

        return state, unexecuted_actions, rewards

    def _advance_time(self, state):
        # Right now, the only time processing we need to do is with shipments.
        reward = 0
        action = {"type": "advance_time", "asin": None, "quantity": None}
        reward = self._metrics.compute_reward(state, action)
        state['clock'] += 1
        logger.debug('clock: {}'.format(state['clock']))
        if self._time_increment == 'daily':
            state['date_time'] += datetime.timedelta(days=1)
        elif self._time_increment == 'hourly':
            state['date_time'] += datetime.timedelta(hours=1)
        else:
            raise ValueError("Unknown time increment arg".format(self._time_increment))

        return state, reward

    def _create_order_entity(self, state, action):
        # semantically, individual actions are singular (order, shipment), state semantics are plural (orders, shipments)
        atype_to_state = action['type']+'s'
        # this could be creating a brand new order, or updating an order w/out turning it into a shipment
        # so, if the uuid already exists, we'll remove the old order; otherwise generate new uuid.
        state, action = self._remove_order_entity(state, action)      
        # either way, append new order to state
        state[atype_to_state].append(action)

        return state

    def _create_shipment_entity(self, state, action):
        atype = action['type']
        asin = action['asin']
        origin = action['origin']
        destination = action['destination']
        quantity = action['quantity']
        # If there's already a uuid, then the action is completing an existing order
        # Therefore, remove the order from the state, as we transform order into shipment
        state, action = self._remove_order_entity(state, action)
        uuid = action['uuid']

        G = state['network']
        
        origin_data = G.nodes[origin]
        destination_data = G.nodes[destination]

        logger.debug("Creating shipment at origin {} and destination {}.".format(origin, destination))
        edge_data = G.get_edge_data(origin, destination)

        # Update only after the other components have been retrieved to avoid
        # chances of corruption.
        # assert origin_data["inventory"][asin] >= quantity
        # vendors may not have a notion of inventory (e.g. maybe just confirmation rate)
        if 'inventory' in origin_data:
            if quantity <= origin_data['inventory'][asin]:
                origin_data['inventory'][asin] -= quantity
            else:
                raise ValueError("Action tried to transfer {} units of {} from {} to {}, but {} only had {} units of inventory for this ASIN!".format(quantity, asin, origin, destination, origin, origin_data['inventory'][asin]))

        shipments = edge_data['shipments']
        transit_time = edge_data['transit_time']

        shipment = {
            'id': uuid,
            'asin': asin,
            'origin': origin,
            'destination': destination,
            'quantity': quantity,
            'time_until_arrival': transit_time
        }
        #logger.debug("edges are {}".format(G.edges(data=True)))
        #logger.debug("Creating shipment {}.".format(shipment))
        #logger.debug("Appending to shipments {} for edge_data {}".format(shipments, edge_data))


        shipments.append(shipment)

        return state

    def _remove_order_entity(self, state, action):
        if 'uuid' in action:
            uuid = action['uuid']
            for order in state['customer_orders']:
                if order['uuid'] == uuid:
                    state['customer_orders'].remove(order)
                    break
            for order in state['purchase_orders']:
                if order['uuid'] == uuid:
                    state['purchase_orders'].remove(order)
                    break
        else:
            action['uuid'] = short_uuid()

        return state, action


    def _transfer_shipments(self, state):
        G = state['network']
        logger.debug("edges are {}".format(G.edges(data=True)))

        for origin, destination, edge_data in G.edges(data=True):
            shipments = edge_data['shipments']
            logger.debug('For edge with origin {} and destination {}, edge data is {}'.format(origin, destination, edge_data))

            # Let's iterate in reverse so that we can remove elements as needed without causing skips
            for shipment in reversed(shipments):
                shipment['time_until_arrival'] -= 1
                logger.debug(
                    "Updated arrival time for shipment {}.".format(shipment))

                if shipment['time_until_arrival'] <= 0:
                    logger.debug(
                        "Shipment {} arrived at destination {}.".format(
                            shipment, destination))

                    destination_data = G.nodes[destination]

                    # If warehouse, then update inventory
                    inventory = destination_data.get('inventory')
                    if inventory:
                        inventory[shipment['asin']] += shipment['quantity']
                    else:
                        # Let's update a 'delivered' attribute so that we can debug it better.
                        destination_data['delivered'] += shipment['quantity']

                    shipments.remove(shipment)

        return (state)

    def run(self):
        logger.info("Simulation Started.")

        context, state = self.get_initial_env_values()

        self.reset_agents(context, state)

        # Invariant: cannot be executed in parallel
        actions = []
        for t in range(0, self._time_horizon):
            logger.info(red("timestep is = " + str(t)))
            logger.info(red("datetime is = " + str(state['date_time'])))
            state, actions, reward = self.step(state, actions)
            logger.info(red("Reward = " + str(reward["timestep_reward"]["total"])))
            logger.info(red("Episode Reward = " +str(self.episode_reward)))

        logger.info("Simulation Completed.")

        return state
