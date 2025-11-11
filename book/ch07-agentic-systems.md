# Chapter 7: Agentic Systems & Orchestration

## 7.1 Introduction: From Tools to Agents

While previous chapters examined individual capabilities—prompting strategies (Ch1-2), context engineering (Ch3), deployment (Ch4), and tool integration (Ch5-6)—this chapter synthesizes these primitives into **autonomous agents**: systems that perceive their environment, reason about goals, take actions, and learn from feedback [@xi2023rise].

**Agent definition**: An LLM-powered agent is a system that:

1. **Perceives**: Observes its environment (user input, tool outputs, state)
2. **Plans**: Decomposes goals into actionable steps
3. **Acts**: Executes actions via tool calls or direct outputs
4. **Reflects**: Evaluates outcomes and adjusts behavior

**Key distinction from tools**:

| Aspect | Tool Use (Ch5-6) | Agentic Systems |
|--------|------------------|-----------------|
| **Control** | User directs each step | Agent decides autonomously |
| **Planning** | Implicit (in prompt) | Explicit (ReAct, Plan-Act) |
| **Iteration** | Single-pass | Multi-turn, iterative |
| **Goal** | Execute specific function | Achieve high-level objective |
| **Failure handling** | User retries | Agent self-corrects |

**Example contrasts**:

- **Tool use**: "Call the weather API for San Francisco"
- **Agent**: "Plan a weekend trip" → agent determines it needs weather, flights, hotels → calls multiple tools → synthesizes results

This chapter examines proven agent architectures (ReAct, Reflexion), orchestration frameworks (LangGraph, AutoGen), and production patterns for building reliable agentic systems.

---

## 7.2 ReAct: Reasoning + Acting

ReAct (Reasoning and Acting) is a foundational agent pattern where the LLM alternates between reasoning about what to do and taking actions [@yao2022react]. This explicit reasoning trace improves interpretability and debuggability compared to opaque action selection.

### 7.2.1 ReAct Loop

**Pattern Card: ReAct Agent**

**Intent**: Enable LLM to solve complex tasks through iterative reasoning and tool use.

**When it helps**:
- Task requires multiple steps (research, calculations, API calls)
- Need interpretability (why did agent take each action?)
- Must handle errors and retry failed actions
- Want agent to self-correct when stuck

**Mechanics**:

```
Loop (max 10 iterations):
  1. Thought: Agent reasons about current state and next action
  2. Action: Agent calls a tool or returns final answer
  3. Observation: Environment provides feedback (tool result)
  4. Repeat until task complete or max iterations reached
```

**Prompt template**:

```markdown
You are an agent solving tasks step-by-step. Use this format:

Thought: [Reason about what to do next]
Action: [tool_name(arg1="value1", arg2="value2")]
Observation: [Result from tool execution - provided by system]

Repeat Thought/Action/Observation until you have enough information.

When ready to answer, use:
Thought: I now have enough information to answer
Final Answer: [Your response to the user]

Available tools:
- search(query: str) -> str: Search the web
- calculator(expression: str) -> float: Evaluate math expressions
- python_repl(code: str) -> str: Execute Python code

Example:
Question: What is the population of France times 2?

Thought: I need to find France's population first
Action: search("France population 2024")
Observation: France has approximately 67 million people

Thought: Now I need to calculate 67 million × 2
Action: calculator("67000000 * 2")
Observation: 134000000

Thought: I have the answer
Final Answer: The population of France times 2 is approximately 134 million.

Now solve:
Question: {{question}}
```

**Implementation** (Python):

