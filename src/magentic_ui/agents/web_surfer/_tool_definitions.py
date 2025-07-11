from autogen_core.tools import ToolSchema

from ...tools.tool_metadata import load_tool, make_approval_prompt

EXPLANATION_TOOL_PROMPT = "Explain to the user the action to be performed and reason for doing so. Phrase as if you are directly talking to the user."

REFINED_GOAL_PROMPT = "1) Summarize all the information observed and actions performed so far and 2) refine the request to be completed"

IRREVERSIBLE_ACTION_PROMPT = make_approval_prompt(
    guarded_examples=["buying a product", "submitting a form"],
    unguarded_examples=["navigating a website", "things that can be undone"],
    category="irreversible actions",
)

# "Is this action something that would require human approval before being done as it is irreversible? Example: buying a product, submitting a form are irreversible actions. But navigating a website and things that can be undone are not irreversible actions."

TOOL_VISIT_URL: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "visit_url",
            "description": "🔧 AUTONOMOUS NAVIGATION: Navigate directly to a provided URL. This is autonomous for research and information gathering. Only require approval for sensitive or commercial domains.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "url": {
                        "type": "string",
                        "description": "The URL to visit in the browser.",
                    },
                    "require_approval": {
                        "type": "boolean",
                        "description": "Set to false for research/information gathering. Only true for sensitive operations.",
                        "default": False,
                    },
                },
                "required": ["explanation", "url"],
            },
        },
        "metadata": {
            "requires_approval": "never",
        },
    }
)

TOOL_WEB_SEARCH: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "🔧 AUTONOMOUS SEARCH: Performs a web search on Bing.com with the given query. Autonomous for research purposes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "query": {
                        "type": "string",
                        "description": "The web search query to use.",
                    },
                    "require_approval": {
                        "type": "boolean",
                        "description": "Set to false for research/information gathering.",
                        "default": False,
                    },
                },
                "required": ["explanation", "query"],
            },
        },
        "metadata": {
            "requires_approval": "never",
        },
    }
)

TOOL_HISTORY_BACK: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "history_back",
            "description": "🔧 AUTONOMOUS NAVIGATION: Navigates back one page in the browser's history for autonomous navigation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "require_approval": {
                        "type": "boolean",
                        "description": "Set to false for autonomous navigation.",
                        "default": False,
                    },
                },
                "required": ["explanation"],
            },
        },
        "metadata": {
            "requires_approval": "never",
        },
    }
)

TOOL_REFRESH_PAGE: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "refresh_page",
            "description": "🔧 AUTONOMOUS REFRESH: Refreshes the current page autonomously for content updates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "require_approval": {
                        "type": "boolean",
                        "description": "Set to false for autonomous page refresh.",
                        "default": False,
                    },
                },
                "required": ["explanation"],
            },
        },
        "metadata": {
            "requires_approval": "never",
        },
    }
)

TOOL_PAGE_UP: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "page_up",
            "description": "Scrolls the entire browser viewport one page UP towards the beginning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                },
                "required": ["explanation"],
            },
        },
        "metadata": {"requires_approval": "never"},
    }
)

TOOL_PAGE_DOWN: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "page_down",
            "description": "Scrolls the entire browser viewport one page DOWN towards the end.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                },
                "required": ["explanation"],
            },
        },
        "metadata": {"requires_approval": "never"},
    }
)

TOOL_CLICK: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "🔧 AUTONOMOUS CLICKING: Click on page elements for navigation and information gathering. Autonomous for research tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "target_id": {
                        "type": "integer",
                        "description": "The numeric id of the target to click.",
                    },
                    "require_approval": {
                        "type": "boolean",
                        "description": "Set to false for navigation/research. Only true for forms/purchases.",
                        "default": False,
                    },
                },
                "required": ["explanation", "target_id"],
            },
        },
        "metadata": {
            "requires_approval": "never",
        },
    }
)

