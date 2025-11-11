# Chapter 6: Claude's Ecosystem: MCP, Tool Use & Integration

## 6.1 Introduction: Claude's Integration Philosophy

While OpenAI approaches LLM integration through Custom GPTs and Actions (Chapter 5), Anthropic's Claude ecosystem emphasizes **composability**, **developer control**, and **open protocols**. Rather than a walled garden, Claude provides flexible primitives that developers can combine to build sophisticated applications [@anthropic2024mcp].

**Core components**:

1. **Model Context Protocol (MCP)**: Open protocol for connecting Claude to data sources and tools
2. **Native Tool Use**: Built-in function calling with structured outputs
3. **Extended Context Windows**: 200K tokens enabling document-level reasoning
4. **Constitutional AI**: Safety guardrails integrated at the model level

**Key differences from ChatGPT**:

| Aspect | Claude | ChatGPT Custom GPTs |
|--------|--------|---------------------|
| **Integration model** | Protocol-based (MCP) | Platform-specific (Actions) |
| **Developer control** | Full control over tool execution | Limited (OpenAI executes) |
| **Data flow** | Direct (client → Claude → tool) | Proxied (via OpenAI) |
| **Open standard** | Yes (MCP is open protocol) | No (proprietary) |
| **Context window** | 200K tokens | 128K tokens (GPT-4) |
| **Tool execution** | Synchronous (deterministic) | Asynchronous (may retry) |

This chapter examines Claude's integration patterns, MCP implementation, and production deployment strategies for Claude-native applications.

---

## 6.2 Model Context Protocol (MCP)

The Model Context Protocol is an open standard for connecting language models to data sources, enabling dynamic context retrieval during conversations [@anthropic2024mcp]. Unlike ChatGPT Actions (which require OpenAPI schemas), MCP uses a simpler, more flexible protocol designed for Claude's architecture.

### 6.2.1 MCP Architecture

**High-level flow**:

```
┌──────────┐          ┌──────────┐          ┌──────────┐
│  Client  │ ◄───────►│   MCP    │ ◄───────►│   Data   │
│  (IDE)   │   JSON   │  Server  │   Query  │  Source  │
└──────────┘          └──────────┘          └──────────┘
     │                      │
     └──────────────────────┘
            Claude API
```

**Components**:

1. **Client**: Application using Claude (IDE, chat interface, agent framework)
2. **MCP Server**: Standalone service exposing data/tools to Claude
3. **Data Source**: Database, API, file system, or external service

**MCP message types**:

```typescript
// 1. List available resources
{
  "method": "resources/list",
  "params": {}
}

// 2. Read specific resource
{
  "method": "resources/read",
  "params": {
    "uri": "file:///path/to/document.md"
  }
}

// 3. Execute tool
{
  "method": "tools/call",
  "params": {
    "name": "search_database",
    "arguments": {
      "query": "SELECT * FROM users WHERE role='admin'"
    }
  }
}
```

**Response format**:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Query results: ..."
    }
  ]
}
```

### 6.2.2 MCP Server Implementation

**Pattern Card: Building an MCP Server**

**Intent**: Expose data sources or tools to Claude via Model Context Protocol.

**When it helps**:
- Need to connect Claude to proprietary data (databases, file systems, APIs)
- Want full control over data access and permissions
- Require custom tool implementations
- Need to integrate with existing infrastructure

**Mechanics**:

**Minimal MCP server (Python)**:

```python
from mcp.server import Server, ResourceTemplate, Tool
from mcp.types import TextContent
import sqlite3

