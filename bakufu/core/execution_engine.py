"""Workflow execution engine for running steps sequentially"""

from collections.abc import Callable, Sequence
from typing import Any

from .ai_provider import (
    AIProvider,
    AIProviderConfig,
    AIProviderError,
    BaseAIProvider,
    MCPSamplingProvider,
)
from .base_types import WorkflowStep
from .collection_processors import CollectionProcessor
from .exceptions import (
    ErrorContext,
    StepExecutionError,
    TemplateError,
)
from .models import (
    AICallStep,
    AnyTextProcessStep,
    CollectionStep,
    ConditionalResult,
    ConditionalStep,
    ExecutionContext,
    Workflow,
)
from .validation import OutputValidator, ValidationConfig, ValidationError

# Remove duplicate StepExecutionError class as it's now imported from exceptions


class WorkflowExecutionEngine:
    """Engine for executing workflow steps"""

    def __init__(self, progress_callback: Callable | None = None) -> None:
        """Initialize execution engine"""
        self.progress_callback = progress_callback

    async def execute_workflow(
        self, workflow: Workflow, context: ExecutionContext
    ) -> dict[str, Any]:
        """Execute complete workflow with all steps"""
        results = {}

        # Notify workflow start
        if self.progress_callback:
            self.progress_callback(
                "workflow_start", workflow_name=workflow.name, total_steps=len(workflow.steps)
            )

        for i, step in enumerate(workflow.steps, 1):
            # Notify step start
            if self.progress_callback:
                self.progress_callback(
                    "workflow_step", current_step=i, step_name=step.id, step_type=step.type
                )

            try:
                result = await self.execute_step(step, context)
                context.set_step_output(step.id, result)
                results[step.id] = result

            except Exception as e:
                error_context = ErrorContext(
                    step_id=step.id, workflow_name=workflow.name, function_name="execute_workflow"
                )

                if isinstance(e, StepExecutionError):
                    error = e
                else:
                    error = StepExecutionError(
                        message=str(e),
                        step_id=step.id,
                        workflow_name=workflow.name,
                        context=error_context,
                        original_error=e,
                    )

                if step.on_error == "stop":
                    raise error from e
                elif step.on_error == "continue":
                    context.set_step_output(step.id, None)
                    results[step.id] = None
                    continue
                elif step.on_error == "skip_remaining":
                    context.set_step_output(step.id, None)
                    results[step.id] = None
                    break

        # Notify workflow completion
        if self.progress_callback:
            self.progress_callback("workflow_complete")

        return results

    async def execute_step(self, step: WorkflowStep, context: ExecutionContext) -> Any:
        """Execute a single workflow step"""
        if isinstance(step, AICallStep):
            return await self._execute_ai_call_step(step, context)
        elif isinstance(step, ConditionalStep):
            return await self._execute_conditional_step(step, context)
        elif step.type == "collection":
            return await self._execute_collection_step(step, context)
        elif hasattr(step, "method") and step.type == "text_process":
            return await self._execute_text_process_step(step, context)  # type: ignore
        else:
            raise StepExecutionError(
                message=f"Unknown step type: {type(step)}",
                step_id=step.id,
                context=ErrorContext(step_id=step.id, function_name="execute_step"),
                suggestions=[
                    "Check step type is 'ai_call', 'collection', 'conditional', or 'text_process'"
                ],
            )

    async def _execute_ai_call_step(self, step: AICallStep, context: ExecutionContext) -> str:
        """Execute AI API call step"""
        # Render prompt template
        try:
            rendered_prompt = context.render_template(step.prompt)
        except Exception as e:
            raise TemplateError(
                message=f"AI step prompt template rendering failed: {e}",
                template_content=step.prompt,
                line_number=getattr(e, "lineno", None),
                context=ErrorContext(step_id=step.id, function_name="_execute_ai_call_step"),
                original_error=e,
                suggestions=[
                    "Check prompt template syntax",
                    "Verify all variables are available in context",
                    f"Template: {step.prompt[:50]}...",
                ],
            ) from e

        # Create AI provider configuration
        provider_config = AIProviderConfig(
            provider=step.provider or context.config.default_provider,
            temperature=step.temperature if step.temperature is not None else 0.7,
            max_tokens=step.max_tokens,
            timeout=context.config.timeout_per_step,
            max_retries=3,
        )

        # Apply provider-specific settings if available
        provider_name = (
            provider_config.provider.split("/")[0]
            if "/" in provider_config.provider
            else provider_config.provider
        )
        if provider_name in context.config.provider_settings:
            provider_config.extra_params.update(context.config.provider_settings[provider_name])

        # Apply step-level ai_params (takes precedence over provider settings)
        if hasattr(step, "ai_params") and getattr(step, "ai_params", None):
            provider_config.extra_params.update(getattr(step, "ai_params", {}))

        try:
            # Choose provider based on sampling mode
            ai_provider: BaseAIProvider
            if context.sampling_mode and context.mcp_context:
                ai_provider = MCPSamplingProvider(context.mcp_context, provider_config)
            else:
                ai_provider = AIProvider(provider_config)

            # Handle validation if specified
            if step.validation:
                return await self._execute_ai_call_with_validation(
                    ai_provider, rendered_prompt, step, context
                )
            else:
                # Determine max_auto_retry_attempts (step-level override or global config)
                max_auto_retry_attempts = (
                    step.max_auto_retry_attempts
                    if step.max_auto_retry_attempts is not None
                    else context.config.max_auto_retry_attempts
                )

                # Prepare completion parameters
                completion_params = {}

                # Add max_tokens if specified in step
                if step.max_tokens is not None:
                    completion_params["max_tokens"] = step.max_tokens

                # Add temperature if specified in step
                if step.temperature is not None:
                    completion_params["temperature"] = step.temperature

                # Add auto-retry attempts if enabled
                if max_auto_retry_attempts > 0:
                    completion_params["max_auto_retry_attempts"] = max_auto_retry_attempts

                response = await ai_provider.complete(rendered_prompt, **completion_params)
                # Add usage information to context
                context.add_step_usage(step.id, response.usage, response.cost_usd)
                return response.content
        except AIProviderError as e:
            # AI provider errors are already well-structured
            raise StepExecutionError(
                message=f"AI provider error: {e!s}",
                step_id=step.id,
                context=ErrorContext(step_id=step.id, function_name="_execute_ai_call_step"),
                original_error=e,
                suggestions=[
                    "Check AI provider configuration",
                    "Verify API keys",
                    "Check network connectivity",
                ],
            ) from e
        except Exception as e:
            raise StepExecutionError(
                message=f"Unexpected AI call error: {e}",
                step_id=step.id,
                context=ErrorContext(step_id=step.id, function_name="_execute_ai_call_step"),
                original_error=e,
                suggestions=[
                    "Check AI provider configuration",
                    "Verify network connectivity",
                    "Check input prompt format",
                ],
            ) from e

    async def _execute_ai_call_with_validation(
        self, ai_provider: BaseAIProvider, prompt: str, step: AICallStep, context: ExecutionContext
    ) -> str:
        """Execute AI call with output validation and retry logic"""
        if step.validation is None:
            raise ValueError("Validation configuration is required")
        validation_config = ValidationConfig(**step.validation)
        validator = OutputValidator(validation_config)

        original_prompt = prompt
        current_prompt = prompt

        # Add JSON wrapper instruction if needed
        if validator.should_force_json_wrapper():
            current_prompt = f"{current_prompt}\n\n{validator.get_json_wrapper_instruction()}"

        for attempt in range(validation_config.max_retries + 1):
            try:
                # Determine max_auto_retry_attempts (step-level override or global config)
                max_auto_retry_attempts = (
                    step.max_auto_retry_attempts
                    if step.max_auto_retry_attempts is not None
                    else context.config.max_auto_retry_attempts
                )

                # Prepare completion parameters for validation
                validation_params = {}

                # Add max_tokens if specified in step
                if step.max_tokens is not None:
                    validation_params["max_tokens"] = step.max_tokens

                # Add temperature if specified in step
                if step.temperature is not None:
                    validation_params["temperature"] = step.temperature

                # Add auto-retry attempts if enabled
                if max_auto_retry_attempts > 0:
                    validation_params["max_auto_retry_attempts"] = max_auto_retry_attempts

                response = await ai_provider.complete(current_prompt, **validation_params)

                # Add usage information to context
                context.add_step_usage(step.id, response.usage, response.cost_usd)

                # Validate the response
                validation_result = validator.validate(response.content, attempt + 1)

                if validation_result.is_valid:
                    # Return the validated output (could be parsed JSON or original text)
                    return validation_result.validated_output or response.content

                # Validation failed, prepare for retry
                if attempt < validation_config.max_retries:
                    retry_prompt_suffix = validator.get_retry_prompt(validation_result)
                    current_prompt = f"{original_prompt}\n\n{retry_prompt_suffix}"
                    continue
                else:
                    # All retries exhausted
                    raise ValidationError(
                        f"Validation failed after {validation_config.max_retries + 1} attempts",
                        response.content,
                        validation_result.errors,
                    )

            except ValidationError:
                raise
            except AIProviderError as e:
                # Re-raise AI provider errors as-is
                raise StepExecutionError(
                    message=f"AI provider error during validation attempt {attempt + 1}: {e!s}",
                    step_id=step.id,
                    context=ErrorContext(
                        step_id=step.id, function_name="_execute_ai_call_with_validation"
                    ),
                    original_error=e,
                    suggestions=[
                        "Check AI provider configuration",
                        "Verify API keys",
                        "Check network connectivity",
                    ],
                ) from e
            except Exception as e:
                if attempt < validation_config.max_retries:
                    continue
                else:
                    raise StepExecutionError(
                        message=f"Unexpected error during validated AI call: {e}",
                        step_id=step.id,
                        context=ErrorContext(
                            step_id=step.id, function_name="_execute_ai_call_with_validation"
                        ),
                        original_error=e,
                        suggestions=[
                            "Check validation configuration",
                            "Verify JSON schema format",
                            "Check custom validation function",
                        ],
                    ) from e

        # This should never be reached
        raise RuntimeError("Validation loop completed without returning a result")

    async def _execute_collection_step(self, step: WorkflowStep, context: ExecutionContext) -> Any:
        """Execute collection operation step"""
        # Render input template to get the collection
        input_attr = getattr(step, "input", None)
        if not input_attr:
            raise StepExecutionError(
                message="Collection step missing required 'input' attribute",
                step_id=step.id,
                workflow_name=context.workflow_name,
            )

        try:
            input_data = context.render_template_object(input_attr)
        except Exception as e:
            raise TemplateError(
                message=f"Collection step input template rendering failed: {e}",
                template_content=str(input_attr),
                line_number=getattr(e, "lineno", None),
                context=ErrorContext(step_id=step.id, function_name="_execute_collection_step"),
                original_error=e,
                suggestions=[
                    "Check input template syntax",
                    "Verify all variables are available in context",
                    f"Template: {str(input_attr)[:50]}...",
                ],
            ) from e

        # Create and execute collection processor
        try:
            # Cast step to CollectionStep since we know it has the right type
            from typing import cast

            collection_step = cast(CollectionStep, step)
            processor = CollectionProcessor(collection_step, self.progress_callback)
            result = await processor.process(input_data, context)

            # Return the output, but store the full CollectionResult for debugging
            # For now, we return just the output to maintain compatibility
            return result.output

        except StepExecutionError:
            # Re-raise StepExecutionError as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise StepExecutionError(
                message=f"Collection operation failed: {e}",
                step_id=step.id,
                context=ErrorContext(step_id=step.id, function_name="_execute_collection_step"),
                original_error=e,
                suggestions=[
                    f"Check {getattr(step, 'operation', 'unknown')} operation configuration",
                    "Verify input data is a list/array",
                    "Check operation-specific parameters",
                ],
            ) from e

    async def _execute_text_process_step(
        self,
        step: AnyTextProcessStep,
        context: ExecutionContext,
    ) -> Any:
        """Execute text processing step using polymorphic processors"""
        # Render input template
        try:
            input_text = context.render_template(step.input)
        except Exception as e:
            raise TemplateError(
                message=f"Text processing step input template rendering failed: {e}",
                template_content=step.input,
                line_number=getattr(e, "lineno", None),
                context=ErrorContext(step_id=step.id, function_name="_execute_text_process_step"),
                original_error=e,
                suggestions=[
                    "Check input template syntax",
                    "Verify all variables are available in context",
                    f"Template: {step.input[:50]}...",
                ],
            ) from e

        # Use direct process method on step
        try:
            return await step.process(input_text, step.id)
        except StepExecutionError:
            # Re-raise StepExecutionError as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise StepExecutionError(
                message=f"Text processing failed: {e}",
                step_id=step.id,
                context=ErrorContext(step_id=step.id, function_name="_execute_text_process_step"),
                original_error=e,
                suggestions=[
                    f"Check {step.method} method configuration",
                    "Verify input text format",
                ],
            ) from e

    async def _execute_conditional_step(
        self, step: ConditionalStep, context: ExecutionContext
    ) -> ConditionalResult:
        """Execute conditional step with if-else or multi-branch logic"""
        try:
            if step.condition is not None:
                # Basic if-else structure
                return await self._execute_basic_conditional(step, context)
            elif step.conditions is not None:
                # Multi-branch structure
                return await self._execute_multi_branch_conditional(step, context)
            else:
                raise StepExecutionError(
                    message="Conditional step has neither 'condition' nor 'conditions' field",
                    step_id=step.id,
                    context=ErrorContext(
                        step_id=step.id, function_name="_execute_conditional_step"
                    ),
                    suggestions=["Check conditional step configuration"],
                )
        except (StepExecutionError, TemplateError):
            # Re-raise StepExecutionError and TemplateError as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise StepExecutionError(
                message=f"Conditional step execution failed: {e}",
                step_id=step.id,
                context=ErrorContext(step_id=step.id, function_name="_execute_conditional_step"),
                original_error=e,
                suggestions=[
                    "Check conditional step configuration",
                    "Verify condition template syntax",
                ],
            ) from e

    async def _execute_basic_conditional(
        self, step: ConditionalStep, context: ExecutionContext
    ) -> ConditionalResult:
        """Execute basic if-else conditional structure"""
        condition_result = None
        evaluation_error = None
        executed_branch = None
        output = None

        # Evaluate condition
        try:
            condition_result_raw = context.render_template_object(step.condition or "")
            # Handle different types that Jinja2 might return
            if isinstance(condition_result_raw, str):
                # If it's a string representation, evaluate it as Python expression
                condition_result = condition_result_raw.lower() in ("true", "1", "yes")
            else:
                condition_result = bool(condition_result_raw)
        except Exception as e:
            evaluation_error = str(e)
            # Handle condition evaluation error based on configuration
            if step.on_condition_error == "stop":
                raise TemplateError(
                    message=f"Condition evaluation failed: {e}",
                    template_content=step.condition or "",
                    line_number=getattr(e, "lineno", None),
                    context=ErrorContext(
                        step_id=step.id, function_name="_execute_basic_conditional"
                    ),
                    original_error=e,
                    suggestions=[
                        "Check condition template syntax",
                        "Verify all variables are available in context",
                        f"Condition: {step.condition}",
                    ],
                ) from e
            elif step.on_condition_error == "continue":
                # Treat as false and continue
                condition_result = False
            elif step.on_condition_error == "skip_remaining":
                # Return empty result
                return ConditionalResult(
                    output=None,
                    condition_result=None,
                    executed_branch=None,
                    evaluation_error=evaluation_error,
                )

        # Execute appropriate branch
        try:
            if condition_result and step.if_true:
                executed_branch = "if_true"
                output = await self._execute_step_list(step.if_true, context)
            elif not condition_result and step.if_false:
                executed_branch = "if_false"
                output = await self._execute_step_list(step.if_false, context)
            # If no matching branch, output remains None
        except Exception:
            # Handle execution errors in branches based on parent step's on_error setting
            if step.on_error == "stop":
                raise
            elif step.on_error in {"continue", "skip_remaining"}:
                output = None

        return ConditionalResult(
            output=output,
            condition_result=condition_result,
            executed_branch=executed_branch,
            evaluation_error=evaluation_error,
        )

    async def _execute_multi_branch_conditional(
        self, step: ConditionalStep, context: ExecutionContext
    ) -> ConditionalResult:
        """Execute multi-branch conditional structure"""
        condition_result = None
        evaluation_error = None
        executed_branch = None
        output = None

        # Evaluate conditions in order until one matches
        for branch in step.conditions or []:
            if branch.default:
                # Default branch - execute if no other branch matched
                if executed_branch is None:
                    executed_branch = branch.name
                    output = await self._execute_step_list(branch.steps, context)
                    condition_result = True  # Default branch is considered "true"
                break
            else:
                # Regular condition branch
                try:
                    condition_result_raw = context.render_template_object(branch.condition)
                    # Handle different types that Jinja2 might return
                    if isinstance(condition_result_raw, str):
                        # If it's a string representation, evaluate it as Python expression
                        condition_result = condition_result_raw.lower() in ("true", "1", "yes")
                    else:
                        condition_result = bool(condition_result_raw)

                    if condition_result:
                        executed_branch = branch.name
                        output = await self._execute_step_list(branch.steps, context)
                        break
                except Exception as e:
                    evaluation_error = str(e)
                    # Handle condition evaluation error
                    if step.on_condition_error == "stop":
                        raise TemplateError(
                            message=f"Branch '{branch.name}' condition evaluation failed: {e}",
                            template_content=branch.condition,
                            line_number=getattr(e, "lineno", None),
                            context=ErrorContext(
                                step_id=step.id, function_name="_execute_multi_branch_conditional"
                            ),
                            original_error=e,
                            suggestions=[
                                "Check branch condition template syntax",
                                "Verify all variables are available in context",
                                f"Branch: {branch.name}, Condition: {branch.condition}",
                            ],
                        ) from e
                    elif step.on_condition_error == "continue":
                        # Skip this branch and continue to next
                        continue
                    elif step.on_condition_error == "skip_remaining":
                        # Return empty result
                        return ConditionalResult(
                            output=None,
                            condition_result=None,
                            executed_branch=None,
                            evaluation_error=evaluation_error,
                        )

        # If no branch was executed, set condition_result to None for multi-branch
        if executed_branch is None and not evaluation_error:
            condition_result = None

        return ConditionalResult(
            output=output,
            condition_result=condition_result,
            executed_branch=executed_branch,
            evaluation_error=evaluation_error,
        )

    async def _execute_step_list(
        self, steps: Sequence[WorkflowStep], context: ExecutionContext
    ) -> Any:
        """Execute a list of steps and return the output of the last step"""
        last_output = None

        for step in steps:
            result = await self.execute_step(step, context)
            context.set_step_output(step.id, result)
            last_output = result

        return last_output
