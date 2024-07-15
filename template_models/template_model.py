import re
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, create_model

# Mapping of string data type to actual Python type
type_mapping = {"str": str, "int": int, "float": float, "bool": bool, "list": list, "dict": dict}


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


SUB = r"<(.*?)>"


@dataclass
class TemplateModel:
    template: str
    descriptions: Optional[dict[str, str]] = field(default_factory=dict[str, str])
    substitutions: Optional[dict[str, Any]] = field(default_factory=dict[str, Any])
    field_regex: str = field(default=SUB)
    delayed_substitution: Optional[bool] = False
    class_name: Optional[str] = None
    class_doc: Optional[str] = None

    def __post_init__(self):
        if not self.class_name:
            self.class_name = f"DynamicModel_{uuid4().hex[:8]}"
        if self.substitutions:
            self.template = self._format(self.template, self.substitutions)
            if self.descriptions:
                self.descriptions = {
                    k: self._format(v, self.substitutions) for k, v in self.descriptions.items()
                }

    # Function to extract field definitions from the template string

    def _extract_field_definitions(
        self, template, descriptions: Optional[dict[str, str]] = None
    ) -> dict[str, tuple[type, Any]]:
        if descriptions is None:
            descriptions = {}
        matches = re.findall(self.field_regex, template)
        field_definitions = {}
        for match in matches:
            parts = match.split("|")
            description = descriptions.get(parts[0], None)
            if len(parts) == 3:
                name, type_str, description = parts
                field_type = type_mapping.get(
                    type_str, str
                )  # Default to str if type is not recognized
            elif len(parts) == 2:
                name, description = parts
                assert description
                field_type = type_mapping.get(description, str)
            else:
                name = parts[0]
                field_type = str
            if description:
                field_definitions[name] = (field_type, Field(..., description=description))
            else:
                field_definitions[name] = (field_type, ...)

        return field_definitions

    def _format(
        self, string: str, substitutions: dict[str, Any], allow_unknown: Optional[bool] = None
    ) -> str:
        if allow_unknown is None:
            allow_unknown = self.delayed_substitution

        if allow_unknown:
            return string.format_map(SafeDict(substitutions))
        return string.format(**substitutions)

    @staticmethod
    def get_field_description(model_class: type[BaseModel], field_name: str) -> Optional[str]:
        """
        Get the description of a specific field in the Pydantic model.
        Args:
            model_class: The Pydantic model class.
            field_name: The name of the field.
        Returns:
            The description of the field, or None if the field does not exist or does not have a description.
        """
        field_info = model_class.model_fields.get(field_name)
        if field_info:
            return field_info.description
        return None

    @staticmethod
    def get_all_field_descriptions(model_class: type[BaseModel]) -> dict[str, str]:
        """
        Get descriptions of all fields in the Pydantic model.
        Args:
            model_class: The Pydantic model class.
        Returns:
            A dictionary mapping field names to their descriptions.
        """
        return {
            field_name: field.description
            for field_name, field in model_class.model_fields.items()
            if field.description is not None
        }

    def get_model(
        self,
        substitutions: Optional[dict[str, Any]] = None,
        class_name: Optional[str] = None,
        class_doc: Optional[str] = None,
    ) -> type[BaseModel]:
        """Get the Pydantic model class based on the template string.
        Args:
            substitutions: A dictionary of substitutions to apply to the template string and fields.
        Returns:
            The Pydantic model class.
        """
        if substitutions is None:
            substitutions = self.substitutions
        if substitutions is None:
            substitutions = {}
        class_name = class_name or self.class_name
        class_doc = class_doc or self.class_doc

        templ = self._format(self.template, substitutions)

        new_descriptions = {}
        if self.descriptions is not None:
            for k, v in self.descriptions.items():
                new_descriptions[k] = self._format(v, substitutions)
        field_definitions = self._extract_field_definitions(templ, new_descriptions)
        DynamicModel = create_model(class_name, **field_definitions)  # type: ignore

        if class_doc:
            class_doc = self._format(class_doc, substitutions)
            DynamicModel.__doc__ = class_doc

        return DynamicModel

    def get_instance(
        self,
        data: dict[str, Any],
        substitutions: Optional[dict[str, Any]] = None,
        class_name: Optional[str] = None,
        class_doc: Optional[str] = None,
    ) -> BaseModel:
        """Get an instance of the Pydantic model based on the data.
        Args:
            data: A dictionary of field values.
            substitutions: A dictionary of substitutions to apply to the template string and fields.
        Returns:
            An instance of the Pydantic model.
        """
        DynamicModel = self.get_model(
            substitutions=substitutions, class_name=class_name, class_doc=class_doc
        )
        model_instance = DynamicModel(**data)
        return model_instance

    def get_text_from_instance(
        self,
        model_instance,
        data: Optional[dict[str, Any]] = None,
        substitutions: Optional[dict[str, Any]] = None,
    ):
        """Generate a text string from the model instance.
        Args:
            model_instance: An instance of the Pydantic model.
            data: A dictionary of additional data to substitute into the template string.
            substitutions: A dictionary of substitutions to apply to the template string.
        Returns:
            The generated text string.
        """

        def replace_match(match):
            field_name = match.group(1).split("|")[0]
            return str(getattr(model_instance, field_name))

        if substitutions is None:
            substitutions = self.substitutions
        if substitutions is None:
            substitutions = {}
        substituted_string = re.sub(SUB, replace_match, self.template)
        ## Also substitute the data
        if substitutions:
            substituted_string = self._format(substituted_string, substitutions)
        if data:
            substituted_string = self._format(substituted_string, data)
        return substituted_string

    # Function to substitute values back into the template string
    def get_text(
        self,
        data: dict[str, Any],
        substitutions: Optional[dict[str, Any]] = None,
        class_name: Optional[str] = None,
        class_doc: Optional[str] = None,
    ) -> str:
        """Generate a text string from the data.
        Args:
            data: A dictionary of field values.
            substitutions: A dictionary of substitutions to apply to the template string.
        Returns:
            The generated text string.
        """
        model_instance = self.get_instance(
            data, substitutions=substitutions, class_name=class_name, class_doc=class_doc
        )
        return self.get_text_from_instance(model_instance, data=data, substitutions=substitutions)