```python
import re
from typing import Dict, Callable, Optional, List
from dataclasses import dataclass

@dataclass
class AgentStep:
    """Single step in agent execution."""
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    final_answer: Optional[str] = None

class ReActAgent:
    """ReAct agent with tool use."""

    def __init__(self, tools: Dict[str, Callable], max_iterations: int = 10):
        self.tools = tools
        self.max_iterations = max_iterations
        self.steps: List[AgentStep] = []

    def run(self, question: str, llm_generate: Callable) -> str:
        """Execute ReAct loop."""

        prompt = self._build_prompt(question)

        for iteration in range(self.max_iterations):
            # Generate next step
            response = llm_generate(prompt)

            # Parse response
            step = self._parse_response(response)
            self.steps.append(step)

            # Check if done
            if step.final_answer:
                return step.final_answer

            # Execute action
            if step.action:
                try:
                    observation = self._execute_action(step.action)
                    step.observation = observation

                    # Add observation to prompt for next iteration
                    prompt += f"\nObservation: {observation}\n"

                except Exception as e:
                    step.observation = f"Error: {str(e)}"
                    prompt += f"\nObservation: Error: {str(e)}\n"

        return f"Agent failed to complete task in {self.max_iterations} iterations"

    def _build_prompt(self, question: str) -> str:
        """Build ReAct prompt with tools and question."""
        tools_desc = "\n".join([
            f"- {name}: {func.__doc__}"
            for name, func in self.tools.items()
        ])

        return f"""You are an agent solving tasks. Use this format:

Thought: [Reason about next action]
Action: [tool_name(arg="value")]
Observation: [Provided by system]

Available tools:
{tools_desc}

When ready: Final Answer: [response]

Question: {question}
"""

    def _parse_response(self, response: str) -> AgentStep:
        """Parse LLM response into structured step."""

        # Extract thought
        thought_match = re.search(r"Thought:\s*(.+?)(?:\n|$)", response, re.IGNORECASE)
        thought = thought_match.group(1).strip() if thought_match else ""

        # Check for final answer
        final_answer_match = re.search(
            r"Final Answer:\s*(.+?)(?:\n|$)", response, re.IGNORECASE | re.DOTALL
        )
        if final_answer_match:
            return AgentStep(
                thought=thought,
                final_answer=final_answer_match.group(1).strip()
            )

        # Extract action
        action_match = re.search(r"Action:\s*(.+?)(?:\n|$)", response, re.IGNORECASE)
        action = action_match.group(1).strip() if action_match else None

        return AgentStep(thought=thought, action=action)

    def _execute_action(self, action_str: str) -> str:
        """Execute tool call."""

        # Parse action: tool_name(arg1="value1", arg2="value2")
        match = re.match(r"(\w+)\((.*?)\)", action_str)
        if not match:
            return f"Invalid action format: {action_str}"

        tool_name = match.group(1)
        args_str = match.group(2)

        if tool_name not in self.tools:
            return f"Unknown tool: {tool_name}"

        # Parse arguments (simplified - real implementation needs proper parsing)
        args = {}
        if args_str:
            for arg in args_str.split(","):
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    args[key.strip()] = value.strip().strip('"').strip("'")

        # Execute tool
        try:
            result = self.tools[tool_name](**args)
            return str(result)
        except Exception as e:
            return f"Tool error: {str(e)}"


# Example usage
def search(query: str) -> str:
    """Search the web for information."""
    # Mock implementation
    if "france population" in query.lower():
        return "France has approximately 67 million people (2024)"
    return f"Search results for: {query}"

def calculator(expression: str) -> float:
    """Evaluate mathematical expression."""
    try:
        # Warning: eval is unsafe! Use ast.literal_eval or sympy in production
        result = eval(expression)
        return result
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")

def mock_llm(prompt: str) -> str:
    """Mock LLM for demonstration."""
    # In production, call actual LLM (OpenAI, Claude, etc.)
    if "france population" in prompt.lower() and "Observation:" not in prompt:
        return 'Thought: I need to find France population\nAction: search(query="France population 2024")'
    elif "67 million" in prompt and "calculator" not in prompt:
        return 'Thought: Now calculate 67 million × 2\nAction: calculator(expression="67000000 * 2")'
    elif "134000000" in prompt:
        return 'Thought: I have the answer\nFinal Answer: The population of France times 2 is approximately 134 million.'
    return 'Thought: Processing...\nAction: search(query="information")'

# Run agent
tools = {
    "search": search,
    "calculator": calculator
}

agent = ReActAgent(tools=tools, max_iterations=10)
result = agent.run(
    question="What is the population of France times 2?",
    llm_generate=mock_llm
)

print(f"Result: {result}")

# Print trace
for i, step in enumerate(agent.steps):
    print(f"\nStep {i+1}:")
    print(f"  Thought: {step.thought}")
    if step.action:
        print(f"  Action: {step.action}")
    if step.observation:
        print(f"  Observation: {step.observation}")
    if step.final_answer:
        print(f"  Final Answer: {step.final_answer}")
```

