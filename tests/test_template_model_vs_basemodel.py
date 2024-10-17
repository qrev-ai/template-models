import pytest

if __name__ == "__main__":
    pytest.main([__file__])

from pydantic import BaseModel, Field

from template_models.template_model import TemplateModel


@pytest.fixture
def template_model():
    template = "Name: <#name|The person's full name#>\nAge: <#age|int|The person's age in years#>\nIs Student: <#is_student|bool|Whether the person is currently a student#>"
    return TemplateModel(
        template=template,
        class_name="Person",
        class_doc="A class representing a person's basic information.",
    )


@pytest.fixture
def hardcoded_model():
    class Person(BaseModel):
        """A class representing a person's basic information."""

        name: str = Field(..., description="The person's full name")
        age: int = Field(..., description="The person's age in years")
        is_student: bool = Field(..., description="Whether the person is currently a student")

    return Person


def test_model_name(template_model, hardcoded_model):
    DynamicModel = template_model.get_model()
    assert DynamicModel.__name__ == "Person"
    assert hardcoded_model.__name__ == "Person"


def test_model_docstring(template_model, hardcoded_model):
    DynamicModel = template_model.get_model()
    assert DynamicModel.__doc__ == hardcoded_model.__doc__


def test_field_names(template_model, hardcoded_model):
    DynamicModel = template_model.get_model()
    dynamic_fields = DynamicModel.model_fields
    hardcoded_fields = hardcoded_model.model_fields
    assert set(dynamic_fields.keys()) == set(hardcoded_fields.keys())


def test_field_types_and_descriptions(template_model, hardcoded_model):
    DynamicModel = template_model.get_model()
    dynamic_fields = DynamicModel.model_fields
    hardcoded_fields = hardcoded_model.model_fields
    for field_name in dynamic_fields:
        dynamic_field = dynamic_fields[field_name]
        hardcoded_field = hardcoded_fields[field_name]
        assert type(dynamic_field.annotation) == type(
            hardcoded_field.annotation
        ), f"Type mismatch for field {field_name}"
        assert (
            dynamic_field.description == hardcoded_field.description
        ), f"Description mismatch for field {field_name}"


def test_instance_creation(template_model, hardcoded_model):
    DynamicModel = template_model.get_model()
    test_data = {"name": "John Doe", "age": 30, "is_student": False}
    dynamic_instance = DynamicModel(**test_data)
    hardcoded_instance = hardcoded_model(**test_data)
    assert dynamic_instance.model_dump() == hardcoded_instance.model_dump()


def test_validation_error(template_model, hardcoded_model):
    DynamicModel = template_model.get_model()
    invalid_data = {"name": "Jane Doe", "age": "not an integer", "is_student": True}
    with pytest.raises(ValueError):
        DynamicModel(**invalid_data)
    with pytest.raises(ValueError):
        hardcoded_model(**invalid_data)