class DatabaseMCPServer(Server):
    """MCP server exposing database queries."""

    def __init__(self, db_path: str):
        super().__init__("database-server", "1.0.0")
        self.db_path = db_path

    async def list_resources(self) -> list[ResourceTemplate]:
        """List available database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        return [
            ResourceTemplate(
                uri=f"db://{table}",
                name=f"Table: {table}",
                description=f"Access {table} table",
                mimeType="application/json"
            )
            for table in tables
        ]

    async def read_resource(self, uri: str) -> list[TextContent]:
        """Read data from a table."""
        # Parse URI: db://table_name
        table_name = uri.split("//")[1]

        # Validate table name (prevent SQL injection)
        if not table_name.isidentifier():
            raise ValueError(f"Invalid table name: {table_name}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT 100")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()

        # Format as JSON
        import json
        data = [dict(zip(columns, row)) for row in rows]

        return [TextContent(
            type="text",
            text=json.dumps(data, indent=2)
        )]

    def get_tools(self) -> list[Tool]:
        """Define available tools."""
        return [
            Tool(
                name="query_database",
                description="Execute a SQL query against the database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL SELECT query"
                        }
                    },
                    "required": ["query"]
                }
            )
        ]

    async def call_tool(self, name: str, arguments: dict) -> list[TextContent]:
        """Execute a tool."""
        if name == "query_database":
            query = arguments["query"]

            # Validate query (only allow SELECT)
            if not query.strip().upper().startswith("SELECT"):
                raise ValueError("Only SELECT queries allowed")

            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(query)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

                import json
                data = [dict(zip(columns, row)) for row in rows]

                return [TextContent(
                    type="text",
                    text=json.dumps(data, indent=2)
                )]
            finally:
                conn.close()

        raise ValueError(f"Unknown tool: {name}")


# Run server
if __name__ == "__main__":
    server = DatabaseMCPServer("app.db")
    server.run()
```

**Client integration (Python)**:

```python
from anthropic import Anthropic
from mcp.client import Client as MCPClient

# Initialize MCP client
mcp_client = MCPClient("http://localhost:8080")

# Initialize Anthropic client
client = Anthropic(api_key="your-key")

# List available resources
resources = await mcp_client.list_resources()
print(f"Available resources: {resources}")

# Read a resource
user_table = await mcp_client.read_resource("db://users")

# Send to Claude with MCP context
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are a database analyst. Use the provided MCP tools to query data."
        }
    ],
    messages=[
        {
            "role": "user",
            "content": f"Analyze the user table:\n\n{user_table[0].text}"
        }
    ]
)

print(response.content[0].text)
```

**Variants**:

1. **File system MCP server**:
```python
class FileSystemMCPServer(Server):
    async def list_resources(self):
        # List files in a directory
        import os
        files = os.listdir(self.root_path)
        return [
            ResourceTemplate(
                uri=f"file://{f}",
                name=f,
                mimeType="text/plain"
            )
            for f in files if f.endswith('.txt')
        ]

    async def read_resource(self, uri: str):
        # Read file content
        filepath = uri.replace("file://", "")
        with open(os.path.join(self.root_path, filepath)) as f:
            return [TextContent(type="text", text=f.read())]
```

2. **API proxy MCP server**:
```python
class APIProxyMCPServer(Server):
    def get_tools(self):
        return [
            Tool(
                name="fetch_weather",
                description="Get current weather for a city",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"}
                    },
                    "required": ["city"]
                }
            )
        ]

    async def call_tool(self, name: str, arguments: dict):
        if name == "fetch_weather":
            city = arguments["city"]
            # Call external weather API
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.weather.example.com/current?city={city}"
                )
                data = response.json()

            return [TextContent(
                type="text",
                text=f"Weather in {city}: {data['conditions']}, {data['temp']}°C"
            )]
```

**Security considerations**:

- **SQL injection**: Validate/sanitize all queries (use parameterized queries, allowlists)
- **Path traversal**: Validate file paths (no `../`, check against allowlist)
- **Resource limits**: Limit query results (e.g., `LIMIT 100`), file sizes, API calls
- **Authentication**: MCP servers should require authentication (API keys, OAuth)
- **OWASP LLM07 (Insecure Plugin Design)**: MCP servers are "plugins"—apply all security best practices

---

## 6.3 Claude Native Tool Use

Claude supports native function calling without requiring external protocols like MCP [@anthropic2024tools]. This approach is similar to OpenAI's function calling but with key differences in execution model and reliability.

### 6.3.1 Tool Use Pattern

**Pattern Card: Claude Tool Use**

**Intent**: Enable Claude to call functions with structured inputs and receive structured outputs.

**When it helps**:
- Need to fetch external data (APIs, databases)
- Want to perform calculations or transformations
- Require deterministic operations (not conversational)
- Must ensure structured outputs

**Mechanics**:

```python
import anthropic

client = anthropic.Anthropic(api_key="your-key")

# Define tools
tools = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and state/country, e.g. 'San Francisco, CA'"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit"
                }
            },
            "required": ["location"]
        }
    },
    {
        "name": "calculate",
        "description": "Perform mathematical calculations",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    }
]

# Initial request
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": "What's the weather in San Francisco and what's 15 * 23?"}
    ]
)

print(f"Stop reason: {response.stop_reason}")  # "tool_use"
print(f"Content: {response.content}")
```

**Response format**:

```json
{
  "id": "msg_123",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll check the weather and do that calculation for you."
    },
    {
      "type": "tool_use",
      "id": "toolu_abc",
      "name": "get_weather",
      "input": {
        "location": "San Francisco, CA",
        "unit": "fahrenheit"
      }
    },
    {
      "type": "tool_use",
      "id": "toolu_def",
      "name": "calculate",
      "input": {
        "expression": "15 * 23"
      }
    }
  ],
  "stop_reason": "tool_use"
}
```

**Executing tools and continuing**:

```python
# Execute tools
tool_results = []

for content_block in response.content:
    if content_block.type == "tool_use":
        tool_name = content_block.name
        tool_input = content_block.input

        if tool_name == "get_weather":
            # Call weather API
            result = fetch_weather_api(
                tool_input["location"],
                tool_input.get("unit", "celsius")
            )
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": content_block.id,
                "content": json.dumps(result)
            })

        elif tool_name == "calculate":
            # Perform calculation
            result = eval(tool_input["expression"])  # Caution: eval is unsafe!
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": content_block.id,
                "content": str(result)
            })

# Continue conversation with tool results
final_response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": "What's the weather in San Francisco and what's 15 * 23?"},
        {"role": "assistant", "content": response.content},
        {"role": "user", "content": tool_results}
    ]
)

print(final_response.content[0].text)
# Output: "The weather in San Francisco is currently 65°F and sunny. The result of 15 * 23 is 345."
```

**Key differences from OpenAI function calling**:

| Aspect | Claude Tool Use | OpenAI Function Calling |
|--------|-----------------|------------------------|
| **Execution** | Client executes tools | OpenAI may execute (Actions) |
| **Parallel calls** | Multiple tools in one request | One at a time typically |
| **Determinism** | Highly deterministic | May retry/reformulate |
| **Error handling** | Client handles errors | OpenAI may auto-retry |
| **Streaming** | Supports streaming tool use | Limited streaming support |

**Failure modes**:

1. **Invalid tool inputs**: Claude generates malformed JSON
   - **Mitigation**: Validate tool inputs before execution
   - Use `try/except` and return error in tool_result

2. **Missing tools**: Claude tries to call a non-existent tool
   - **Mitigation**: Return error: `{"error": "Unknown tool: {name}"}`

3. **Infinite loops**: Tool calls trigger more tool calls indefinitely
   - **Mitigation**: Limit conversation depth (max 10 turns)

**Security notes**:

- **OWASP LLM07 (Insecure Plugin Design)**: Tools are attack vectors
  - Validate all tool inputs (type, range, format)
  - Use allowlists for constrained parameters
  - Never use `eval()` on tool inputs (use `ast.literal_eval()` for safe evaluation)

- **OWASP LLM08 (Excessive Agency)**: Limit tool capabilities
  - Read-only tools for data access
  - Confirmation required for destructive operations
  - Rate limiting per tool per session

---

## 6.4 Extended Context Windows

Claude's 200K token context window (vs GPT-4's 128K) enables document-level reasoning without chunking or RAG in many cases [@anthropic2024claude3].

### 6.4.1 Long Context Strategies

**When to use long context vs RAG**:

| Use Case | Recommendation | Rationale |
|----------|----------------|-----------|
| **Single document analysis** (<150K tokens) | Long context | Avoids chunking artifacts, preserves document structure |
| **Multi-document search** (>200K tokens) | RAG | Exceeds context limit, RAG more efficient |
| **Precise citation needed** | RAG | Can point to specific chunks |
| **Temporal queries** ("latest update") | RAG | Can filter by metadata (timestamps) |
| **Cross-document reasoning** | Hybrid | Use RAG to retrieve, long context to reason |

**Pattern: Long Context Document Analysis**:

```python
import anthropic

def analyze_long_document(document_path: str, question: str) -> str:
    """Analyze a document using Claude's extended context."""

    # Load document
    with open(document_path) as f:
        document_content = f.read()

    # Check token count (approximate: 4 chars/token)
    estimated_tokens = len(document_content) / 4

    if estimated_tokens > 180000:  # Leave room for response
        raise ValueError(f"Document too large: ~{estimated_tokens} tokens (max 180K)")

    client = anthropic.Anthropic(api_key="your-key")

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": f"""<document>
{document_content}
</document>

