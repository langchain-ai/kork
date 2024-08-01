"""Implementation of a programming chain."""
from __future__ import annotations

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    Union,
    cast,
)

from langchain.chains.base import Chain
from langchain_core.prompts import PromptTemplate

try:
    from langchain.base_language import BaseLanguageModel
except ImportError:
    from langchain.schema import BaseLanguageModel

from kork import ast
from kork.ast_printer import AbstractAstPrinter, AstPrinter
from kork.environment import Environment, create_environment
from kork.examples import (
    AbstractExampleRetriever,
    InputFormatter,
    SimpleExampleRetriever,
    format_examples,
    format_text,
)
from kork.exceptions import LLMParseException
from kork.interpreter import InterpreterResult, run_interpreter
from kork.prompt_adapter import FewShotTemplate
from kork.retrieval import AbstractContextRetriever, FuncLike, SimpleContextRetriever
from kork.utils import unwrap_tag

_INSTRUCTION_PROMPT = """\
You are programming in a language called "{language_name}".

You are an expert programmer and must follow the instructions below exactly.

Your goal is to translate a user query into a corresponding and valid {language_name}
program.

{external_functions_block}

Do not assume that any other functions except for the ones listed above exist.

Wrap the program in <code> and </code> tags.

Store the solution to the query in a variable called "result".

Here is a sample valid program:

<code>
var x = 1 # Assign 1 to the variable x
var result = 1 + 2 # Calculate the sum of 1 + 2 and assign to result
var result = x # Assign the value of x to result
</code>

Guidelines:
- Do not use operators, instead invoke appropriate external functions.
- Do not declare functions, do not use loops, do not use conditionals.
- Solve the problem only using variable declarations and function invocations.

Begin!
"""


# PUBLIC API


DEFAULT_INSTRUCTION_PROMPT = PromptTemplate(
    input_variables=[
        "language_name",
        "external_functions_block",
    ],
    template=_INSTRUCTION_PROMPT,
)


class CodeResult(TypedDict):
    """Result of a code chain."""

    errors: Sequence[Exception]
    raw: str
    code: str
    environment: Optional[Environment]  # Returned on success


# PUBLIC API

ExampleTuple = Tuple[str, ast.Program]


