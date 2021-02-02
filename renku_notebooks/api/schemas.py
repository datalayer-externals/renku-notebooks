from marshmallow import Schema, fields, post_load, post_dump
import collections

from .. import config
from .custom_fields import UnionField


class LaunchNotebookRequest(Schema):
    """Used to validate the requesting for launching a jupyterhub server"""

    namespace = fields.Str(required=True)
    project = fields.Str(required=True)
    branch = fields.Str(missing="master")
    commit_sha = fields.Str(required=True)
    notebook = fields.Str(missing=None)
    image = fields.Str(missing=None)
    server_options = fields.Dict(
        keys=fields.Str(), missing={}, data_key="serverOptions"
    )


def flatten_dict(d, parent_key="", sep="."):
    """
    Convert a nested dictionary into a dictionary that is one level deep.
    Nested dictionaries of any depth have their keys combined by a ".".
    I.e. calling this function on {"A": 1, "B": {"C": {"D": 2}}}
    will result in {"A":1, "B.C.D":2}. Used to address the fact that
    marshamallow will parse schema keys with dots in them as a series
    of nested dictionaries.
    From: https://stackoverflow.com/a/6027615
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


class UserPodAnnotations(
    Schema.from_dict(
        {
            f"{config.RENKU_ANNOTATION_PREFIX}namespace": fields.Str(required=True),
            f"{config.RENKU_ANNOTATION_PREFIX}projectId": fields.Str(required=True),
            f"{config.RENKU_ANNOTATION_PREFIX}projectName": fields.Str(required=True),
            f"{config.RENKU_ANNOTATION_PREFIX}branch": fields.Str(required=True),
            f"{config.RENKU_ANNOTATION_PREFIX}commit-sha": fields.Str(required=True),
            f"{config.RENKU_ANNOTATION_PREFIX}username": fields.Str(required=False),
            f"{config.RENKU_ANNOTATION_PREFIX}default_image_used": fields.Str(
                required=True
            ),
            f"{config.RENKU_ANNOTATION_PREFIX}repository": fields.Str(required=True),
            f"{config.RENKU_ANNOTATION_PREFIX}git-host": fields.Str(required=False),
            f"{config.JUPYTERHUB_ANNOTATION_PREFIX}servername": fields.Str(
                required=True
            ),
            f"{config.JUPYTERHUB_ANNOTATION_PREFIX}username": fields.Str(required=True),
        }
    )
):
    """
    Used to validate the annotations of a jupyterhub user pod
    that are returned to the UI as part of any endpoint that list servers.
    """

    def get_attribute(self, obj, key, *args, **kwargs):
        # in marshmallow, any schema key with a dot in it is converted to nested dictionaries
        # in marshmallow, this overrides that behaviour for dumping (serializing)
        return obj[key]

    @post_load
    def unnest_keys(self, data, **kwargs):
        # in marshmallow, any schema key with a dot in it is converted to nested dictionaries
        # this overrides that behaviour for loading (deserializing)
        return flatten_dict(data)


UserPodResources = Schema.from_dict(
    # Memory and CPU resources that should be present in the response to creating a
    # jupyterhub noteboooks server.
    {
        "cpu": fields.Str(required=True),
        "memory": fields.Str(required=True),
        "ephemeral-storage": fields.Str(required=False),
    }
)


class LaunchNotebookResponse(Schema):
    """
    The response sent after a successful creation of a jupyterhub server. Or
    if the user tries to create a server that already exists.
    """

    annotations = fields.Nested(UserPodAnnotations())
    name = fields.Str()
    state = fields.Dict()
    started = fields.DateTime(format="iso", allow_none=True)
    status = fields.Dict()
    url = fields.Str()
    resources = fields.Nested(UserPodResources())
    image = fields.Str()


class ServersGetResponse(Schema):
    """The response for listing all servers that are active or launched by a user."""

    servers = fields.Dict(
        keys=fields.Str(), values=fields.Nested(LaunchNotebookResponse())
    )


class DefaultResponseSchema(Schema):
    """Schema used for reporting general errors."""

    messages = fields.Dict(keys=fields.Str(), values=fields.Str())


class FailedParsing(Schema):
    """Schema used for reporting errors when parsing of parameters fails."""

    messages = fields.Dict(
        keys=fields.Str(),
        values=fields.Dict(keys=fields.Str, values=fields.List(fields.Str())),
    )


class ServerOptionsOption(Schema):
    """The schema used to describe a single option for the server_options endpoint."""

    default = UnionField(
        [
            fields.Str(required=True),
            fields.Number(required=True),
            fields.Bool(required=True),
        ]
    )
    displayName = fields.Str(required=True)
    order = fields.Int(required=True)
    type = fields.Str(required=True)
    options = fields.List(UnionField([fields.Str(), fields.Number()]))


class ServerOptions(Schema):
    """
    Specifies which options are available to the user in the UI when
    launching a jupyterhub server.
    """

    cpu_request = fields.Nested(ServerOptionsOption())
    defaultUrl = fields.Nested(ServerOptionsOption())
    gpu_request = fields.Nested(ServerOptionsOption())
    lfs_auto_fetch = fields.Nested(ServerOptionsOption())
    mem_request = fields.Nested(ServerOptionsOption())


class ServerLogs(Schema):
    """
    The list of k8s logs (one log line per list element)
    for the pod that runs the jupyterhub server.
    """

    items = fields.List(fields.Str())

    @post_dump
    @post_load
    def remove_item_key(self, data, **kwargs):
        return data.get("items", [])


class AuthState(Schema):
    """
    This is part of the schema that specifies information about a logged in user.
    It holds the username and access token for a logged in user.
    """

    access_token = fields.Str()
    gitlab_user = fields.Dict(keys=fields.Str())


class User(Schema):
    """Species information about a logged in user."""

    admin = fields.Bool()
    auth_state = fields.Nested(AuthState(), missing=None)
    created = fields.DateTime(format="iso")
    groups = fields.List(fields.Str())
    kind = fields.Str()
    last_activity = fields.DateTime(format="iso")
    name = fields.Str()
    pending = fields.Str(missing=None)
    server = fields.Str(missing=None)
    servers = fields.Dict(
        keys=fields.Str(), values=fields.Nested(LaunchNotebookResponse()), missing={}
    )