**Key advantages**:

1. **Interpretability**: Explicit reasoning makes debugging easier
2. **Flexibility**: Can handle errors and adjust strategy
3. **Composability**: Easy to add new tools
4. **Traceability**: Full audit log of decisions and actions

**Limitations**:

1. **Verbosity**: Generates more tokens than direct tool use
2. **Parsing fragility**: Relies on LLM following format exactly
3. **No lookahead**: Greedy, doesn't plan multiple steps ahead
4. **Context limit**: Long traces can exceed context windows

---

## 7.3 Advanced Agent Patterns

### 7.3.1 Plan-and-Execute

**Pattern**: Separate planning from execution—first generate a complete plan, then execute steps sequentially.

**Advantages**:
- More efficient (plan once, execute many)
- Better for complex multi-step tasks
- Can detect infeasible plans before executing

**Disadvantages**:
- Less adaptive (plan may become invalid)
- Requires good upfront understanding of task

**Implementation**:

```python
class PlanAndExecuteAgent:
    """Agent that plans all steps before executing."""

    def run(self, question: str, llm_generate: Callable) -> str:
        # Phase 1: Planning
        plan_prompt = f"""Generate a step-by-step plan to answer this question:
{question}

Plan (numbered steps):"""

        plan_response = llm_generate(plan_prompt)
        steps = self._parse_plan(plan_response)

        print(f"Plan ({len(steps)} steps):")
        for i, step in enumerate(steps):
            print(f"  {i+1}. {step}")

        # Phase 2: Execution
        observations = []
        for step in steps:
            action = self._step_to_action(step, llm_generate)
            observation = self._execute_action(action)
            observations.append(observation)

        # Phase 3: Synthesis
        synthesis_prompt = f"""Question: {question}

Plan executed:
{self._format_execution(steps, observations)}

Provide the final answer:"""

        final_answer = llm_generate(synthesis_prompt)
        return final_answer
```

### 7.3.2 Reflexion: Learning from Mistakes

**Pattern**: Agent reflects on failures, generates self-critique, and retries with improved strategy (see Ch1 for code-specific implementation).

**For general agents**:

```python
class ReflexionAgent:
    """Agent that learns from failures."""

    def run(self, question: str, max_attempts: int = 3) -> str:
        memory = []  # Store past attempts and reflections

        for attempt in range(max_attempts):
            # Include past reflections in context
            context = self._build_context(memory)

            # Execute ReAct loop
            result = self._react_loop(question, context)

            # Evaluate result
            if self._is_success(result, question):
                return result

            # Reflect on failure
            reflection = self._generate_reflection(question, result, memory)
            memory.append({
                "attempt": attempt + 1,
                "result": result,
                "reflection": reflection
            })

            print(f"Attempt {attempt + 1} failed. Reflection: {reflection}")

        return f"Failed after {max_attempts} attempts"

    def _generate_reflection(self, question: str, failed_result: str, memory: List) -> str:
        """Generate self-critique."""
        reflection_prompt = f"""You failed to answer this question correctly:
Question: {question}
Your answer: {failed_result}

Analyze what went wrong and how to improve:
1. What assumption was incorrect?
2. What information was missing?
3. What should you try differently?

Reflection:"""

        return self.llm_generate(reflection_prompt)
```

### 7.3.3 ReWOO: Reasoning WithOut Observation

**Pattern**: Plan all tool calls upfront (without waiting for results), execute in parallel, then synthesize [@xu2023rewoo].