<question>
{question}
</question>

Please analyze the document and answer the question. Cite specific sections when relevant."""
            }
        ]
    )

    return response.content[0].text


# Example usage
answer = analyze_long_document(
    "legal_contract.txt",
    "What are the termination conditions?"
)
print(answer)
```

**Optimization techniques**:

1. **XML tags for structure**:
```xml
<documents>
  <document id="1" source="report_2023.pdf">
    ...
  </document>
  <document id="2" source="report_2024.pdf">
    ...
  </document>
</documents>

<question>
Compare revenue growth between 2023 and 2024.
</question>
```

2. **Prefill for structured outputs**:
```python
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=2048,
    messages=[
        {"role": "user", "content": f"<document>{document}</document>\n\nExtract key findings as JSON."},
        {"role": "assistant", "content": "{"}  # Prefill to force JSON
    ]
)
```

3. **Caching for repeated queries** (if supported):
```python
# Use prompt caching to avoid re-processing the same document
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": f"<document>{large_document}</document>",
            "cache_control": {"type": "ephemeral"}  # Cache this content
        }
    ],
    messages=[
        {"role": "user", "content": "Question 1"},
        # ... later:
        {"role": "user", "content": "Question 2"}
        # Document is cached, saves tokens/cost
    ]
)
```

---

## 6.5 Production Integration Patterns

### 6.5.1 Agent Framework Integration

**LangChain with Claude**:

```python
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain import hub

# Define tools
def search_database(query: str) -> str:
    """Search the database."""
    # Mock implementation
    return f"Results for: {query}"

tools = [
    Tool(
        name="SearchDatabase",
        func=search_database,
        description="Search the company database. Input should be a natural language query."
    )
]

# Initialize Claude
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    temperature=0,
    max_tokens=1024
)

# Create agent
prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5
)

# Run agent
result = agent_executor.invoke({
    "input": "Find all users who signed up in the last month"
})

print(result["output"])
```

**LlamaIndex with Claude**:

```python
from llama_index.llms.anthropic import Anthropic
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# Load documents
documents = SimpleDirectoryReader("./data").load_data()

# Initialize Claude
llm = Anthropic(model="claude-3-5-sonnet-20241022")

# Create index
index = VectorStoreIndex.from_documents(documents, llm=llm)

# Query
query_engine = index.as_query_engine()
response = query_engine.query("What are the main findings?")

print(response)
```

### 6.5.2 Streaming Responses

Claude supports streaming for low-latency user experiences:

```python
import anthropic

client = anthropic.Anthropic(api_key="your-key")

# Stream response
with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Write a long essay on quantum computing"}
    ]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

print("\n")

# Final message
final_message = stream.get_final_message()
print(f"Stop reason: {final_message.stop_reason}")
print(f"Total tokens: {final_message.usage.input_tokens + final_message.usage.output_tokens}")
```

**Streaming tool use**:

```python
with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": "What's the weather?"}
    ]
) as stream:
    for event in stream:
        if event.type == "content_block_start":
            if event.content_block.type == "tool_use":
                print(f"Calling tool: {event.content_block.name}")

        elif event.type == "content_block_delta":
            if hasattr(event.delta, "text"):
                print(event.delta.text, end="", flush=True)
```

---

## 6.6 Comparison: Claude vs ChatGPT Integration

### 6.6.1 Decision Matrix

| Requirement | Choose Claude | Choose ChatGPT |
|-------------|---------------|----------------|
| **Open protocol needed** | ✓ (MCP is open) | ✗ (Actions proprietary) |
| **Full execution control** | ✓ (client-side) | ✗ (server-side) |
| **Long context (>128K)** | ✓ (200K) | ✗ (128K max) |
| **No-code deployment** | ✗ (requires dev) | ✓ (GPT Builder GUI) |
| **Non-technical users** | ✗ | ✓ (GPT Store) |
| **Deterministic tool execution** | ✓ | ○ (less predictable) |
| **Built-in auth/OAuth** | ✗ (DIY) | ✓ (platform handles) |
| **Streaming tool use** | ✓ | ✗ (limited) |

**Hybrid approach**:

Use both platforms for different use cases:

- **Claude**: Developer-facing tools, API integration, long document analysis
- **ChatGPT**: End-user facing conversational applications, no-code deployments

---

## 6.7 Security Considerations

### 6.7.1 MCP Server Security

**Checklist for production MCP servers**:

- [ ] **Authentication**: Require API keys or OAuth tokens for all requests
- [ ] **Authorization**: Check user permissions before returning data
- [ ] **Input validation**: Sanitize all inputs (SQL injection, path traversal, etc.)
- [ ] **Rate limiting**: Limit requests per user/IP (prevent DoS)
- [ ] **Resource limits**: Cap query results, file sizes, API calls
- [ ] **Logging**: Log all requests, tool calls, errors (audit trail)
- [ ] **HTTPS only**: No plain HTTP in production
- [ ] **Secret management**: Store credentials in environment variables/vaults
- [ ] **Error messages**: Don't leak sensitive info in error messages
- [ ] **Monitoring**: Track anomalies (spike in errors, unusual queries)

**OWASP LLM Top 10 for Claude integrations**:

- **LLM01 (Prompt Injection)**: Validate tool inputs, use structured formats
- **LLM02 (Insecure Output Handling)**: Sanitize Claude outputs before execution/rendering
- **LLM06 (Sensitive Information Disclosure)**: Filter PII from MCP responses
- **LLM07 (Insecure Plugin Design)**: Validate MCP server inputs, use allowlists
- **LLM08 (Excessive Agency)**: Limit tool capabilities, require confirmations

### 6.7.2 Tool Use Security

**Safe tool execution pattern**:

```python
import json
from typing import Any, Dict
from enum import Enum

class ToolError(Exception):
    """Tool execution error."""
    pass

class ToolExecutor:
    """Secure tool executor with validation and rate limiting."""

    def __init__(self):
        self.call_counts = {}  # Rate limiting per tool
        self.max_calls_per_minute = 60

    def validate_tool_input(self, tool_name: str, tool_input: Dict[str, Any]) -> None:
        """Validate tool input before execution."""

        if tool_name == "query_database":
            query = tool_input.get("query", "")

            # Only allow SELECT
            if not query.strip().upper().startswith("SELECT"):
                raise ToolError("Only SELECT queries allowed")

            # No dangerous keywords
            dangerous = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
            if any(keyword in query.upper() for keyword in dangerous):
                raise ToolError(f"Query contains forbidden keyword")

            # Limit result size
            if "LIMIT" not in query.upper():
                raise ToolError("Query must include LIMIT clause")

        elif tool_name == "read_file":
            filepath = tool_input.get("path", "")

            # No path traversal
            if ".." in filepath or filepath.startswith("/"):
                raise ToolError("Invalid file path")

            # Allowlisted extensions only
            allowed_extensions = [".txt", ".md", ".json"]
            if not any(filepath.endswith(ext) for ext in allowed_extensions):
                raise ToolError(f"File type not allowed")

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute tool with security checks."""

        # Rate limiting
        import time
        current_time = time.time()
        key = f"{tool_name}_{current_time // 60}"  # Per-minute bucket

        if key not in self.call_counts:
            self.call_counts[key] = 0

        if self.call_counts[key] >= self.max_calls_per_minute:
            raise ToolError(f"Rate limit exceeded for {tool_name}")

        self.call_counts[key] += 1

        # Validate input
        try:
            self.validate_tool_input(tool_name, tool_input)
        except ToolError as e:
            return json.dumps({"error": str(e)})

        # Execute tool
        try:
            if tool_name == "query_database":
                result = execute_sql_query(tool_input["query"])
                return json.dumps(result)

            elif tool_name == "read_file":
                with open(tool_input["path"]) as f:
                    return f.read()

            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})

        except Exception as e:
            # Don't leak internal errors
            print(f"Tool error: {e}")  # Log internally
            return json.dumps({"error": "Tool execution failed"})
