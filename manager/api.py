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

__all__ = ("Deployments", "Deployment")


from .logger import getLogger
from .ce_adapter import Interface, ContainerState, CEAdapterError, NotFound
import falcon
import json


logger = getLogger(__name__.split(".", 1)[-1])


def reqDebugLog(req):
    logger.debug("method='{}' path='{}' content_type='{}'".format(req.method, req.path, req.content_type))


def reqErrorLog(req, ex):
    logger.error("method='{}' path='{}' - {}".format(req.method, req.path, ex))


class Deployments:
    def __init__(self, ce_adapter: Interface):
        self.__ce_adapter = ce_adapter

    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response):
        reqDebugLog(req)
        try:
            items = self.__ce_adapter.listContainers()
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
            resp.body = json.dumps(items)
        except NotFound as ex:
            resp.status = falcon.HTTP_404
            reqErrorLog(req, ex)
        except Exception as ex:
            resp.status = falcon.HTTP_500
            reqErrorLog(req, ex)

    def on_post(self, req: falcon.request.Request, resp: falcon.response.Response):
        reqDebugLog(req)
        if not req.content_type == falcon.MEDIA_JSON:
            resp.status = falcon.HTTP_415
        else:
            try:
                data = json.load(req.bounded_stream)
                if data["name"] in self.__ce_adapter.listContainers():
                    self.__ce_adapter.removeContainer(data["name"])
                self.__ce_adapter.createContainer(data["name"], data["deployment_configs"], data.get("service_configs"), data.get("runtime_vars"))
                resp.status = falcon.HTTP_200
            except KeyError as ex:
                resp.status = falcon.HTTP_400
                reqErrorLog(req, ex)
            except Exception as ex:
                resp.status = falcon.HTTP_500
                reqErrorLog(req, ex)


class Deployment:
    def __init__(self, ce_adapter: Interface):
        self.__ce_adapter = ce_adapter

    def on_patch(self, req: falcon.request.Request, resp: falcon.response.Response, deployment):
        reqDebugLog(req)
        if not req.content_type == falcon.MEDIA_JSON:
            resp.status = falcon.HTTP_415
        else:
            try:
                data = json.load(req.bounded_stream)
                if data["state"] == ContainerState.running:
                    self.__ce_adapter.startContainer(deployment)
                elif data["state"] == ContainerState.stopped:
                    self.__ce_adapter.stopContainer(deployment)
                else:
                    raise KeyError
                resp.status = falcon.HTTP_200
            except KeyError as ex:
                resp.status = falcon.HTTP_400
                reqErrorLog(req, ex)
            except NotFound as ex:
                resp.status = falcon.HTTP_404
                reqErrorLog(req, ex)
            except Exception as ex:
                resp.status = falcon.HTTP_500
                reqErrorLog(req, ex)

    def on_delete(self, req: falcon.request.Request, resp: falcon.response.Response, deployment):
        reqDebugLog(req)
        try:
            self.__ce_adapter.removeContainer(deployment, purge=True)
            resp.status = falcon.HTTP_200
        except NotFound as ex:
            resp.status = falcon.HTTP_404
            reqErrorLog(req, ex)
        except Exception as ex:
            resp.status = falcon.HTTP_500
            reqErrorLog(req, ex)