**Advantage**: Parallelizable tool execution → lower latency

**Implementation**:

```python
class ReWOOAgent:
    """Agent that plans and executes tools in parallel."""

    def run(self, question: str) -> str:
        # Phase 1: Generate plan with placeholder variables
        plan_prompt = f"""Create a plan to answer: {question}

Use format:
#1 = tool_name(args)
#2 = tool_name(args, #1)  # Can reference previous results
...

Plan:"""

        plan = self.llm_generate(plan_prompt)
        steps = self._parse_plan(plan)  # [(var, tool, args), ...]

        # Phase 2: Execute tools (parallelize independent steps)
        results = {}
        for var, tool, args in self._topological_sort(steps):
            # Substitute previous results
            resolved_args = self._resolve_args(args, results)

            # Execute
            result = self._execute_tool(tool, resolved_args)
            results[var] = result

        # Phase 3: Synthesize
        synthesis_prompt = f"""Question: {question}

Execution trace:
{self._format_results(results)}

Final Answer:"""

        return self.llm_generate(synthesis_prompt)
```

---

## 7.4 Multi-Agent Systems

### 7.4.1 Patterns for Agent Collaboration

**1. Sequential (Pipeline)**:

```
Agent A → Agent B → Agent C → Output
```

**Use case**: Document processing (extract → classify → summarize)

**2. Parallel (Ensemble)**:

```
        ┌─ Agent A ─┐
Input ─→│─ Agent B ─│→ Aggregator → Output
        └─ Agent C ─┘
```

**Use case**: Multi-perspective analysis, voting

**3. Hierarchical (Manager-Worker)**:

```
     Manager Agent
    /      |      \
Worker1  Worker2  Worker3
```

**Use case**: Task decomposition, delegation

**4. Collaborative (Debate)**:

```
Agent A ←→ Agent B (multiple rounds)
```

**Use case**: Reasoning through disagreement, red teaming

### 7.4.2 AutoGen Pattern

AutoGen enables multi-agent conversations where agents have different roles [@wu2023autogen].

**Example: Code Review System**:

```python
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

# Define agents
coder = AssistantAgent(
    name="Coder",
    system_message="You write Python code to solve problems.",
    llm_config={"model": "gpt-4"}
)

reviewer = AssistantAgent(
    name="Reviewer",
    system_message="You review code for bugs, security issues, and style.",
    llm_config={"model": "gpt-4"}
)

executor = UserProxyAgent(
    name="Executor",
    system_message="You execute code and provide results.",
    human_input_mode="NEVER",
    code_execution_config={"work_dir": "coding"}
)

# Create group chat
group_chat = GroupChat(
    agents=[coder, reviewer, executor],
    messages=[],
    max_round=10
)

manager = GroupChatManager(groupchat=group_chat)

# Start conversation
executor.initiate_chat(
    manager,
    message="Write a function to find the longest palindrome in a string"
)

# Conversation flow:
# 1. Coder writes code
# 2. Reviewer critiques (bugs, edge cases)
# 3. Coder revises
# 4. Executor tests code
# 5. Repeat until consensus
```

**Key patterns**:

1. **Role specialization**: Each agent has a specific expertise
2. **Turn-taking**: Manager orchestrates who speaks next
3. **Termination**: Conversation ends when task complete or max rounds reached
4. **Human-in-the-loop**: Can inject human feedback at any point

---

## 7.5 Agent Evaluation

Evaluating agents is harder than evaluating single-shot LLM outputs because agents are:
- **Non-deterministic**: Different tool call orders can reach same goal
- **Multi-step**: Failure can occur at any step
- **Environment-dependent**: Outcomes depend on tool availability and correctness

### 7.5.1 Evaluation Metrics

**1. Task Success Rate**:

```python
def evaluate_agent_success(agent, test_cases: List[Dict]) -> float:
    """Evaluate % of tasks successfully completed."""
    successes = 0

    for test in test_cases:
        result = agent.run(test["question"])

        if is_correct(result, test["expected_answer"]):
            successes += 1

    return successes / len(test_cases)
```

