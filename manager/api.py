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


from .ce_adapter import Interface, ContainerState, CEAdapterError, NotFound
import falcon
import json


class Deployments:
    def __init__(self, ce_adapter: Interface):
        self.__ce_adapter = ce_adapter

    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response):
        try:
            items = self.__ce_adapter.listContainers()
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
            resp.body = json.dumps(items)
        except NotFound:
            resp.status = falcon.HTTP_404
        except CEAdapterError:
            resp.status = falcon.HTTP_500

    def on_post(self, req: falcon.request.Request, resp: falcon.response.Response):
        if not req.content_type == falcon.MEDIA_JSON:
            resp.status = falcon.HTTP_415
        else:
            try:
                data = json.load(req.bounded_stream)
                if data:
                    if data["name"] in self.__ce_adapter.listContainers():
                        self.__ce_adapter.removeContainer(data["name"])
                    self.__ce_adapter.createContainer(data["name"], data["deployment_configs"], data.get("service_configs"), data.get("runtime_vars"))
                    resp.status = falcon.HTTP_200
            except KeyError:
                resp.status = falcon.HTTP_400
            except CEAdapterError:
                resp.status = falcon.HTTP_500


class Deployment:
    def __init__(self, ce_adapter: Interface):
        self.__ce_adapter = ce_adapter

    def on_put(self, req: falcon.request.Request, resp: falcon.response.Response, deployment):
        if not req.content_type == falcon.MEDIA_JSON:
            resp.status = falcon.HTTP_415
        else:
            try:
                data = json.load(req.bounded_stream)
                if data:
                    if data["state"] == ContainerState.running:
                        self.__ce_adapter.stopContainer(deployment)
                    elif data["state"] == ContainerState.stopped:
                        self.__ce_adapter.startContainer(deployment)
                    resp.status = falcon.HTTP_200
            except KeyError:
                resp.status = falcon.HTTP_400
            except NotFound:
                resp.status = falcon.HTTP_404
            except CEAdapterError:
                resp.status = falcon.HTTP_500

    def on_delete(self, req: falcon.request.Request, resp: falcon.response.Response, deployment):
        try:
            self.__ce_adapter.removeContainer(deployment, purge=True)
            resp.status = falcon.HTTP_200
        except NotFound:
            resp.status = falcon.HTTP_404
        except CEAdapterError:
            resp.status = falcon.HTTP_500
