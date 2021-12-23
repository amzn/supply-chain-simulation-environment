# Decision loops
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
from scse.api.simulation import run_simulation

"""
Author: Max Bronckers

This class will host the vars and functions to initialize the Bayesian Optimization loop.
"""

class ExperimentLoop:
    def __init__(self, name, f) -> None:
        pass
        self.name = name
        self.f = f
        self.parameter_space: ParameterSpace = None
        self.model: IModel = None
        self.acquisition_func = None


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

def main():

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
    new_X, new_Y = (list(t) for t in zip(*sorted(zip(bayesopt_loop.loop_state.X,bayesopt_loop.loop_state.Y))))
    print(max(new_Y))

if __name__ == "__main__":
    main()