import re
from urllib.parse import urlparse, parse_qsl, urlencode
from flask import request
from werkzeug.datastructures import ImmutableMultiDict
from pweb_form_rest.data.pweb_request_info import PWebRequestInfo


class RequestData:

    def _parse_value(self, value):
        if value == "null" or value == "None":
            return None
        return value

    def _form_data_dict_to_dict(self, _input: ImmutableMultiDict, default=None):
        if not _input:
            return default
        requested_data = _input.to_dict(flat=False)
        response = {}
        for data in requested_data:
            if len(requested_data[data]) == 1:
                response[data] = self._parse_value(requested_data[data][0])
            else:
                response[data] = self._parse_value(requested_data[data])
        return response

    def json_data(self, default=None):
        json = request.get_json()
        if json:
            return json
        return default

    def form_data(self, default=None):
        data = request.form
        if data:
            return self._form_data_dict_to_dict(data, default)
        return default

    def file_data(self, default=None):
        files = request.files
        if files:
            return self._form_data_dict_to_dict(files, default)
        return default

    def form_and_file_data(self, default=None):
        form_data = self.form_data(default={})
        file_data = self.file_data(default={})
        form_data.update(file_data)
        if form_data:
            return form_data
        return default

    def query_args(self, default=None):
        data = request.args
        if data:
            return data
        return default

    def get_query_args_value(self, key: str, default=None, type=None):
        data = self.query_args(default=None)
        if not data:
            return default
        if key in data:
            value = data.getlist(key, type)
            if len(value) == 1:
                return value[0]
            return value
        return default

    def request_method(self):
        return request.method

    def is_post(self):
        return 'POST' == self.request_method()

    def is_get(self):
        return 'GET' == self.request_method()

    def current_url(self):
        return request.referrer

    def get_header(self, name: str, default=None):
        return request.headers.get(name, default)

    def get_auth_header(self):
        header = self.get_header("Authorization")
        if not header:
            header = self.get_header("authorization")
        return header

    def get_bearer_token(self):
        authorization_header = self.get_auth_header()
        if not authorization_header:
            return None
        group = re.match("^Bearer\\s+(.*)", authorization_header)
        if group:
            return group.group(1)
        return None

    def get_url_info(self) -> PWebRequestInfo:
        url_dictionary = PWebRequestInfo()
        if request and request.url:
            if request.path:
                url_dictionary.relativeURL = str(request.path)
            url_dictionary.relativeURLWithParam = str(request.full_path)
            url_dictionary.hostWithPort = str(request.host)
            url_dictionary.method = str(request.method)
            url_dictionary.urlRule = str(request.url_rule)
            url_dictionary.baseURL = str(request.host_url).strip("/")
        return url_dictionary

    def get_host_name(self):
        url_details = urlparse(request.host_url)
        if url_details and url_details.hostname:
            return url_details.hostname
        return None

    def parse_query_params(self, url):
        parsed = urlparse(url)
        params = dict(parse_qsl(parsed.query))
        return params

    def add_to_query_params(self, url, params: dict):
        if not params:
            return url
        current_params = self.parse_query_params(url)
        merged_params = urlencode({**current_params, **params})
        parsed = urlparse(url)
        parsed = parsed._replace(query=merged_params)
        return parsed.geturl()