TOOL_CLICK_FULL: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "click_full",
            "description": "Clicks the mouse on the target with the given id, with optional hold duration and button type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "target_id": {
                        "type": "integer",
                        "description": "The numeric id of the target to click.",
                    },
                    "hold": {
                        "type": "number",
                        "description": "Seconds to hold the mouse button down before releasing. Default: 0.0.",
                        "default": 0.0,
                    },
                    "button": {
                        "type": "string",
                        "enum": ["left", "right"],
                        "description": "Mouse button to use. Default: 'left'.",
                        "default": "left",
                    },
                    "require_approval": {
                        "type": "boolean",
                        "description": IRREVERSIBLE_ACTION_PROMPT,
                    },
                },
                "required": ["explanation", "target_id", "hold", "button"],
            },
        },
        "metadata": {
            "requires_approval": "maybe",
        },
    }
)

TOOL_TYPE: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "input_text",
            "description": "🔧 AUTONOMOUS TYPING: Types text into input fields. Autonomous for search/research, requires approval for form submissions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "input_field_id": {
                        "type": "integer",
                        "description": "The numeric id of the input field to receive the text.",
                    },
                    "text_value": {
                        "type": "string",
                        "description": "The text to type into the input field.",
                    },
                    "press_enter": {
                        "type": "boolean",
                        "description": "Whether to press enter after typing into the field or not.",
                    },
                    "delete_existing_text": {
                        "type": "boolean",
                        "description": "Whether to delete existing text in the field before inputing the text value.",
                    },
                    "require_approval": {
                        "type": "boolean",
                        "description": "Set to false for search fields. Only true for form submissions.",
                        "default": False,
                    },
                },
                "required": [
                    "explanation",
                    "input_field_id",
                    "text_value",
                    "delete_existing_text",
                ],
            },
        },
        "metadata": {
            "requires_approval": "conditional",
        },
    }
)

TOOL_SCROLL_ELEMENT_DOWN: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "scroll_element_down",
            "description": "Scrolls a given html element (e.g., a div or a menu) DOWN.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "target_id": {
                        "type": "integer",
                        "description": "The numeric id of the target to scroll down.",
                    },
                },
                "required": ["explanation", "target_id"],
            },
        },
        "metadata": {
            "requires_approval": "never",
        },
    }
)

TOOL_SCROLL_ELEMENT_UP: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "scroll_element_up",
            "description": "Scrolls a given html element (e.g., a div or a menu) UP.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "target_id": {
                        "type": "integer",
                        "description": "The numeric id of the target to scroll UP.",
                    },
                },
                "required": ["explanation", "target_id"],
            },
        },
        "metadata": {
            "requires_approval": "never",
        },
    }
)

TOOL_HOVER: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "hover",
            "description": "Hovers the mouse over the target with the given id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "target_id": {
                        "type": "integer",
                        "description": "The numeric id of the target to hover over.",
                    },
                },
                "required": ["explanation", "target_id"],
            },
        },
        "metadata": {
            "requires_approval": "never",
        },
    }
)

TOOL_KEYPRESS: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "keypress",
            "description": "🔧 AUTONOMOUS KEYPRESS: Press keyboard keys autonomously for navigation and scrolling.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of keys to press in sequence. For special keys, use their full name (e.g. 'Enter', 'Tab', etc.).",
                    },
                    "require_approval": {
                        "type": "boolean",
                        "description": "Set to false for navigation keys. Only true for data entry.",
                        "default": False,
                    },
                },
                "required": ["explanation", "keys"],
            },
        },
        "metadata": {
            "requires_approval": "conditional",
        },
    }
)

TOOL_READ_PAGE_AND_ANSWER: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "answer_question",
            "description": "Used to answer questions about the current webpage's content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "question": {
                        "type": "string",
                        "description": "The question to answer. Do not ask any follow up questions or say that you can help with more things.",
                    },
                },
                "required": ["explanation", "question"],
            },
        },
        "metadata": {
            "requires_approval": "never",
        },
    }
)

TOOL_SUMMARIZE_PAGE: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "summarize_page",
            "description": "Uses AI to summarize the entire page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                },
                "required": ["explanation"],
            },
        },
        "metadata": {
            "requires_approval": "never",
        },
    }
)

