import requests
from flask import Response, request
from werkzeug.exceptions import Conflict, Forbidden, NotFound

from mwdb.core.config import app_config
from mwdb.core.plugins import hooks
from mwdb.core.service import Resource
from mwdb.model import db
from mwdb.schema.remotes import RemotesListResponseSchema
from mwdb.version import app_build_version

from . import logger, requires_authorization


class RemoteListResource(Resource):
    @requires_authorization
    def get(self):
        """
        ---
        summary: Get list of configured remote names
        description: |
            Return a list of available remote names
        security:
            - bearerAuth: []
        tags:
            - remotes
        responses:
            200:
                description: List of user configured remotes
                content:
                  application/json:
                    schema: RemotesListResponseSchema
        """
        remotes = app_config.mwdb.remotes
        schema = RemotesListResponseSchema()
        return schema.dump({"remotes": remotes})


class RemoteAPI:
    def __init__(self, remote_name):
        if remote_name not in app_config.mwdb.remotes:
            raise NotFound(f"Unknown remote instance name ('{remote_name}')")

        self.remote_url = app_config.get_key(f"remote:{remote_name}", "url")
        self.api_key = app_config.get_key(f"remote:{remote_name}", "api_key")
        self.session = requests.Session()
        self.session.headers["User-Agent"] = (
            f"mwdb-core/{app_build_version} " + self.session.headers["User-Agent"]
        )

    @staticmethod
    def map_remote_api_error(response):
        if response.status_code == 200:
            return None
        elif response.status_code == 404:
            raise NotFound("Remote object not found")
        elif response.status_code == 403:
            raise Forbidden(
                "You are not permitted to perform this action on remote instance"
            )
        elif response.status_code == 409:
            raise Conflict(
                "Remote object already exists in remote instance and has different type"
            )
        else:
            response.raise_for_status()

    def request(self, method, path, *args, **kwargs):
        response = self.session.request(
            method,
            f"{self.remote_url}/api/{path}",
            *args,
            headers={"Authorization": f"Bearer {self.api_key}"},
            **kwargs,
        )
        self.map_remote_api_error(response)
        return response


class RemoteAPIResource(Resource):
    def do_request(self, method, remote_name, remote_path):
        remote = RemoteAPI(remote_name)
        response = remote.request(
            method, remote_path, params=request.args, data=request.data, stream=True
        )
        return Response(
            response.iter_content(chunk_size=2**16),
            mimetype=response.headers["content-type"],
        )

    def get(self, remote_name, remote_path):
        return self.do_request("get", remote_name, remote_path)

    def post(self, remote_name, remote_path):
        return self.do_request("post", remote_name, remote_path)

    def put(self, remote_name, remote_path):
        return self.do_request("put", remote_name, remote_path)

    def delete(self, remote_name, remote_path):
        return self.do_request("delete", remote_name, remote_path)


class RemotePullResource(Resource):
    ObjectType = None
    ItemResponseSchema = None

    on_created = None
    on_reuploaded = None

    def create_pulled_object(self, item, is_new):
        try:
            db.session.commit()

            if is_new:
                hooks.on_created_object(item)
                self.on_created(item)
            else:
                hooks.on_reuploaded_object(item)
                self.on_reuploaded(item)
        finally:
            item.release_after_upload()

        logger.info(
            f"{self.ObjectType.__name__} added",
            extra={"dhash": item.dhash, "is_new": is_new},
        )
        schema = self.ItemResponseSchema()
        return schema.dump(item)
