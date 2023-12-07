import re



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
