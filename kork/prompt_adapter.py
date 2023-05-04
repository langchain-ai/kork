"""A prompt adapter to allow working with both regular LLMs and Chat LLMs.

The prompt adapter supports breaking the prompt into:

1) Instruction Section
2) (Optional) Example Section
"""
from typing import Any, Callable, List, Sequence, Tuple

from langchain import BasePromptTemplate, PromptTemplate
from langchain.schema import BaseMessage, HumanMessage, PromptValue, SystemMessage
from pydantic import Extra


class FewShotPromptValue(PromptValue):
    """Integration with langchain prompt format."""

    string: Callable[[], str]
    messages: Callable[[], List[BaseMessage]]

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
        arbitrary_types_allowed = True

    def to_string(self) -> str:
        """Format the prompt to a string."""
        return self.string()

    def to_messages(self) -> List[BaseMessage]:
        """Get materialized messages."""
        return self.messages()


class FewShotTemplate(BasePromptTemplate):
    """Code prompt template."""

    instruction_template: PromptTemplate
    examples: Sequence[Tuple[str, str]] = ()

    @property
    def _prompt_type(self) -> str:
        """Get the prompt type."""
        return "FewShotTemplate"

    def format_prompt(self, **kwargs: Any) -> PromptValue:
        """Format the prompt."""
        if len(self.input_variables) != 1:
            raise AssertionError(
                f"Expected 1 input variable, got {len(self.input_variables)}"
            )

        query_key = self.input_variables[0]
        query = kwargs[query_key]

        def _lazy_string() -> str:
            """Lazy string."""
            return self.to_string(query)

        def _lazy_messages() -> List[BaseMessage]:
            """Lazy messages."""
            return self.to_messages(query)

        return FewShotPromptValue(
            string=_lazy_string,
            messages=_lazy_messages,
        )

    def format(self, **kwargs: Any) -> str:
        """Deprecated format method."""
        raise NotImplementedError()

    def to_string(self, query: str) -> str:
        """Format the prompt to a string."""
        instruction_section = self.instruction_template.format()

        examples_block = ""

        for input_example, output_example in self.examples:
            examples_block += f"Input: {input_example}\n\nOutput: {output_example}\n\n"

        return instruction_section + examples_block + f"Input: {query}\n\nOutput:"

    def to_messages(self, query: str) -> List[BaseMessage]:
        """Get materialized messages."""
        instruction_segment = self.instruction_template.format().strip()
        messages: List[BaseMessage] = [SystemMessage(content=instruction_segment)]

        for input_example, output_example in self.examples:
            messages.append(HumanMessage(content=input_example.strip()))
            messages.append(SystemMessage(content=output_example.strip()))

        messages.append(HumanMessage(content=query.strip()))

        return messages
