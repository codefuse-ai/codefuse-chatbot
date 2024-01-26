import json
import os
import re
import requests
from pydantic import BaseModel, Field
from typing import List

from .base_tool import BaseToolModel


class WorldTimeGetTimezoneByArea(BaseToolModel):
    """
    World Time API
    Tips:
        default control Required, e.g.  key1 is not Required/key2 is Required
    """

    name = "WorldTime.getTimezoneByArea"
    description = "a listing of all timezones available for that area."

    class ToolInputArgs(BaseModel):
        """Input for WorldTimeGetTimezoneByArea."""
        area: str = Field(..., description="area")

    class ToolOutputArgs(BaseModel):
        """Output for WorldTimeGetTimezoneByArea."""
        DateTimeJsonResponse: str = Field(..., description="a list of available timezones")

    @classmethod
    def run(area: str) -> ToolOutputArgs:
        """excute your tool!"""
        url = "http://worldtimeapi.org/api/timezone"
        try:
            res = requests.get(url, json={"area": area})
            return res.text
        except Exception as e:
            return e


def worldtime_run(area):
    url = "http://worldtimeapi.org/api/timezone"
    res = requests.get(url, json={"area": area})
    return res.text

# class WorldTime(BaseTool):
#     api_spec: str = '''
#   description: >-
#     A simple API to get the current time based on
#     a request with a timezone.

# servers:
#   - url: http://worldtimeapi.org/api/

# paths:
#   /timezone:
#     get:
#       description: a listing of all timezones.
#       operationId: getTimezone
#       responses:
#         default:
#           $ref: "#/components/responses/SuccessfulListJsonResponse"

#   /timezone/{area}:
#     get:
#       description: a listing of all timezones available for that area.
#       operationId: getTimezoneByArea
#       parameters:
#         - name: area
#           in: path
#           required: true
#           schema:
#             type: string
#       responses:
#         '200':
#           $ref: "#/components/responses/SuccessfulListJsonResponse"
#         default:
#           $ref: "#/components/responses/ErrorJsonResponse"

#   /timezone/{area}/{location}:
#     get:
#       description: request the current time for a timezone.
#       operationId: getTimeByTimezone
#       parameters:
#         - name: area
#           in: path
#           required: true
#           schema:
#             type: string
#         - name: location
#           in: path
#           required: true
#           schema:
#             type: string
#       responses:
#         '200':
#           $ref: "#/components/responses/SuccessfulDateTimeJsonResponse"
#         default:
#           $ref: "#/components/responses/ErrorJsonResponse"

#   /ip:
#     get:
#       description: >-
#         request the current time based on the ip of the request.
#         note: this is a "best guess" obtained from open-source data.
#       operationId: getTimeByIP
#       responses:
#         '200':
#           $ref: "#/components/responses/SuccessfulDateTimeJsonResponse"
#         default:
#           $ref: "#/components/responses/ErrorJsonResponse"

# components:
#   responses:
#     SuccessfulListJsonResponse:
#       description: >-
#         the list of available timezones in JSON format
#       content:
#         application/json:
#           schema:
#             $ref: "#/components/schemas/ListJsonResponse"

#     SuccessfulDateTimeJsonResponse:
#       description: >-
#         the current time for the timezone requested in JSON format
#       content:
#         application/json:
#           schema:
#             $ref: "#/components/schemas/DateTimeJsonResponse"

#     ErrorJsonResponse:
#       description: >-
#         an error response in JSON format
#       content:
#         application/json:
#           schema:
#             $ref: "#/components/schemas/ErrorJsonResponse"

#   schemas:
#     ListJsonResponse:
#       type: array
#       description: >-
#         a list of available timezones
#       items:
#         type: string

#     DateTimeJsonResponse:
#       required:
#         - abbreviation
#         - client_ip
#         - datetime
#         - day_of_week
#         - day_of_year
#         - dst
#         - dst_offset
#         - timezone
#         - unixtime
#         - utc_datetime
#         - utc_offset
#         - week_number
#       properties:
#         abbreviation:
#           type: string
#           description: >-
#             the abbreviated name of the timezone
#         client_ip:
#           type: string
#           description: >-
#             the IP of the client making the request
#         datetime:
#           type: string
#           description: >-
#             an ISO8601-valid string representing
#             the current, local date/time
#         day_of_week:
#           type: integer
#           description: >-
#             current day number of the week, where sunday is 0
#         day_of_year:
#           type: integer
#           description: >-
#             ordinal date of the current year
#         dst:
#           type: boolean
#           description: >-
#             flag indicating whether the local
#             time is in daylight savings
#         dst_from:
#           type: string
#           description: >-
#             an ISO8601-valid string representing
#             the datetime when daylight savings
#             started for this timezone
#         dst_offset:
#           type: integer
#           description: >-
#             the difference in seconds between the current local
#             time and daylight saving time for the location
#         dst_until:
#           type: string
#           description: >-
#             an ISO8601-valid string representing
#             the datetime when daylight savings
#             will end for this timezone
#         raw_offset:
#           type: integer
#           description: >-
#             the difference in seconds between the current local time
#             and the time in UTC, excluding any daylight saving difference
#             (see dst_offset)
#         timezone:
#           type: string
#           description: >-
#             timezone in `Area/Location` or
#             `Area/Location/Region` format
#         unixtime:
#           type: integer
#           description: >-
#             number of seconds since the Epoch
#         utc_datetime:
#           type: string
#           description: >-
#             an ISO8601-valid string representing
#             the current date/time in UTC
#         utc_offset:
#           type: string
#           description: >-
#             an ISO8601-valid string representing
#             the offset from UTC
#         week_number:
#           type: integer
#           description: >-
#             the current week number

#     ErrorJsonResponse:
#       required:
#         - error
#       properties:
#         error:
#           type: string
#           description: >-
#             details about the error encountered
# '''

#     def exec_tool(self, message: UserMessage) -> UserMessage:
#         match = re.search(r'{[\s\S]*}', message.content)
#         if match:
#             params = json.loads(match.group())
#             url = params["url"]
#             if "params" in params:
#                 url = url.format(**params["params"])
#             res = requests.get(url)
#             response_msg = UserMessage(content=f"API response: {res.text}")
#         else:
#             raise "ERROR"
#         return response_msg