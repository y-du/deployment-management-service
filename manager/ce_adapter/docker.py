"""
   Copyright 2020 Yann Dumont

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""


__all__ = ("DockerAdapter", )


from ..logger import getLogger
from ..configuration import dm_conf
from .interface import Interface, ContainerState, EngineAPIError, NotFound, CEAdapterError
import docker
import docker.errors
import docker.types
import typing


logger = getLogger(__name__.split(".", 1)[-1])


error_map = {
    docker.errors.APIError: EngineAPIError,
    docker.errors.NotFound: NotFound
}

container_state_map = {
    "created": ContainerState.stopped,
    "restarting": ContainerState.running,
    "running": ContainerState.running,
    "removing": ContainerState.running,
    "paused": ContainerState.stopped,
    "exited": ContainerState.stopped,
    "dead": ContainerState.stopped
}


class DockerAdapter(Interface):
    def __init__(self):
        self.__client = docker.DockerClient(base_url=dm_conf.CE.socket)

    def __getVolName(self, c_name, v_name) -> str:
        return "{}_{}".format(c_name, v_name)

    def __createVolume(self, c_name, v_name):
        try:
            self.__client.volumes.create(name=v_name, labels={c_name: None})
        except Exception as ex:
            logger.error("can't create volume '{}' - {}".format(v_name, ex))
            raise error_map.setdefault(ex, CEAdapterError)(ex)

    def __removeVolume(self, name):
        try:
            volume = self.__client.volumes.get(name)
            volume.remove()
        except Exception as ex:
            logger.error("can't remove volume '{}' - {}".format(name, ex))
            raise error_map.setdefault(ex, CEAdapterError)(ex)

    def __initVolumes(self, c_name, volumes):
        volumes = [self.__getVolName(c_name, vol) for vol in volumes]
        existing_volumes = self.__client.volumes.list(filters={"label": c_name})
        if existing_volumes:
            existing_volumes = [vol.name for vol in existing_volumes]
        new_volumes = set(volumes) - set(existing_volumes)
        missing_volumes = set(existing_volumes) - set(volumes)
        for volume in new_volumes:
            self.__createVolume(c_name, volume)
        for volume in missing_volumes:
            self.__removeVolume(volume)

    def __purgeVolumes(self, c_name):
        volumes = self.__client.volumes.list(filters={"label": c_name})
        for volume in volumes:
            try:
                volume.remove(force=True)
            except Exception as ex:
                logger.error("can't purge volume '{}' - {}".format(volume.name, ex))
                # raise error_map.setdefault(ex, CEAdapterError)(ex)

    def listContainers(self) -> dict:
        try:
            container_objs = self.__client.containers.list(all=True)
            deployments = dict()
            for container in container_objs:
                deployments[container.name] = {
                    "image": container.image.tags[0],
                    "hash": container.id,
                    "state": container_state_map[container.status]
                }
            return deployments
        except Exception as ex:
            logger.error("can't list deployments - {}".format(ex))
            raise error_map.setdefault(ex, CEAdapterError)(ex)

    def startContainer(self, name: str) -> None:
        try:
            container_obj = self.__client.containers.get(name)
            container_obj.start()
        except Exception as ex:
            logger.error("can't start deployment '{}' - {}".format(name, ex))
            raise error_map.setdefault(ex, CEAdapterError)(ex)

    def stopContainer(self, name: str) -> None:
        try:
            container_obj = self.__client.containers.get(name)
            container_obj.stop()
            # container_obj.wait()
        except Exception as ex:
            logger.error("can't stop deployment '{}' - {}".format(name, ex))
            raise error_map.setdefault(ex, CEAdapterError)(ex)

    def createContainer(self, name: str, dpy_conf: dict, srv_conf: typing.Optional[dict] = None, env_conf: typing.Optional[dict] = None) -> None:
        try:
            self.__client.images.pull(repository=dpy_conf["image"])
            self.__initVolumes(name, dpy_conf["volumes"])
            volumes = {self.__getVolName(name, volume): {"bind": target, "mode": "rw"} for volume, target in dpy_conf["volumes"].items()}
            srv_conf = srv_conf or dict()
            env_conf = env_conf or dict()
            self.__client.containers.create(
                name=name,
                network=dm_conf.ContainerNetwork.name,
                image=dpy_conf["image"],
                environment={**srv_conf, **env_conf},
                volumes=volumes,
                ports={"{}/{}".format(port["container"], port["protocol"] or "tcp"): port["host"] for port in dpy_conf["ports"]},
                detach=True
            )
        except Exception as ex:
            logger.error("can't create container '{}' - {}".format(name, ex))
            raise error_map.setdefault(ex, CEAdapterError)(ex)

    def removeContainer(self, name: str, purge=False) -> None:
        try:
            container_obj = self.__client.containers.get(name)
            container_obj.remove()
            if purge:
                self.__purgeVolumes(name)
        except Exception as ex:
            logger.error("can't remove deployment '{}' - {}".format(name, ex))
            raise error_map.setdefault(ex, CEAdapterError)(ex)