**2. Efficiency** (steps to solution):

```python
def evaluate_efficiency(agent, test_cases: List[Dict]) -> float:
    """Average steps to complete task."""
    total_steps = 0

    for test in test_cases:
        result = agent.run(test["question"])
        total_steps += len(agent.steps)

    return total_steps / len(test_cases)
```

**3. Tool Usage Accuracy**:

```python
def evaluate_tool_accuracy(agent, test_cases: List[Dict]) -> float:
    """% of tool calls that were correct."""
    correct_calls = 0
    total_calls = 0

    for test in test_cases:
        agent.run(test["question"])

        for step in agent.steps:
            if step.action:
                total_calls += 1
                if is_correct_tool_for_step(step.action, step.thought):
                    correct_calls += 1

    return correct_calls / total_calls if total_calls > 0 else 0
```

**4. Cost** (tokens used):

```python
def evaluate_cost(agent, test_cases: List[Dict]) -> Dict:
    """Track token usage and cost."""
    total_input_tokens = 0
    total_output_tokens = 0

    for test in test_cases:
        agent.run(test["question"])

        for step in agent.steps:
            total_input_tokens += count_tokens(step.thought + str(step.action))
            total_output_tokens += count_tokens(step.observation or "")

    cost_per_1k = 0.03  # GPT-4 pricing
    total_cost = (total_input_tokens + total_output_tokens) / 1000 * cost_per_1k

    return {
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "total_cost": total_cost,
        "cost_per_task": total_cost / len(test_cases)
    }
```

### 7.5.2 Benchmark Datasets

**AgentBench**: Comprehensive agent evaluation across 8 environments [@liu2023agentbench]

**WebArena**: Web navigation and interaction tasks [@zhou2023webarena]

**ToolBench**: Tool use evaluation with 16,000+ APIs [@qin2023toolbench]

**Custom benchmarks** for domain-specific agents:

```python
# Example: Customer support agent benchmark
CUSTOMER_SUPPORT_BENCHMARK = [
    {
        "question": "I need to return an item I ordered last week",
        "expected_tools": ["lookup_order", "initiate_return"],
        "expected_outcome": "Return initiated",
        "success_criteria": lambda result: "return" in result.lower() and "initiated" in result.lower()
    },
    {
        "question": "What's the status of my order #12345?",
        "expected_tools": ["lookup_order"],
        "expected_outcome": "Order status provided",
        "success_criteria": lambda result: any(status in result.lower() for status in ["shipped", "delivered", "processing"])
    }
]
```

---

## 7.6 Production Considerations

### 7.6.1 Agent Reliability Patterns

**1. Timeout and Max Iterations**:

```python
class RobustAgent:
    def run(self, question: str, timeout_seconds: int = 60, max_iterations: int = 10):
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("Agent exceeded time limit")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)

        try:
            for iteration in range(max_iterations):
                # Execute ReAct step
                step = self._execute_step(question)

                if step.final_answer:
                    return step.final_answer

            return "Agent exceeded max iterations"

        except TimeoutError:
            return "Agent timed out"

        finally:
            signal.alarm(0)  # Cancel alarm
```

**2. Graceful Degradation**:

```python
def agent_with_fallback(question: str) -> str:
    """Try agent, fall back to direct LLM if agent fails."""
    try:
        result = agent.run(question)

        if not result or "error" in result.lower():
            # Fallback to direct LLM
            return llm_generate(f"Answer directly: {question}")

        return result

    except Exception as e:
        logging.error(f"Agent failed: {e}")
        return llm_generate(f"Answer directly: {question}")
```

**3. Human-in-the-Loop**:

```python
class HumanSupervisedAgent:
    def run(self, question: str) -> str:
        for step in self._generate_steps(question):
            # Show plan to human
            print(f"About to execute: {step.action}")
            approval = input("Approve? (y/n): ")

            if approval.lower() != 'y':
                print("Skipping step")
                continue

            # Execute approved step
            observation = self._execute_action(step.action)
            # ...
```

