from typing import Optional, Any
from luqum.tree import Item

from mwdb.core.search.fields import BaseField, MultiBaseField, JSONBaseField
from mwdb.core.search.parse_helpers import (
    PathSelector,
    unescape_string,
    transform_for_config_like_statement,
    transform_for_quoted_config_like_statement,
    jsonpath_range_equals,
    jsonpath_config_string_equals,
)

from mlwr.model import Config, File, TextBlob


class MultiFileField(MultiBaseField):
    def _get_condition_for_value(self, escaped_value: str):
        value = unescape_string(escaped_value)
        if re.fullmatch(r"[0-9a-fA-F]{8}", value):
            return File.crc32 == value
        elif re.fullmatch(r"[0-9a-fA-F]{32}", value):
            return File.md5 == value
        elif re.fullmatch(r"[0-9a-fA-F]{40}", value):
            return File.sha1 == value
        elif re.fullmatch(r"[0-9a-fA-F]{64}", value):
            return File.sha256 == value
        elif re.fullmatch(r"[0-9a-fA-F]{128}", value):
            return File.sha512 == value
        else:
            raise ObjectNotFoundException(f"{value} is not valid hash value")


class MultiConfigField(MultiBaseField):
    def _get_condition_for_value(self, escaped_value: str):
        value = unescape_string(escaped_value)
        if re.fullmatch(r"[0-9a-fA-F]{64}", value):
            return Config.dhash == value
        else:
            value = transform_for_quoted_config_like_statement(
                "*" + escaped_value + "*"
            )
            json_element = Config._cfg.operate(JSONPATH_ASTEXT, "{}", result_type=Text)
            return json_element.like(value)


class ConfigField(JSONBaseField):
    def __init__(self):
        super().__init__(Config.cfg)

    def _get_value_for_like_statement(self, value: str) -> str:
        return transform_for_config_like_statement(value)

    def _get_quoted_value_for_like_statement(self, value: str) -> str:
        return transform_for_quoted_config_like_statement(value)

    def _get_jsonpath_for_range_equals(
        self,
        path_selector: PathSelector,
        low: Optional[str],
        high: Optional[str],
        include_low: bool,
        include_high: bool,
    ) -> str:
        return jsonpath_range_equals(
            path_selector, low, high, include_low, include_high
        )

    def _get_jsonpath_for_string_equals(
        self, path_selector: PathSelector, value: str
    ) -> str:
        return jsonpath_config_string_equals(path_selector, value)

    def _get_condition(self, node: Item, path_selector: PathSelector) -> Any:
        return self._get_json_condition(node, path_selector)


class MultiBlobField(MultiBaseField):
    def _get_condition_for_value(self, escaped_value: str):
        value = unescape_string(escaped_value)
        if re.fullmatch(r"[0-9a-fA-F]{64}", value):
            return TextBlob.dhash == value
        else:
            # Blobs are unicode-escaped too
            value = transform_for_config_like_statement("*" + escaped_value + "*")
            return TextBlob._content.like(value)


class FileNameField(BaseField):
    accepts_wildcards = True

    def _get_condition(self, node: Item, path_selector: PathSelector) -> Any:
        string_value = string_from_node(node, escaped=True)
        name_condition = string_equals(File.file_name, string_value)
        if is_pattern_value(string_value):
            """
            Should translate to:

            EXISTS (
                SELECT 1
                FROM unnest(object.alt_names) AS alt_name
                WHERE alt_name LIKE <pattern>
            )
            """
            escaped_value = transform_for_like_statement(string_value)
            alt_name = func.unnest(File.alt_names).alias("alt_name")
            alt_names_condition = exists(
                select([1])
                .select_from(alt_name)
                .where(column(alt_name.name).like(escaped_value))
            )
        else:
            # Use @> operator to utilize GIN index on ARRAY
            unescaped_value = unescape_string(string_value)
            value_array = cast(array([unescaped_value]), ARRAY(String))
            alt_names_condition = File.alt_names.operate(CONTAINS, value_array)
        return or_(name_condition, alt_names_condition)
