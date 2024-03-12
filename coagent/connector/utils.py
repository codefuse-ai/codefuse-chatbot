import re, copy, json
from loguru import logger


def extract_section(text, section_name):
    # Define a pattern to extract the named section along with its content
    section_pattern = rf'#### {section_name}\n(.*?)(?=####|$)'
    
    # Find the specific section content
    section_content = re.search(section_pattern, text, re.DOTALL)
    
    if section_content:
        # If the section is found, extract the content and strip the leading/trailing whitespace
        # This will also remove leading/trailing newlines
        content = section_content.group(1).strip()
        
        # Return the cleaned content
        return content
    else:
        # If the section is not found, return an empty string
        return ""


def parse_section(text, section_name):
    # Define a pattern to extract the named section along with its content
    section_pattern = rf'#### {section_name}\n(.*?)(?=####|$)'
    
    # Find the specific section content
    section_content = re.search(section_pattern, text, re.DOTALL)
    
    if section_content:
        # If the section is found, extract the content
        content = section_content.group(1)
        
        # Define a pattern to find segments that follow the format **xx:**
        segments_pattern = r'\*\*([^*]+):\*\*'
        
        # Use findall method to extract all matches in the section content
        segments = re.findall(segments_pattern, content)
        
        return segments
    else:
        # If the section is not found, return an empty list
        return []
    

def parse_text_to_dict(text):
    # Define a regular expression pattern to capture the key and value
    main_pattern = r"\*\*(.+?):\*\*\s*(.*?)\s*(?=\*\*|$)"
    list_pattern = r'```python\n(.*?)```'
    plan_pattern = r'\[\s*.*?\s*\]'

    # Use re.findall to find all main matches in the text
    main_matches = re.findall(main_pattern, text, re.DOTALL)

    # Convert main matches to a dictionary
    parsed_dict = {key.strip(): value.strip() for key, value in main_matches}

    for k, v in parsed_dict.items():
        for pattern in [list_pattern, plan_pattern]:
            if "PLAN" != k: continue
            v = v.replace("```list", "```python")
            match_value = re.search(pattern, v, re.DOTALL)
            if match_value:
                # Add the code block to the dictionary
                parsed_dict[k] = eval(match_value.group(1).strip())
                break

    return parsed_dict


def parse_dict_to_dict(parsed_dict) -> dict:
    code_pattern = r'```python\n(.*?)```'
    tool_pattern = r'```json\n(.*?)```'
    java_pattern = r'```java\n(.*?)```'
    
    pattern_dict = {"code": code_pattern, "json": tool_pattern, "java": java_pattern}
    spec_parsed_dict = copy.deepcopy(parsed_dict)
    for key, pattern in pattern_dict.items():
        for k, text in parsed_dict.items():
            # Search for the code block
            if not isinstance(text, str): 
                spec_parsed_dict[k] = text
                continue
            _match = re.search(pattern, text, re.DOTALL)
            if _match:
                # Add the code block to the dictionary
                try:
                    spec_parsed_dict[key] = json.loads(_match.group(1).strip())
                    spec_parsed_dict[k] = json.loads(_match.group(1).strip())
                except:
                    spec_parsed_dict[key] = _match.group(1).strip()
                    spec_parsed_dict[k] = _match.group(1).strip()
                break
    return spec_parsed_dict


def prompt_cost(model_type: str, num_prompt_tokens: float, num_completion_tokens: float):
    input_cost_map = {
        "gpt-3.5-turbo": 0.0015,
        "gpt-3.5-turbo-16k": 0.003,
        "gpt-3.5-turbo-0613": 0.0015,
        "gpt-3.5-turbo-16k-0613": 0.003,
        "gpt-4": 0.03,
        "gpt-4-0613": 0.03,
        "gpt-4-32k": 0.06,
    }

    output_cost_map = {
        "gpt-3.5-turbo": 0.002,
        "gpt-3.5-turbo-16k": 0.004,
        "gpt-3.5-turbo-0613": 0.002,
        "gpt-3.5-turbo-16k-0613": 0.004,
        "gpt-4": 0.06,
        "gpt-4-0613": 0.06,
        "gpt-4-32k": 0.12,
    }

    if model_type not in input_cost_map or model_type not in output_cost_map:
        return -1

    return num_prompt_tokens * input_cost_map[model_type] / 1000.0 + num_completion_tokens * output_cost_map[model_type] / 1000.0
