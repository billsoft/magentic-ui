# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend/Python Development
- **Start application**: `magentic-ui --port 8081` or `python -m magentic_ui.backend.cli`
- **Start without Docker**: `magentic-ui --run-without-docker --port 8081`
- **CLI mode**: `magentic-cli --work-dir PATH_TO_STORE_LOGS`
- **Docker diagnostics**: `magentic-ui doctor` and `magentic-ui fix-docker`
- **Lint code**: `ruff check src`
- **Format code**: `ruff format src tests samples`
- **Type checking**: `pyright src` or `mypy src`
- **Run tests**: `pytest -m "not npx" tests --cov=src --cov-report=xml --cov-report=term-missing`
- **Run single test**: `pytest tests/test_specific_file.py::TestClass::test_method`
- **All checks**: `poethepoet check` (runs format, lint, pyright, test)
- **Prerequisites for tests**: `playwright install` (required before running browser tests)

### Frontend Development
- **Install dependencies**: `yarn install` (in `frontend/` directory)
- **Development server**: `npm run start` (serves at http://localhost:8000)
- **Clean development**: `gatsby clean && gatsby develop`
- **Build production**: `yarn build` (outputs to `src/magentic_ui/backend/web/ui/`)
- **Type checking**: `npm run typecheck`
- **Clean build cache**: `gatsby clean`
- **Environment setup**: Copy `.env.default` to `.env.development` for local development
- **Framework**: Gatsby with React, Tailwind CSS, Zustand for state management

### Docker Commands
- **Rebuild Docker images**: `magentic-ui --rebuild-docker --port 8081`
- **Build browser image**: `docker build -t magentic-ui-vnc-browser:latest ./src/magentic_ui/docker/magentic-ui-browser-docker`
- **Build Python env image**: `docker build -t magentic-ui-python-env:latest ./src/magentic_ui/docker/magentic-ui-python-env`

## Project Architecture

### High-Level Structure
Magentic-UI is a human-centered interface for web agents built on AutoGen's multi-agent framework. It provides both a web UI and CLI for interacting with a team of specialized AI agents.

### Core Architecture Components

**Multi-Agent System:**
- **Orchestrator** (`src/magentic_ui/teams/orchestrator/`): Central coordinator that manages planning, execution, and agent delegation
- **WebSurfer** (`src/magentic_ui/agents/web_surfer/`): Browser automation agent using Playwright for web navigation
- **Coder** (`src/magentic_ui/agents/_coder.py`): Code execution agent with Docker sandbox
- **FileSurfer** (`src/magentic_ui/agents/file_surfer/`): File management and conversion agent
- **ImageGenerator** (`src/magentic_ui/agents/_image_generator.py`): Image generation capabilities
- **UserProxy** (`src/magentic_ui/agents/_user_proxy.py`): Human interaction interface

**Backend Framework:**
- **FastAPI web server** (`src/magentic_ui/backend/web/`): RESTful API and WebSocket endpoints
- **Database layer** (`src/magentic_ui/backend/database/`): SQLModel with PostgreSQL support
- **Team management** (`src/magentic_ui/backend/teammanager/`): Orchestrates agent teams and manages execution
- **CLI interface** (`src/magentic_ui/backend/cli.py`): Command-line entry points and Docker management

**Frontend (Gatsby/React):**
- **Session management** (`frontend/src/components/views/manager.tsx`): Multi-session handling with WebSocket connections
- **Chat interface** (`frontend/src/components/views/chat/`): Real-time conversation UI with plan editing
- **Settings system** (`frontend/src/components/settings/`): Model configuration and agent settings
- **State management** (Zustand): Centralized configuration and session state with localStorage persistence
- **Component architecture**: Compound components, context providers, and API service layers
- **Styling**: Tailwind CSS with custom design system and dark/light mode support

### Key Integration Points

**Agent Communication:**
- Agents communicate through AutoGen's event-driven messaging system
- The Orchestrator delegates tasks based on step requirements and agent capabilities
- WebSocket connections provide real-time updates to the frontend

**Docker Integration:**
- Browser automation runs in isolated VNC containers (`src/magentic_ui/docker/magentic-ui-browser-docker/`)
- Code execution happens in sandboxed Python environments (`src/magentic_ui/docker/magentic-ui-python-env/`)
- Docker health checks and automatic image rebuilding ensure system reliability

**Configuration System:**
- Model clients support OpenAI, Azure OpenAI, and Ollama (`src/magentic_ui/magentic_ui_config.py`)
- Agent behaviors are configurable through YAML/JSON files
- UI settings are persisted and synchronized with backend configuration

### Development Patterns

**Adding New Agents:**
1. Create agent class extending AutoGen base classes in `src/magentic_ui/agents/`
2. Register in team configuration (`src/magentic_ui/task_team.py`)
3. Add UI controls in frontend settings if needed
4. Update type definitions in `frontend/src/components/types/datamodel.ts`

**WebSocket Message Flow:**
1. Frontend sends messages through WebSocket to `/api/ws/runs/{run_id}`
2. Backend processes through `TeamManager.run_stream()`
3. Orchestrator coordinates agent responses
4. Real-time updates stream back to frontend

**Model Integration:**
- Model clients are configured in `src/magentic_ui/magentic_ui_config.py`
- Frontend model forms are in `frontend/src/components/settings/tabs/agentSettings/modelSelector/`
- Each agent can use different models through the configuration system

**State Management (Frontend):**
- Use Zustand stores for complex state (`frontend/src/components/store.tsx`)
- Persist critical state with localStorage via `persist` middleware
- API service classes handle communication (`frontend/src/components/views/api.ts`)

**Testing Patterns:**
- Backend: Use `@pytest.mark.asyncio` for async tests, create fixtures for browser/temp directories
- Frontend: Currently relies on TypeScript strict mode and manual testing
- Integration: Background task tests in root directory for WebSocket communication

## Important Implementation Notes

- **Docker is required** for full functionality (web browsing, code execution, file operations)
- **WebSocket connections** handle real-time communication between frontend and backend
- **Plan editing** allows users to modify AI-generated plans before execution
- **Background task management** supports multiple concurrent sessions
- **Memory and learning** features can store and retrieve successful plans
- **Security controls** include action guards and approval policies for sensitive operations

## Testing and Quality

### Backend Testing
- **Framework**: pytest with async support (`pytest-asyncio`)
- **Test markers**: `@pytest.mark.npx` for tests requiring NPX, `@pytest.mark.asyncio` for async tests
- **Coverage**: `--cov=src --cov-report=xml --cov-report=term-missing`
- **Browser testing**: Playwright integration with headless Chrome
- **Fixture patterns**: Async fixtures for browser setup, temporary directories for file operations
- **Integration tests**: WebSocket communication, Docker container health checks
- **Configuration**: `pytest.ini` sets async loop scope and defines NPX marker
- **Test environment**: `PYTHONPATH=src` required, excludes NPX-dependent tests by default
- **Custom test runner**: `python run_all_tests.py` for comprehensive testing with timeout management

### Frontend Testing
- **Current status**: No formal testing framework configured
- **Type safety**: TypeScript with strict mode provides compile-time validation
- **Manual testing**: Hot reload development server at http://localhost:8000
- **Build validation**: Production build process serves as integration test

### Quality Tools
- **Linting**: Ruff for Python code formatting and linting
- **Type checking**: Pyright (primary) and MyPy (alternative) for Python
- **Frontend types**: TypeScript with strict mode
- **Pre-commit workflow**: `poethepoet check` runs all quality checks

## Critical Multi-Step Execution System

### Orchestrator State Management
The Orchestrator (`src/magentic_ui/teams/orchestrator/_orchestrator.py`) uses a sophisticated state management system:
- **current_step_idx**: Tracks execution progress through plan steps
- **step_execution_status**: Maps step indices to execution states ("not_started", "in_progress", "completed", "failed", "skipped")
- **Race condition prevention**: Step index is only incremented in one location to prevent duplicate progression

### Agent Completion Signals
**Critical**: Agents must use step-specific completion signals to prevent premature task termination:
- **WebSurfer**: Use "✅ 当前步骤已完成" instead of "✅ 任务已完成"
- **ImageGenerator**: Use "图像生成任务已完成" or "图像已成功生成"
- **CoderAgent**: Use format-specific signals like "文档创建任务已完成", "HTML转换完成", "PDF生成完成"

### Error Recovery Patterns
- **Validation errors**: WebSurfer includes recovery mechanisms for validation errors in `_web_surfer.py`
- **Timeout handling**: Agents should provide meaningful fallback responses when operations timeout
- **Context preservation**: Failed steps should preserve context for subsequent steps

### Signal Recognition Rules
The Orchestrator distinguishes between:
- **Step completion signals**: Indicate single step completion - continue to next step
- **Task completion signals**: Indicate entire task completion - should trigger plan termination
- **Global signals**: Avoided to prevent confusion between step and task completion

## Multi-Agent Workflow Debugging

### Common Issues
1. **Premature termination**: Usually caused by agents sending global completion signals instead of step-specific ones
2. **Step index race conditions**: Multiple code paths incrementing current_step_idx simultaneously
3. **Context loss**: Information not properly passed between agents in multi-step workflows

### Debugging Commands
- **Test multi-step execution**: `python run_all_tests.py` (runs comprehensive test suite)
- **Test specific components**: `pytest test_orchestrator_signal_recognition.py -v`
- **Test agent collaboration**: `pytest test_agent_collaboration.py -v`

## MCP (Model Context Protocol) Integration

### Adding MCP Agents
Configure MCP agents in `config.yaml` under `mcp_agent_configs`:
- Each MCP agent can access multiple MCP servers via `mcp_servers` configuration
- Supported server types: `StdioServerParams` and `SseServerParams`
- MCP agents are `AssistantAgent` instances with `AggregateMcpWorkbench` tool access

### MCP Server Management
- MCP servers are exposed through `autogen_ext.tools.mcp.McpWorkbench` objects
- Server configuration includes command, args, and connection parameters
- Each agent can have different MCP server access based on role requirements

## Development Environment

### Environment Variables
- **Required**: `OPENAI_API_KEY` for OpenAI models, `OPENROUTER_API_KEY` for OpenRouter
- **Config resolution**: Environment variables in `config.yaml` use `$VARIABLE_NAME` syntax
- **Frontend**: API URL configured via `GATSBY_API_URL` in `.env.development`

### Configuration Management
- **Primary config**: `config.yaml` in root directory with YAML anchor support
- **Client resolution**: Supports environment variable substitution automatically
- **Model switching**: Each agent can use different model clients through configuration
- **Network stability**: Enhanced HTTP client config with retry mechanisms