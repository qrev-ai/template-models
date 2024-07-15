from dataclasses import dataclass
from typing import Any, Optional

from openai import OpenAI
from pydantic import BaseModel
from qrev_instructor import get_api_service, get_client, instructor

from .template_model import TemplateModel


def generate_tool_schema(pydantic_model):
    schema = pydantic_model.schema()

    # Find non-optional fields
    required_fields = [
        field for field, field_info in pydantic_model.__fields__.items() if field_info.required
    ]

    # Add required fields to the schema
    schema["required"] = required_fields

    tool_definition = {
        "name": pydantic_model.__name__,
        "description": pydantic_model.__doc__ or "",
        "schema": schema,
    }
    return tool_definition


@dataclass
class LLMTemplateModel(TemplateModel):
    system_prompt: Optional[str] = None

    def generate_instance(
        self,
        query: str,
        class_name: str | None = None,
        class_doc: str | None = None,
        system_prompt: Optional[str] = None,
        substitutions: Optional[dict[str, Any]] = None,
        verbose: bool = True,
        llm: Optional[instructor.Instructor] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
    ) -> BaseModel:
        model_name = model_name or "gpt-3.5-turbo"
        system_prompt = system_prompt or self.system_prompt

        if system_prompt and substitutions:
            ## Has to be allow_unknown because llama_index also can have substitutions
            system_prompt = self._format(system_prompt, substitutions, allow_unknown=True)
        client = get_client(model=model_name, client=llm)
        
        
        pymodel = self.get_model(
            substitutions=substitutions, class_name=class_name, class_doc=class_doc
        )

        try:
            # Extract structured data from natural language
            model_instance = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": query}],
                response_model=pymodel,
            )
            return model_instance
        except Exception as e:
            print(e)
            raise

    def generate_text(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        substitutions: Optional[dict[str, Any]] = None,
        verbose: bool = True,
        llm: Optional[instructor.Instructor] = None,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.0,
    ) -> str:
        if substitutions:
            raise NotImplementedError("Substitutions are not supported for LLMTemplateModel yet")
        instance = self.generate_instance(
            query=query,
            system_prompt=system_prompt,
            substitutions=substitutions,
            verbose=verbose,
            llm=llm,
            model_name=model_name,
            temperature=temperature,
        )
        return self.get_text_from_instance(instance)