class CodeChain(Chain):
    """A coding chain."""

    llm: BaseLanguageModel
    """The language model to use for the coding chain."""
    interpreter: Callable[[str, Environment], InterpreterResult]
    """The interpreter to use for the coding chain."""
    ast_printer: AbstractAstPrinter
    """The AST printer to use for the coding chain."""
    context_retriever: Optional[AbstractContextRetriever] = None
    """Context to inject into the environment and prompt.
    
    At the moment, this context is limited to external functions.
    """
    example_retriever: Optional[AbstractExampleRetriever] = None
    """Examples that should be added to the prompt."""
    instruction_template: PromptTemplate = DEFAULT_INSTRUCTION_PROMPT
    """Template for the instruction prompt."""
    input_key: str = "query"
    # Smirking kat language
    language_name: str = "😼"
    input_formatter: InputFormatter = "triple_quotes"

    """The smirking kat programming language; aka Kork; aka 😼"""

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    @property
    def input_keys(self) -> List[str]:
        """Will be whatever keys the prompt expects.

        :meta private:
        """
        return [self.input_key]

    @property
    def output_keys(self) -> List[str]:
        """Output keys to return.

        :meta private:
        """
        return ["raw", "errors", "code", "environment"]

    def prepare_context(
        self, query: str, variables: Optional[Mapping[str, Any]] = None
    ) -> Tuple[Environment, FewShotTemplate]:
        """Get the pre-populated environment and the few shot template.

        Args:
            query: The query to prepare the context for.
            variables: Any variables that should be added to the context.

        Returns:
            The prepopulated environment and a pre-formatted few shot template.
        """
        if self.context_retriever:
            external_function_definitions = self.context_retriever.retrieve(query)
        else:
            external_function_definitions = []

        environment = create_environment(external_function_definitions, variables)

        if self.example_retriever:
            formatted_examples = self.example_retriever.retrieve(query)
        else:
            formatted_examples = []

        external_functions = "\n".join(
            [
                self.ast_printer.visit(func_declaration)
                for func_declaration in environment.list_external_functions()
            ]
        )

        input_variables = self.instruction_template.input_variables

        formatting_variables = {}

        if "language_name" in input_variables:
            formatting_variables["language_name"] = self.language_name

        if external_functions:
            external_functions_block = (
                "You have access to the following external functions:\n\n"
                f"```{self.language_name}\n"
                f"{external_functions}\n"
                "```\n"
            )
        else:
            external_functions_block = "Do not assume any functions exist.\n"

        if "external_functions_block" in input_variables:
            formatting_variables["external_functions_block"] = external_functions_block

        prompt = self.instruction_template.partial(
            **formatting_variables,
        )

        return environment, FewShotTemplate(
            instruction_template=prompt,
            examples=formatted_examples,
            input_variables=["query"],
        )

    def _call(self, inputs: Dict[str, str]) -> CodeResult:  # type: ignore
        """Call the chain."""
        # Note not using original query!!
        # We remove the leading and trailing whitespace from the query
        # to make things a bit more robust.
        query = inputs[self.input_key].strip()

        variables: Mapping[str, Any] = cast(
            Mapping[str, Any], inputs.get("variables", {})
        )

        if not isinstance(variables, dict):
            raise TypeError(
                f"Variables must be a dictionary, got {type(variables)} instead."
            )

        environment, few_shot_template = self.prepare_context(query, variables)

        chain = few_shot_template | self.llm

        formatted_query = format_text(query, self.input_formatter)
        llm_output = chain.invoke({"query": formatted_query})

        # Extract content from AIMessage
        llm_output_content = llm_output.content
        code = unwrap_tag("code", llm_output_content)

        if not code:
            return {
                "errors": [
                    LLMParseException(
                        "Could not find code block. Please make sure the code "
                        "is wrapped in a code block."
                    )
                ],
                "raw": llm_output_content,
                "code": "",
                "environment": None,
            }

        interpreter_result = self.interpreter(code, environment)

        if interpreter_result["errors"]:
            return {
                "errors": interpreter_result["errors"],
                "raw": llm_output_content,
                "code": code,
                "environment": None,
            }

        return {
            "errors": [],
            "raw": llm_output_content,
            "code": code,
            "environment": interpreter_result["environment"],
        }

    @property
    def _chain_type(self) -> str:
        """Used for serialization."""
        return "code_chain"

    @classmethod
    def from_defaults(
        cls,
        *,
        llm: BaseLanguageModel,
        interpreter: Callable[[str, Environment], InterpreterResult] = run_interpreter,
        ast_printer: AbstractAstPrinter = AstPrinter(),
        context: Union[AbstractContextRetriever, Sequence[FuncLike], None] = None,
        examples: Union[AbstractExampleRetriever, Sequence[ExampleTuple], None] = None,
        instruction_template: PromptTemplate = DEFAULT_INSTRUCTION_PROMPT,
        input_key: str = "query",
        # Smirking kat language
        language_name: str = "😼",
        input_formatter: InputFormatter = "markdown_text",
    ) -> CodeChain:
        """Create a code chain from pre-configured defaults.

        Args:
            llm: The language model to use for coding
            interpreter: The interpreter that will be used to execute the program
            ast_printer: An ast printer that can print the AST as a text string
            context: Either a list of functions or a context retriever.
                               The list of functions can be a mixture of python
                               callables and Kork external functions.
                               All python functions will be converted into Kork
                               external functions, and everything passed into
                               the default context retriever.
            examples: An example retriever or a list of examples.
                       If a list of examples, a simple example retriever
                       will be created.
            instruction_template: Use to customize the instruction components of
                                  the prompt.
            language_name: The language name to use for the prompt.
            input_formatter: A formatting that will be applied to the input part
                             of each example tuple, if passing in a list of examples.
            input_key: The input key to use.

        Returns:
            A code chain
        """
        if isinstance(examples, (AbstractExampleRetriever, type(None))):
            _example_retriever = examples
        elif isinstance(examples, Sequence):
            formatted_examples = format_examples(
                language_name,
                examples,
                ast_printer,
                input_formatter=input_formatter,
            )
            _example_retriever = SimpleExampleRetriever(examples=formatted_examples)
        else:
            raise TypeError(
                f"example_retriever must be of type `AbstractExampleRetriever` or "
                f"`Sequence[ExampleTuple]`. Got {type(examples)} instead."
            )

        if isinstance(context, (AbstractContextRetriever, type(None))):
            _context_retriever = context
        elif isinstance(context, Sequence):
            _context_retriever = SimpleContextRetriever.from_functions(context)
        else:
            raise TypeError(
                f"context_retriever must be of type `AbstractContextRetriever` or "
                f"`Sequence[FunctionDefinition]`. Got {type(context)} "
                f"instead."
            )

        return cls(
            llm=llm,
            interpreter=interpreter,
            ast_printer=ast_printer,
            context_retriever=_context_retriever,
            example_retriever=_example_retriever,
            instruction_template=instruction_template,
            input_key=input_key,
            language_name=language_name,
            input_formatter=input_formatter,
        )