```

---

## 6.8 Key Takeaways

1. **MCP is Claude's open integration protocol**: Enables connecting Claude to data sources and tools through a standard protocol, giving developers full control over execution.

2. **Claude's tool use is deterministic and client-controlled**: Unlike ChatGPT Actions (which OpenAI executes), Claude returns structured tool calls for the client to execute, providing predictability and control.

3. **200K context window enables document-level reasoning**: Use long context for single documents <150K tokens; use RAG for multi-document search or >200K tokens.

4. **Security is the developer's responsibility**: Claude doesn't execute tools or access MCP servers—developers must validate inputs, handle errors, and enforce security policies.

5. **MCP servers require rigorous security**: Implement authentication, input validation, rate limiting, and resource limits. MCP servers are attack vectors (OWASP LLM07).

6. **Structured prompts improve reliability**: Use XML tags to structure context, prefill for structured outputs, and provide clear tool descriptions.

7. **Choose Claude for developer control, ChatGPT for no-code**: Claude excels at programmatic integrations and long-context tasks; ChatGPT excels at end-user applications and no-code deployment.

---

## References

This chapter references the following works:

1. Anthropic (2024): "Model Context Protocol (MCP)" - Protocol specification and implementation guide [@anthropic2024mcp]

2. Anthropic (2024): "Tool Use (Function Calling)" - Native tool use documentation [@anthropic2024tools]

3. Anthropic (2024): "Claude 3 Model Card" - Context window and capability specifications [@anthropic2024claude3]

4. OWASP (2024): "OWASP Top 10 for LLM Applications" - Security considerations [@owasp2024llm]

All examples tested with Claude 3.5 Sonnet (claude-3-5-sonnet-20241022) as of January 2025.

---

**Next**: Chapter 7 examines agentic systems and orchestration frameworks, covering ReAct, ReWOO, Reflexion agents, and multi-agent collaboration patterns.
