"""
Author: Max Bronckers

This class will host any non-GPy models that are used to fit to the data resulting from our simulations:
- X0: number of batteries in grid
- X1: number of time steps in simulation?
- Y: miniSCOT reward function value

The models need to implement the IModel interface for Emukit to work.

Note: GPy models have a wrapper implemented already --> see emukit.model_wrappers
"""

from emukit.core.interfaces import IModel
import numpy as np

class SklearnGPModel(IModel):
    """ Example class using Sklearn GP """
    def __init__(self, sklearn_model):
        self.model = sklearn_model

    def predict(self, X):
        mean, std = self.model.predict(X, return_std=True)
        return mean[:, None], np.square(std)[:, None]

    def set_data(self, X: np.ndarray, Y: np.ndarray) -> None:
        self.model.fit(X, Y)

    def optimize(self, verbose: bool = False) -> None:
        # There is no separate optimization routine for sklearn models
        pass

    @property
    def X(self) -> np.ndarray:
        return self.model.X_train_

    @property
    def Y(self) -> np.ndarray:
        return self.model.y_train_
