import requests, os, sys
# src_dir = os.path.join(
#     os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# )
# sys.path.append(src_dir)

# from dev_opsgpt.utils.common_utils import st_load_file
# from dev_opsgpt.sandbox.pycodebox import PyCodeBox
# from examples.file_fastapi import upload_file, download_file
# from pathlib import Path
# import httpx
# from loguru import logger
# from io import BytesIO


# def _parse_url(url: str, base_url: str) -> str:
#     if (not url.startswith("http")
#                 and base_url
#             ):
#         part1 = base_url.strip(" /")
#         part2 = url.strip(" /")
#         return f"{part1}/{part2}"
#     else:
#         return url

# base_url: str = "http://127.0.0.1:7861"
# timeout: float = 60.0,
# url = "/files/upload"
# url = _parse_url(url, base_url)
# logger.debug(url)
# kwargs = {}
# kwargs.setdefault("timeout", timeout)

# import asyncio
# file = "./torch_test.py"
# upload_filename = st_load_file(file, filename="torch_test.py")
# asyncio.run(upload_file(upload_filename))

import requests
url = "http://127.0.0.1:7862/sdfiles/download?filename=torch_test.py&save_filename=torch_test.py"
r = requests.get(url)
print(type(r.text))