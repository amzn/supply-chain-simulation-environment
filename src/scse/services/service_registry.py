"""Modules must not interact directly with other modules, because otherwise it
becomes very hard to replace, add, remove Modules and not break everything in
the process.

Instead, Modules must either communicate through the state, action, reward
triad or by explicitly registering and consuming services from the service registry.

The latter approach allows the framework to keep track of what is being used by
whom and thus manage the execution of the Modules with the right service
dependencies.

Contrast this by having the Buying module explicitly import the
Poisson-implementation of Demand Forecasting; then if one wants to try out with
a different implementation of Demand Forecasting, one would need to change both
the Buying and the Forecasting modules in spite of the interface not having
changed.

"""

"""
ServiceRegistry implemented as a simple dictionary.

TODO As the number of Modules and Services grow, we should change this to keep
 explicit track of consumers and producers.
"""
import os
import importlib
import inspect

class ServiceRegistry:
    def __init__(self):
        self._registry = [os.path.splitext(filename)[0] for filename in os.listdir() if os.path.splitext(filename)[1] == '.py' and filename not in ['__init__.py']]
        self._signed_in_services = {}

    def list_available_services(self):
        return self._registry

    def load_service(self, service_name, run_parameters):
        # if the service has already been initialized, we want to return the same instance of the service
        if service_name in self._signed_in_services:
            service_instance = self._signed_in_services[service_name]
        else:
            _DEFAULT_SERVICES_PATH = 'scse.services.'
            target_service_package = _DEFAULT_SERVICES_PATH+service_name
            current_service = importlib.import_module(target_service_package)
            class_to_return = []
            for name, obj in inspect.getmembers(current_service):
                if inspect.isclass(obj) and name not in ['Service', 'datetime', 'timedelta']:
                    class_to_return.append(name)
            if len(class_to_return) != 1:
                raise ValueError("Tried to load service without exactly one class")
            else:
                service_class = getattr(current_service, class_to_return[0])
                service_instance = service_class(run_parameters)
                self._signed_in_services[service_name] = service_instance

        return service_instance

    def reset_signed_in_services(self, context):
        for service_name in self._signed_in_services:
            self._signed_in_services[service_name].reset(context)
"""
Singleton Service Registry
"""
singleton = ServiceRegistry()
