import docker
import logging

logger = logging.getLogger(__name__)

_DOCKER_API_VERSION = '1.24'
_INFERENCE_COMMAND = 'serve'
_DEFAULT_EXPOSE_PORT = '8080/tcp'
_DEFAULT_REGION = 'us-east-1'

def registry(aws_id, region):
    return '{}.dkr.ecr.{}.amazonaws.com'.format(aws_id, region)


def run_container(aws_id, image_label):
    try:
        client = docker.from_env(version = _DOCKER_API_VERSION)
    except Exception as e:
        logger.error(e)
        raise ValueError("Could not connect to Docker. Make sure Docker is installed.")

    registry_addr = registry(aws_id, _DEFAULT_REGION)

    # Use environment = {} to pass environment variables to the containers (not documented)
    container = client.containers.run("{}/{}".format(registry_addr, image_label),
                                      ports = {_DEFAULT_EXPOSE_PORT: None},
                                      command = _INFERENCE_COMMAND, detach = True)
    return container


def get_host_port(container):
    try:
        # Reload attrs from server to make sure they are up to date.
        container.reload()
        return container.attrs['NetworkSettings']['Ports']['8080/tcp'][0]['HostPort']
    except TypeError as e:
        logger.debug(e)
        msg = "Could not retrieve host port. It is likely that container is still starting."
        raise ValueError(msg)


def remove_container(container):
    container.stop()
    container.remove()

