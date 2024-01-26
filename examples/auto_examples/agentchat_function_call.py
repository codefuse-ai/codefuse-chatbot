import os, sys, requests

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(src_dir)

# from configs.model_config import *
from coagent.connector.phase import BasePhase
from coagent.connector.agents import BaseAgent
from coagent.connector.chains import BaseChain
from coagent.connector.schema import (
    Message, Memory, load_role_configs, load_phase_configs, load_chain_configs
    )
from coagent.connector.configs import AGETN_CONFIGS, CHAIN_CONFIGS, PHASE_CONFIGS
from coagent.connector.utils import parse_section
import importlib


# update new agent configs
# tool learning 实现参考 ~/examples/agent_examples/toolReactPhase_example.py