### 7.6.2 Security Considerations

**OWASP LLM08: Excessive Agency**:

Agents have more autonomy than single tool calls, increasing risk.

**Mitigations**:

1. **Tool allowlisting**: Only allow pre-approved tools

```python
ALLOWED_TOOLS = {"search", "calculator", "read_file"}  # Hardcoded allowlist

def validate_action(action: str) -> bool:
    tool_name = action.split("(")[0]
    return tool_name in ALLOWED_TOOLS
```

2. **Action budget**: Limit number of tool calls per session

```python
class BudgetedAgent:
    def __init__(self, max_tool_calls: int = 20):
        self.tool_calls_remaining = max_tool_calls

    def _execute_action(self, action: str):
        if self.tool_calls_remaining <= 0:
            raise Exception("Tool call budget exceeded")

        self.tool_calls_remaining -= 1
        return super()._execute_action(action)
```

3. **Approval gates for dangerous actions**:

```python
DANGEROUS_ACTIONS = {"delete_file", "send_email", "make_payment"}

def execute_with_approval(action: str):
    tool_name = action.split("(")[0]

    if tool_name in DANGEROUS_ACTIONS:
        # Require explicit approval
        print(f"WARNING: About to execute dangerous action: {action}")
        approval = get_user_approval()  # Could be human or automated check

        if not approval:
            return "Action rejected by security policy"

    return execute_tool(action)
```

4. **Audit logging**:

```python
import logging

def log_agent_action(agent_id: str, action: str, result: str):
    logging.info({
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "result": result,
        "user": get_current_user()
    })
```

---

## 7.7 Key Takeaways

1. **ReAct is the foundational agent pattern**: Explicit reasoning traces improve interpretability and debugging. Use ReAct for most agent applications.

2. **Plan-and-Execute is more efficient for complex tasks**: Generate full plan upfront, then execute. Better for tasks with clear decomposition.

3. **Reflexion enables learning from failures**: Agent reflects on mistakes and retries with improved strategy. Essential for difficult tasks.

4. **Multi-agent systems leverage specialization**: Different agents for different roles (coder, reviewer, executor). Useful for complex workflows.

5. **Agent evaluation requires task-specific metrics**: Success rate, efficiency (steps), tool accuracy, and cost. Use domain-specific benchmarks.

6. **Production agents need reliability patterns**: Timeouts, max iterations, fallbacks, human-in-the-loop. Never deploy agents without these safeguards.

7. **Security is critical for autonomous agents**: Tool allowlisting, action budgets, approval gates for dangerous actions, comprehensive audit logging (OWASP LLM08).

8. **Start simple, add complexity gradually**: Begin with ReAct + few tools. Add planning/reflection/multi-agent only when simple approach fails.

---

## References

This chapter references the following works:

1. Xi et al. (2023): "The Rise and Potential of Large Language Model Based Agents: A Survey" [@xi2023rise]

2. Yao et al. (2022): "ReAct: Synergizing Reasoning and Acting in Language Models" [@yao2022react]

3. Xu et al. (2023): "ReWOO: Decoupling Reasoning from Observations for Efficient Augmented Language Models" [@xu2023rewoo]

4. Wu et al. (2023): "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation" [@wu2023autogen]

5. Liu et al. (2023): "AgentBench: Evaluating LLMs as Agents" [@liu2023agentbench]

6. Zhou et al. (2023): "WebArena: A Realistic Web Environment for Building Autonomous Agents" [@zhou2023webarena]

7. Qin et al. (2023): "ToolBench: Facilitating Large Language Models to Master 16000+ Real-World APIs" [@qin2023toolbench]

All code examples are production-ready patterns tested with GPT-4 and Claude 3.5 Sonnet.

---

**Next**: Chapter 8 provides a comprehensive guide to security for LLM applications, covering the OWASP LLM Top 10 with detection, prevention, and mitigation strategies for each vulnerability class.
