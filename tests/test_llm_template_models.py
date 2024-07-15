import pytest
from pi_conf import load_config
from pydantic import BaseModel

from template_models import LLMTemplateModel

load_config().to_env() ## put .config.toml into environment variables

@pytest.fixture
def name_age_template():
    return "Name:<name|str|This is the name field> Age:<age|int|This is the age field>"

@pytest.fixture
def name_age_with_sub_fields():
    return "Var1:{var1} Name:<name|str|This is the name field> Age:<age|int|This is the age field>"

def test_model_instance(name_age_template):
    query = "My name is Jay and I am 30 years old."
    text_generator = LLMTemplateModel(name_age_template)
    model_instance = text_generator.generate_instance(query)

    assert model_instance.name == "Jay" #type: ignore
    assert model_instance.age == 30 #type: ignore

def test_text_generator(name_age_template):
    query = "My name is Jay and I am 30 years old."
    text_generator = LLMTemplateModel(name_age_template)
    assert text_generator.generate_text(query) == "Name:Jay Age:30"

def test_text_generator_with_sub_fields(name_age_with_sub_fields):
    query = "My name is Jay and I am 30 years old."
    subs = {"var1": "Value1"}
    text_generator = LLMTemplateModel(name_age_with_sub_fields, substitutions=subs)
    model_instance = text_generator.generate_instance(query)

    assert model_instance.name == "Jay" #type: ignore
    assert model_instance.age == 30 #type: ignore

    assert text_generator.generate_text(query) == "Var1:Value1 Name:Jay Age:30"

def test_text_generator_with_sub_fields_delayed1(name_age_with_sub_fields):
    query = "My name is Jay and I am 30 years old."
    text_generator = LLMTemplateModel(name_age_with_sub_fields, delayed_substitution=True)

    assert text_generator.generate_text(query) == "Var1:{var1} Name:Jay Age:30"

# def test_text_generator_with_sub_fields_delayed2(name_age_with_sub_fields):
#     query = "My name is Jay and I am 30 years old."
#     text_generator = LLMTemplateModel(name_age_with_sub_fields, delayed_substitution=True)
#     substitutions = {"var1": "Value1"}
#     assert text_generator.generate_text(query, substitutions=substitutions) == "Var1:Value1 Name:Jay Age:30"

def test_generate_model(name_age_template):
    text_generator = LLMTemplateModel(name_age_template)
    assert issubclass(text_generator.get_model(), BaseModel)

def test_descriptions(name_age_template):
    text_generator = LLMTemplateModel(name_age_template)
    model_class = text_generator.get_model()
    assert text_generator.get_field_description(model_class, "name") == "This is the name field"
    assert text_generator.get_field_description(model_class, "age") == "This is the age field"

    assert text_generator.get_all_field_descriptions(model_class) == {
        "name": "This is the name field",
        "age": "This is the age field",
    }

def test_doc_string():
    text_generator = LLMTemplateModel("Blank", class_doc="My Doc String")
    model = text_generator.get_model()
    assert model.__doc__ == "My Doc String"

def test_doc_string_on_generate_model():
    text_generator = LLMTemplateModel("Blank")
    model = text_generator.get_model(class_doc="My Doc String")
    assert model.__doc__ == "My Doc String"

def test_doc_name():
    text_generator = LLMTemplateModel("Blank", class_name="MyModel")
    model = text_generator.get_model()
    assert model.__name__ == "MyModel"

def test_doc_name_on_generate_model():
    text_generator = LLMTemplateModel("Blank")
    model = text_generator.get_model(class_name="MyModel")
    assert model.__name__ == "MyModel"

if __name__ == "__main__":
    pytest.main([__file__, "-k", "", "-W", "ignore:Module already imported:pytest.PytestWarning"])