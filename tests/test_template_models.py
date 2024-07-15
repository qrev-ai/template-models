import pytest
from pydantic import BaseModel, Field
from template_models.template_model import TemplateModel


@pytest.fixture
def name_age_no_type():
    # Template string with field names, data types, and descriptions enclosed in <>
    return "Name:<name|This is the name field> Age:<age|This is the age field>"


@pytest.fixture
def name_age():
    # Template string with field names, data types, and descriptions enclosed in <>
    return "Name:<name|str|This is the name field> Age:<age|int|This is the age field>"


@pytest.fixture
def name_age_with_sub_fields():
    # Template string with field names, data types, and descriptions enclosed in <>
    return "Var1:{var1} Name:<name|str|This is the name field> Age:<age|int|This is the age field>"


def test_model_instance(name_age):
    data = {"name": "Jay", "age": 30}
    text_generator = TemplateModel(name_age)
    model_instance = text_generator.get_instance(data)

    assert model_instance.name == "Jay" #type: ignore
    assert model_instance.age == 30 #type: ignore


def test_text_generator(name_age):
    data = {"name": "Jay", "age": 30}
    text_generator = TemplateModel(name_age)
    assert text_generator.get_text(data) == "Name:Jay Age:30"


def test_text_generator_no_type(name_age_no_type):
    data = {"name": "Jay", "age": "30"}
    text_generator = TemplateModel(name_age_no_type)
    assert text_generator.get_text(data) == "Name:Jay Age:30"


def test_text_generator_with_sub_fields(name_age_with_sub_fields):
    data = {"name": "Jay", "age": 30}
    subs = {"var1": "Value1"}
    text_generator = TemplateModel(name_age_with_sub_fields, substitutions=subs)
    model_instance = text_generator.get_instance(data)

    assert model_instance.name == "Jay" #type: ignore
    assert model_instance.age == 30 #type: ignore

    assert text_generator.get_text(data) == "Var1:Value1 Name:Jay Age:30"


def test_text_generator_with_sub_fields_delayed1(name_age_with_sub_fields):
    data = {"name": "Jay", "age": 30}
    text_generator = TemplateModel(name_age_with_sub_fields, delayed_substitution=True)

    assert text_generator.get_text(data) == "Var1:{var1} Name:Jay Age:30"


def test_text_generator_with_sub_fields_delayed2(name_age_with_sub_fields):
    data = {"name": "Jay", "age": 30}
    text_generator = TemplateModel(name_age_with_sub_fields, delayed_substitution=True)
    substitutions = {"var1": "Value1"}
    assert (
        text_generator.get_text(data, substitutions=substitutions) == "Var1:Value1 Name:Jay Age:30"
    )


def test_get_model(name_age):
    text_generator = TemplateModel(name_age)
    assert issubclass(text_generator.get_model(), BaseModel)


def test_descriptions(name_age):
    text_generator = TemplateModel(name_age)
    model_class = text_generator.get_model()
    assert text_generator.get_field_description(model_class, "name") == "This is the name field"
    assert text_generator.get_field_description(model_class, "age") == "This is the age field"

    assert text_generator.get_all_field_descriptions(model_class) == {
        "name": "This is the name field",
        "age": "This is the age field",
    }


def test_descriptions_no_type(name_age_no_type):
    text_generator = TemplateModel(name_age_no_type)
    model_class = text_generator.get_model()
    assert text_generator.get_field_description(model_class, "name") == "This is the name field"
    assert text_generator.get_field_description(model_class, "age") == "This is the age field"

    assert text_generator.get_all_field_descriptions(model_class) == {
        "name": "This is the name field",
        "age": "This is the age field",
    }


def test_doc_string():
    text_generator = TemplateModel("Blank", class_doc="My Doc String")
    model = text_generator.get_model()
    assert model.__doc__ == "My Doc String"


def test_doc_string_on_get_model():
    text_generator = TemplateModel("Blank")
    model = text_generator.get_model(class_doc="My Doc String")
    assert model.__doc__ == "My Doc String"


def test_doc_name():
    text_generator = TemplateModel("Blank", class_name="MyModel")
    model = text_generator.get_model()
    assert model.__name__ == "MyModel"


def test_doc_name_on_get_model():
    text_generator = TemplateModel("Blank")
    model = text_generator.get_model(class_name="MyModel")
    assert model.__name__ == "MyModel"


if __name__ == "__main__":
    pytest.main([__file__, "-k", "", "-W", "ignore:Module already imported:pytest.PytestWarning"])
    # pytest.main([ __file__ ,"-k", "test_descriptions", "-W", "ignore:Module already imported:pytest.PytestWarning"])
    # from llm_text_generator import generate_tool_schema
    # class MyModel(BaseModel):
    #     """My prompt for model model_description"""
    #     name: str = Field("John", description="This is the name field")
    #     age: int = Field(30, description="This is the age field")
    # from pprint import pprint
    # pprint(generate_tool_schema(MyModel))


