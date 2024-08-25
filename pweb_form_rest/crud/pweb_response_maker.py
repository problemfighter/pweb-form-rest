import json
import typing as t
from flask import make_response, send_file
from pweb_form_rest.data.pweb_response_data import PWebMessageResponse, PWebDataResponse, PWebPagination, \
    PWebPaginateResponse
from pweb_form_rest.data.pweb_response_status import PWebResponseCode, PWebResponseStatus
from pweb_form_rest.schema.pweb_rest_schema import PWebDataDTO, APIPaginateResponse
from pweb_orm import PWebBaseModel


class PWebHTTPResponse:

    def response(self, response_data, code=200, headers: dict = None):
        response_obj = make_response(response_data, code)
        if headers:
            response_obj.headers.update(headers)
        return response_obj

    def json_string_response(self, json_string: str, code=200, headers: dict = None):
        _headers = {
            "Content-Type": "application/json; charset=utf-8",
        }
        if headers and isinstance(headers, dict):
            _headers.update(headers)
        return self.response(json_string, code=code, headers=_headers)

    def json_response(self, dictionary, code=200, headers: dict = None):
        json_object = {}
        if dictionary:
            json_object = dictionary
        response_string = "{}"
        try:
            response_string = json.dumps(json_object)
        except Exception as e:
            response_string = "{}"
        return self.json_string_response(response_string, code, headers)

    def file_response(self, file_path, download_name: t.Optional[str] = None):
        return send_file(file_path, download_name=download_name)

    def text_response(self, text: str, code=200, headers: dict = None):
        return self.response(text, code=code, headers=headers)


class ResponseMaker:
    headers: dict = None
    http_response: PWebHTTPResponse = PWebHTTPResponse()

    def add_header(self, key: str, value):
        if not self.headers:
            self.headers = {}
        self.headers[key] = value

    def message(self, message: str, status: str, code: str, http_code=200):
        message_response = PWebMessageResponse()
        message_response.message = message
        message_response.status = status
        message_response.code = code
        return self.http_response.json_string_response(message_response.to_dict(), http_code, self.headers)

    def success_message(self, message: str, code: str = PWebResponseCode.success, http_code=200):
        return self.message(message, PWebResponseStatus.success, code, http_code)

    def error_message(self, message: str, code: str = PWebResponseCode.error, http_code=200):
        return self.message(message, PWebResponseStatus.error, code, http_code)

    def data_type_response(self, model: PWebBaseModel, response_dto: PWebDataDTO, many=False, status: str = PWebResponseStatus.success, code: str = PWebResponseCode.success, message: str = None):
        data_response = PWebDataResponse()
        data_response.status = status
        data_response.code = code
        data_response.message = message
        data_response.add_data(model, response_dto, many)
        return data_response

    def data_response(self, model: PWebBaseModel, response_dto: PWebDataDTO, many=False, status: str = PWebResponseStatus.success, code: str = PWebResponseCode.success, http_code=200, message: str = None):
        data_response = self.data_type_response(model=model, response_dto=response_dto, many=many, status=status, code=code, message=message)
        return self.http_response.json_string_response(data_response.to_dict(), http_code, self.headers)

    def set_pagination_data(self, model: PWebBaseModel):
        pagination = PWebPagination()
        pagination.page = model.page
        pagination.totalPage = model.pages
        pagination.itemPerPage = model.per_page
        pagination.total = model.total
        return pagination

    def _get_paginate_response_object(self,  model: PWebBaseModel):
        pagination = self.set_pagination_data(model)
        response = PWebPaginateResponse()
        response.status = PWebResponseStatus.success
        response.code = PWebResponseCode.success
        response.pagination = pagination
        return response

    def get_paginate_dict(self, model: PWebBaseModel, data: list):
        pagination = self.set_pagination_data(model=model)
        response = APIPaginateResponse().dump({"pagination": pagination})
        response["data"] = data
        return response

    def paginate_type_response(self, model: PWebBaseModel, response_dto: PWebDataDTO):
        response = self._get_paginate_response_object(model=model)
        response.data = model.items
        response.add_only_data(model.items, response_dto, True)
        return response.to_dict()

    def paginate_response(self, model: PWebBaseModel, response_dto: PWebDataDTO):
        response_dict = self.paginate_type_response(model, response_dto)
        return self.http_response.json_string_response(response_dict, headers=self.headers)

    def list_data_type_response(self, model: PWebBaseModel, response_dto: PWebDataDTO, status: str = PWebResponseStatus.success, code: str = PWebResponseCode.success, http_code=200):
        data_response = PWebDataResponse()
        data_response.status = status
        data_response.code = code
        data_response.add_data(model, response_dto, True)
        return self.http_response.json_string_response(data_response.to_dict(), http_code, self.headers)

    def paginate_object_response(self, pageable_model: PWebBaseModel, data: list, status: str = PWebResponseStatus.success, code: str = PWebResponseCode.success, http_code=200, message=None):
        data_response = self._get_paginate_response_object(model=pageable_model)
        data_response.data = data
        data_response.status = status
        data_response.code = code
        data_response.message = message
        return self.http_response.json_string_response(data_response.to_dict(), http_code, self.headers)

    def dictionary_object_response(self, data: dict, status: str = PWebResponseStatus.success, code: str = PWebResponseCode.success, http_code=200, message=None):
        data_response = PWebDataResponse()
        data_response.status = status
        data_response.code = code
        data_response.data = data
        data_response.message = message
        return self.http_response.json_string_response(data_response.to_dict(), http_code, self.headers)

    def list_object_response(self, data: list, status: str = PWebResponseStatus.success, code: str = PWebResponseCode.success, http_code=200):
        data_response = PWebDataResponse()
        data_response.status = status
        data_response.code = code
        data_response.data = data
        data_response.add_data(None, None, True)
        return self.http_response.json_string_response(data_response.to_dict(), http_code, self.headers)
