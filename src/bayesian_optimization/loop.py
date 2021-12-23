# Decision loops
from scse.api.simulation import run_simulation
from emukit.core.interfaces.models import IModel
from emukit.core.parameter_space import ParameterSpace
from emukit.core import ParameterSpace, ContinuousParameter, DiscreteParameter
from emukit.core.initial_designs import RandomDesign

from emukit.experimental_design import ExperimentalDesignLoop
from emukit.bayesian_optimization.loops import BayesianOptimizationLoop
from emukit.quadrature.loop import VanillaBayesianQuadratureLoop

# Acquisition functions
from emukit.bayesian_optimization.acquisitions import ExpectedImprovement
from emukit.experimental_design.acquisitions import ModelVariance
from emukit.quadrature.acquisitions import IntegralVarianceReduction

# Acquistion optimizers
from emukit.core.optimization import GradientAcquisitionOptimizer

# Stopping conditions
from emukit.core.loop import FixedIterationsStoppingCondition
from emukit.core.loop import ConvergenceStoppingCondition

# Models
from emukit.model_wrappers import GPyModelWrapper
from GPy.models import GPRegression

import numpy as np
import logging
logging.basicConfig(level=logging.INFO)


# miniSCOT function

"""
Author: Max Bronckers

This class will host the vars and functions to initialize the Bayesian Optimization loop.
"""

_log = logging.getLogger(__name__)


class ExperimentLoop:
    def __init__(self, name, function, p_space: ParameterSpace, model: IModel, max_iters, batch_size) -> None:
        self.name = name
        self.f = function
        self.parameter_space: ParameterSpace = p_space

        self.model: IModel = model if model else None
        self.acquisition_func = None
        self.design = RandomDesign(self.parameter_space) if p_space else None

        self.bo_loop = None
        self.batch_size = batch_size
        self.max_iters = max_iters
        self.stopping_condition = FixedIterationsStoppingCondition(
            i_max=max_iters) | ConvergenceStoppingCondition(eps=0.01)

    def initial_design(self, num_data_points):
        _log.info("Obtaining {} sample points".format(num_data_points))
        # Initial set of batteries and associated reward of simulation
        self.X = self.design.get_samples(num_data_points)
        self.Y = self.f(self.X)

    def set_model(self, model: IModel):
        self.model = model

    def init_bo(self):
        _log.info("Initializing BO loop ...")
        # Load core elements for Bayesian optimization
        self.acquisition_func = ExpectedImprovement(model=self.model)
        self.optimizer = GradientAcquisitionOptimizer(
            space=self.parameter_space)

        # Create the Bayesian optimization object
        self.bo_loop = BayesianOptimizationLoop(model=self.model,
                                                space=self.parameter_space,
                                                acquisition=self.acquisition_func,
                                                batch_size=self.batch_size,
                                                acquisition_optimizer=self.optimizer)

    def run_bo(self):
        if not self.bo_loop:
            self.init_bo()

        self.bo_loop.run_loop(self.f, self.stopping_condition)


def f(X):
    """
    Handling API call to miniSCOT simulation given some inputs 

    X contains parameter configs x = [x0 x1 ...]
    - The order of parameters in x should follow the order specified in the parameter_space declaration 
    - E.g. here we specify num_batteries = x[0]

    """
    Y = []
    for x in X:
        num_batteries = x[0]

        cum_reward = run_simulation(
            time_horizon=336, num_batteries=num_batteries)

        Y.append(cum_reward[-1])

    Y = np.reshape(np.array(Y), (-1, 1))
    return Y


def example():
    # Specify parameter space
    max_num_batteries = 25
    num_batteries = DiscreteParameter(
        'num_batteries', [i for i in range(0, max_num_batteries)])
    week = 336
    time_horizon = DiscreteParameter(
        'time_horizon', [i for i in range(0, 52*week, week)])
    parameter_space = ParameterSpace([num_batteries])

    # Init loop
    loop = ExperimentLoop(name="Example",
                          function=f, p_space=parameter_space, model=None,
                          max_iters=10, batch_size=3)

    loop.initial_design(num_data_points=3)

    # Create emulator
    gpy_model = GPRegression(loop.X, loop.Y)
    gpy_model.optimize()
    model = GPyModelWrapper(gpy_model)

    loop.set_model(model)
    loop.init_bo()
    loop.run_bo()

    print("Loop finished")


def main():
    """
    This code explicitly shows the entire flow of the BO loop.
    """
    # Specify parameter space
    max_num_batteries = 25
    num_batteries = DiscreteParameter(
        'num_batteries', [i for i in range(0, max_num_batteries)])
    week = 336
    time_horizon = DiscreteParameter(
        'time_horizon', [i for i in range(0, 52*week, week)])
    parameter_space = ParameterSpace([num_batteries])
    design = RandomDesign(parameter_space)

    # Initial set of batteries and associated reward of simulation
    num_data_points = 2
    X = design.get_samples(num_data_points)
    Y = f(X)

    # emulator model
    gpy_model = GPRegression(X, Y)
    gpy_model.optimize()
    model_emukit = GPyModelWrapper(gpy_model)

    # Load core elements for Bayesian optimization
    expected_improvement = ExpectedImprovement(model=model_emukit)
    optimizer = GradientAcquisitionOptimizer(space=parameter_space)

    # Create the Bayesian optimization object
    batch_size = 1
    bayesopt_loop = BayesianOptimizationLoop(model=model_emukit,
                                             space=parameter_space,
                                             acquisition=expected_improvement,
                                             batch_size=batch_size)

    # Run the loop and extract the optimum;  we either complete 10 steps or converge
    max_iters = 1
    stopping_condition = FixedIterationsStoppingCondition(
        i_max=max_iters) | ConvergenceStoppingCondition(eps=0.01)

    bayesopt_loop.run_loop(f, stopping_condition)

    # Visualize and get extrema
    new_X, new_Y = bayesopt_loop.loop_state.X, bayesopt_loop.loop_state.Y


if __name__ == "__main__":
    example()
