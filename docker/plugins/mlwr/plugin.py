import logging

from mwdb.core.plugins import PluginAppContext, PluginHookHandler
# for some reason attempts to re-export these in local search submodule have failed
from mwdb.core.search.fields import (
    SizeField,
    StringField,
    DatetimeField,
    BaseField,
    MultiBaseField,
    JSONBaseField
)

from .resources.blob import TextBlobItemResource, TextBlobResource
from .resources.config import (
    ConfigItemResource,
    ConfigResource,
    ConfigStatsResource,
)
from .resources.file import (
    FileDownloadResource,
    FileDownloadZipResource,
    FileItemResource,
    FileResource,
)
from .resources.remotes import (
    RemoteConfigPullResource,
    RemoteConfigPushResource,
    RemoteFilePullResource,
    RemoteFilePushResource,
    RemoteTextBlobPullResource,
    RemoteTextBlobPushResource,
)
from .model import (
    Config,
    File,
    TextBlob,
)
from .hooks import MlwrHookHandler
from .search.fields import (
    # SizeField,
    # StringField,
    # DatetimeField,
    FileNameField,
    MultiFileField,
    ConfigField,
    MultiConfigField,
    MultiBlobField
)


logger = logging.getLogger("mwdb.plugin.mlwr")


def entrypoint(app_context: PluginAppContext):
    # hooks
    app_context.register_hook_handler(MlwrHookHandler)

    # File endpoints
    app_context.register_resource(FileResource, "/file")
    app_context.register_resource(FileItemResource, "/file/<hash64:identifier>")
    app_context.register_resource(FileDownloadResource, "/file/<hash64:identifier>/download")
    app_context.register_resource(FileDownloadZipResource, "/file/<hash64:identifier>/download/zip")

    # Config endpoints
    app_context.register_resource(ConfigResource, "/config")
    app_context.register_resource(ConfigStatsResource, "/config/stats")
    app_context.register_resource(ConfigItemResource, "/config/<hash64:identifier>")

    # Blob endpoints
    app_context.register_resource(TextBlobResource, "/blob")
    app_context.register_resource(TextBlobItemResource, "/blob/<hash64:identifier>")

    # Remote endpoints
    app_context.register_resource(RemoteFilePullResource, "/remote/<remote_name>/pull/file/<hash64:identifier>")
    app_context.register_resource(RemoteConfigPullResource, "/remote/<remote_name>/pull/config/<hash64:identifier>")
    app_context.register_resource(RemoteTextBlobPullResource, "/remote/<remote_name>/pull/blob/<hash64:identifier>")
    app_context.register_resource(RemoteFilePushResource, "/remote/<remote_name>/push/file/<hash64:identifier>")
    app_context.register_resource(RemoteConfigPushResource, "/remote/<remote_name>/push/config/<hash64:identifier>")
    app_context.register_resource(RemoteTextBlobPushResource, "/remote/<remote_name>/push/blob/<hash64:identifier>")

    # search stuff
    object_mappings = {
        "file": File,
        "static": Config,  # legacy
        "config": Config,
        "blob": TextBlob,
    }
    for key, val in object_mappings.items():
        app_context.register_object_mapping(key, val)

    # more search stuff
    app_context.register_field_mapping(File.__name__, {
        "name": FileNameField(),
        "size": SizeField(File.file_size),
        "type": StringField(File.file_type),
        "md5": StringField(File.md5),
        "sha1": StringField(File.sha1),
        "sha256": StringField(File.sha256),
        "sha512": StringField(File.sha512),
        "ssdeep": StringField(File.ssdeep),
        "crc32": StringField(File.crc32),
        "multi": MultiFileField(),
    })
    app_context.register_field_mapping(Config.__name__, {
        "type": StringField(Config.config_type),
        "family": StringField(Config.family),
        "cfg": ConfigField(),
        "multi": MultiConfigField(),
    })
    app_context.register_field_mapping(TextBlob.__name__, {
        "name": StringField(TextBlob.blob_name),
        "size": SizeField(TextBlob.blob_size),
        "type": StringField(TextBlob.blob_type),
        "content": StringField(TextBlob._content),
        "first_seen": DatetimeField(TextBlob.upload_time),
        "last_seen": DatetimeField(TextBlob.last_seen),
        "multi": MultiBlobField(),
    })


def configure():
    logger.info("Configuring 'drakvuf' attribute key.")
    attribute = MetakeyDefinition(key="drakvuf",
                                  url_template=f"{config.drakvuf.drakvuf_url}/progress/$value",
                                  label="Drakvuf analysis",
                                  description="Reference to the Drakvuf analysis for file")
    db.session.merge(attribute)
    db.session.commit()
