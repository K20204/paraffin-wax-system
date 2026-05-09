import math
from abc import ABC, abstractmethod


class MixingModel(ABC):
    @abstractmethod
    def mix(self, values, weights):
        pass


class LinearMixingModel(MixingModel):
    def mix(self, values, weights):
        total = sum(weights)
        if total == 0:
            return 0
        return sum(w * v for w, v in zip(weights, values)) / total


class LogMixingModel(MixingModel):
    def mix(self, values, weights):
        total = sum(weights)
        if total == 0:
            return 0
        log_sum = sum(w * math.log(max(v, 1e-10)) for w, v in zip(weights, values))
        return math.exp(log_sum / total)


def get_model(name):
    models = {"linear": LinearMixingModel(), "logarithmic": LogMixingModel()}
    return models.get(name, LinearMixingModel())
