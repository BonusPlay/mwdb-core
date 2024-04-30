from typing import Dict, Tuple, Type

from mwdb.model import (
    Comment,
    KartonAnalysis,
    Object,
    Tag,
    User,
)

from .exceptions import FieldNotQueryableException
from .fields import (
    AttributeField,
    BaseField,
    CommentAuthorField,
    DatetimeField,
    FavoritesField,
    RelationField,
    ShareField,
    SharerField,
    SizeField,
    StringField,
    StringListField,
    UploadCountField,
    UploaderField,
    UUIDField,
)
from .parse_helpers import PathSelector, parse_field_path

object_mapping: Dict[str, Type[Object]] = {
    "object": Object,
}

field_mapping: Dict[str, Dict[str, BaseField]] = {
    Object.__name__: {
        "dhash": StringField(Object.dhash),
        "tag": StringListField(Object.tags, Tag.tag),
        "comment": StringListField(Object.comments, Comment.comment),
        "meta": AttributeField(),  # legacy
        "attribute": AttributeField(),
        "shared": ShareField(),
        "sharer": SharerField(),
        "uploader": UploaderField(),
        "upload_time": DatetimeField(Object.upload_time),
        "parent": RelationField(Object.parents),
        "child": RelationField(Object.children),
        "favorites": FavoritesField(),
        "karton": UUIDField(Object.analyses, KartonAnalysis.id),
        "comment_author": CommentAuthorField(Object.comment_authors, User.login),
        "upload_count": UploadCountField(),
    },
}


def register_field_mapping(key: str, mapper: Dict[str, BaseField]):
    global field_mapping
    field_mapping[key] = mapper


def register_object_mapping(name: str, type_: Type[Object]):
    global object_mapping
    object_mapping[name] = type_


def get_field_mapper(
    queried_type: str, field_selector: str
) -> Tuple[BaseField, PathSelector]:
    field_path = parse_field_path(field_selector)
    field_name, asterisks = field_path[0]
    # Map object type selector
    if field_name in object_mapping:
        selected_type = object_mapping[field_name]
        field_path = field_path[1:]
    else:
        selected_type = queried_type

    # Map object field selector
    field_name, asterisks = field_path[0]
    if field_name in field_mapping[selected_type.__name__]:
        field = field_mapping[selected_type.__name__][field_name]
    elif field_name in field_mapping[Object.__name__]:
        field = field_mapping[Object.__name__][field_name]
    else:
        raise FieldNotQueryableException(f"No such field {field_name}")

    return field, field_path
