# Decision loops
from emukit.core.interfaces.models import IModel
from emukit.core.parameter_space import ParameterSpace
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


def main():
    loop = ExperimentLoop()

    # Function to estimate
    f = None # the API call to miniSCOT, which needs to be parsed

    # Initial design => initial set of batteries and associated reward of simulation

    X = None # inputs: num_batteries, time_steps in simulation, battery size?
    Y = None # reward metric

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
                                            space=loop.parameter_space,
                                            acquisition=expected_improvement,
                                            batch_size=batch_size)

    # Run the loop and extract the optimum;  we either complete 10 steps or converge
    max_iters = 10
    stopping_condition = FixedIterationsStoppingCondition(
        i_max=max_iters) | ConvergenceStoppingCondition(eps=0.01)

    bayesopt_loop.run_loop(loop.f, stopping_condition)

    # Visualize and get extrema