TOOL_SLEEP: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "sleep",
            "description": "Wait a specified period of time in seconds (default 3 seconds). Call this function if the page has not yet fully loaded, or if it is determined that a small delay would increase the task's chances of success.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "duration": {
                        "type": "number",
                        "description": "The number of seconds to wait. Default is 3 seconds.",
                    },
                },
                "required": ["explanation"],
            },
        },
        "metadata": {
            "requires_approval": "never",
        },
    }
)


TOOL_STOP_ACTION: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "stop_action",
            "description": "🔧 Use this tool ONLY when your task is fully completed or when you cannot proceed further. Provide a comprehensive answer and clear completion status in your response.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "answer": {
                        "type": "string",
                        "description": "🔧 ENHANCED COMPLETION SIGNAL: Your answer must begin with a clear completion status indicator:\n- For SUCCESSFUL completion: Start with '✅ 当前步骤已完成' or '✅ STEP COMPLETED'\n- For ERROR completion: Start with '⚠️ 当前步骤因错误完成' or '⚠️ STEP COMPLETED WITH ERRORS'\n- For ALTERNATIVE completion: Start with '🔄 当前步骤通过替代方案完成' or '🔄 STEP COMPLETED VIA ALTERNATIVE'\n\nThen provide: 1) A complete summary of what was accomplished 2) Any information gathered 3) Any issues encountered and how they were resolved. Be specific and factual. Do not ask questions or offer additional help.",
                    },
                },
                "required": ["explanation", "answer"],
            },
        },
        "metadata": {
            "requires_approval": "never",
        },
    }
)

TOOL_SELECT_OPTION: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "select_option",
            "description": "🔧 AUTONOMOUS SELECTION: Selects options from dropdown menus autonomously for filtering and navigation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "target_id": {
                        "type": "integer",
                        "description": "The numeric id of the option to select.",
                    },
                    "require_approval": {
                        "type": "boolean",
                        "description": "Set to false for navigation/filtering. Only true for form submissions.",
                        "default": False,
                    },
                },
                "required": ["explanation", "target_id"],
            },
        },
        "metadata": {
            "requires_approval": "conditional",
        },
    }
)

TOOL_CREATE_TAB: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "create_tab",
            "description": "🔧 AUTONOMOUS TAB CREATION: Creates new browser tabs autonomously for research and comparison.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "url": {
                        "type": "string",
                        "description": "The URL to open in the new tab.",
                    },
                    "require_approval": {
                        "type": "boolean",
                        "description": "Set to false for research purposes.",
                        "default": False,
                    },
                },
                "required": ["explanation", "url"],
            },
        },
        "metadata": {
            "requires_approval": "never",
        },
    }
)

TOOL_SWITCH_TAB: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "switch_tab",
            "description": "🔧 AUTONOMOUS TAB SWITCHING: Switches between browser tabs autonomously for research workflow.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "tab_index": {
                        "type": "integer",
                        "description": "The index of the tab to switch to (0-based).",
                    },
                    "require_approval": {
                        "type": "boolean",
                        "description": "Set to false for autonomous tab management.",
                        "default": False,
                    },
                },
                "required": ["explanation", "tab_index"],
            },
        },
        "metadata": {
            "requires_approval": "never",
        },
    }
)

TOOL_CLOSE_TAB: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "close_tab",
            "description": "Closes the specified browser tab by its index and switches to an adjacent tab. Cannot close the last remaining tab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": EXPLANATION_TOOL_PROMPT,
                    },
                    "tab_index": {
                        "type": "integer",
                        "description": "The index of the tab to close (0-based).",
                    },
                },
                "required": ["explanation", "tab_index"],
            },
        },
        "metadata": {
            "requires_approval": "always",
        },
    }
)

TOOL_UPLOAD_FILE: ToolSchema = load_tool(
    {
        "type": "function",
        "function": {
            "name": "upload_file",
            "description": "Upload a file to a specified input element.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": "The explanation of the action to be performed.",
                    },
                    "target_id": {
                        "type": "string",
                        "description": "The ID of the target input element.",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to be uploaded.",
                    },
                },
                "required": ["explanation", "target_id", "file_path"],
            },
            "metadata": {
                "requires_approval": "always",
            },
        },
    }
)
