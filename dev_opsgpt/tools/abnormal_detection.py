
import json
import os
import re
from pydantic import BaseModel, Field
from typing import List, Dict
import requests
import numpy as np
from loguru import logger

from .base_tool import BaseToolModel



class KSigmaDetector(BaseToolModel):
    """
    Tips:
        default control Required, e.g.  key1 is not Required/key2 is Required
    """

    name: str = "KSigmaDetector"
    description: str = "Anomaly detection using K-Sigma method"

    class ToolInputArgs(BaseModel):
        """Input for KSigmaDetector."""

        data: List[float] = Field(..., description="List of data points")
        detect_window: int = Field(default=5, description="The size of the detect window for detecting anomalies")
        abnormal_window: int = Field(default=3, description="The threshold for the number of abnormal points required to classify the data as abnormal")
        k: float = Field(default=3.0, description="the coef of k-sigma")

    class ToolOutputArgs(BaseModel):
        """Output for KSigmaDetector."""

        is_abnormal: bool = Field(..., description="Indicates whether the input data is abnormal or not")

    @staticmethod
    def run(data, detect_window=5, abnormal_window=3, k=3.0):
        refer_data = np.array(data[-detect_window:])
        detect_data = np.array(data[:-detect_window])
        mean = np.mean(refer_data)
        std = np.std(refer_data)

        is_abnormal = np.sum(np.abs(detect_data - mean) > k * std) >= abnormal_window
        return {"is_abnormal": is_abnormal}