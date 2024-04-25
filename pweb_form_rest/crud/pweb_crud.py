from copy import copy
from flask import sessions
from marshmallow import EXCLUDE, ValidationError
from pweb_form_rest.common.pweb_fr_config import PWebFRConfig
from pweb_form_rest.common.pweb_fr_exception import form_rest_exception
from pweb_form_rest.crud.pweb_request_data import RequestData
from pweb_form_rest.data.pweb_response_status import PWebResponseCode
from pweb_form_rest.schema.pweb_rest_schema import PWebDataDTO
from pweb_orm import PWebBaseModel, and_, or_, pweb_orm


class PWebCRUD:
    request_data: RequestData = RequestData()

    def validate_data(self, data: dict, data_dto: PWebDataDTO, session=sessions, unknown=EXCLUDE):
        try:
            setattr(data_dto, "unknown", unknown)
            errors = data_dto.validate(data, session=session)
            if errors:
                raise form_rest_exception.process_validation_exception(errors=errors, message=PWebFRConfig.VALIDATION_ERROR)
            return data
        except ValidationError as error:
            raise form_rest_exception.process_validation_exception(errors=error.messages, message=PWebFRConfig.VALIDATION_ERROR)

    def load_model_from_dict(self, data: dict, data_dto: PWebDataDTO, session=sessions, instance=None):
        return data_dto.load(data, session=session, instance=instance, unknown=EXCLUDE)

    def load_allowed_data_from_dict(self, data: dict, data_dto: PWebDataDTO, instance=None):
        modified_data_dto = copy(data_dto)
        if hasattr(modified_data_dto, "_load_instance"):
            setattr(modified_data_dto, "_load_instance", False)
        return modified_data_dto.load(data, instance=instance, unknown=EXCLUDE)

    def populate_model(self, data: dict, data_dto: PWebDataDTO, session=sessions, instance=None):
        try:
            return self.load_model_from_dict(data, data_dto, session, instance)
        except ValidationError as error:
            raise form_rest_exception.process_validation_exception(errors=error.messages, message=PWebFRConfig.VALIDATION_ERROR)

    def get_json_data(self, data_dto: PWebDataDTO, is_validate=True, load_only=False, json_obj=None):
        if not json_obj:
            json_obj = self.request_data.json_data()
        else:
            if "data" not in json_obj:
                json_obj = {"data": json_obj}
        if not json_obj or "data" not in json_obj:
            raise form_rest_exception.error_message_exception(message=PWebFRConfig.INVALID_REQUEST_DATA, code=PWebResponseCode.error)
        json_obj = json_obj["data"]

        if is_validate:
            self.validate_data(json_obj, data_dto)

        if load_only:
            return self.load_allowed_data_from_dict(json_obj, data_dto)

        return json_obj

    def get_form_data(self, data_dto: PWebDataDTO, is_validate=True, is_populate_model=False, load_only=False, form_data=None):
        if not form_data:
            form_data = self.request_data.form_and_file_data()

        if not form_data:
            raise form_rest_exception.error_message_exception(message=PWebFRConfig.INVALID_REQUEST_DATA, code=PWebResponseCode.error)

        if is_validate:
            data = self.validate_data(form_data, data_dto)

            if is_populate_model:
                return self.load_model_from_dict(data, data_dto)

        if load_only:
            return self.load_allowed_data_from_dict(form_data, data_dto)

        return form_data

    def get_query_args(self, name, exception=True, exception_message=None, default=None, type=None):
        value = self.request_data.get_query_args_value(name, default=default, type=type)
        if not value and exception:
            if not exception_message:
                exception_message = name + " not found"
            raise form_rest_exception.error_message_exception(exception_message)
        return value

    def set_sort_order(self, model, query, default_field=PWebFRConfig.SORT_DEFAULT_FIELD_NAME, default_order=PWebFRConfig.SORT_DEFAULT_ORDER_NAME):
        sort_field = self.request_data.get_query_args_value(PWebFRConfig.SORT_FIELD_PARAM_NAME, default=default_field)
        sort_order = self.request_data.get_query_args_value(PWebFRConfig.SORT_ORDER_PARAM_NAME, default=default_order)
        if sort_order and (sort_order != "asc" and sort_order != "desc"):
            sort_order = default_order

        if not sort_order or not sort_field:
            return query

        if sort_order == "asc":
            return query.order_by(getattr(model, sort_field).asc())

        return query.order_by(getattr(model, sort_field).desc())

    def set_pagination(self, query, item_per_page=PWebFRConfig.TOTAL_ITEM_PER_PAGE):
        page: int = self.request_data.get_query_args_value(PWebFRConfig.PAGE_PARAM_NAME, default=0, type=int)
        per_page: int = self.request_data.get_query_args_value(PWebFRConfig.ITEM_PER_PAGE_PARAM_NAME, default=item_per_page, type=int)
        return query.paginate(page=page, per_page=per_page, error_out=False)

    def set_search(self, model, search_fields: list, query, search_text: str = None):
        like = []
        search = search_text
        if not search:
            search = self.request_data.get_query_args_value(PWebFRConfig.SEARCH_FIELD_PARAM_NAME)
        if search:
            for field in search_fields:
                like.append(getattr(model, field).ilike("%{}%".format(search)))
            if like:
                return query.filter(or_(*like))
        return query

    def list(self, model: PWebBaseModel, query=None, search_fields: list = None, enable_pagination: bool = True, enable_sort: bool = True,
             is_deleted=False, sort_field=None, sort_order=None, item_per_page=None, search_text: str = None
             ):
        if not query:
            query = model.query
        query = query.filter(getattr(model, "isDeleted") == is_deleted)

        if not sort_field:
            sort_field = PWebFRConfig.SORT_DEFAULT_FIELD_NAME

        if not sort_order:
            sort_order = PWebFRConfig.SORT_DEFAULT_ORDER_NAME

        if not item_per_page:
            item_per_page = PWebFRConfig.TOTAL_ITEM_PER_PAGE

        if enable_sort:
            query = self.set_sort_order(model, query=query, default_field=sort_field, default_order=sort_order)

        if search_fields:
            query = self.set_search(model, query=query, search_fields=search_fields, search_text=search_text)

        if enable_pagination:
            return self.set_pagination(query, item_per_page=item_per_page)

        return query.all()

    def get_by_id(self, model: PWebBaseModel, id: int, is_deleted: bool = False, exception: bool = False, message: str = "Entry Not Found!", query=None):
        if not query:
            query = model.query
        result = query.filter(and_(model.id == id, model.isDeleted == is_deleted)).first()
        if result:
            return result
        if not result and exception:
            raise form_rest_exception.error_message_exception(message)
        return None

    def get_first(self, model: PWebBaseModel, query, is_deleted: bool = False, exception: bool = False, message: str = "Entry Not Found!"):
        result = query.filter(and_(model.isDeleted == is_deleted)).first()
        if result:
            return result
        if not result and exception:
            raise form_rest_exception.error_message_exception(message)
        return None

    def get_by_ids(self, model: PWebBaseModel, ids, is_deleted: bool = False, exception: bool = False, message: str = "Not Found!", query=None):
        if not query:
            query = model.query
        result = query.filter(and_(model.id.in_(ids), model.isDeleted == is_deleted)).all()
        if result:
            return result
        if not result and exception:
            raise form_rest_exception.error_message_exception(message)
        return None

    def get_by_ids_not_in(self, model: PWebBaseModel, ids, is_deleted: bool = False, exception: bool = False, message: str = "Not Found!", query=None):
        if not query:
            query = model.query
        result = query.filter(and_(model.id.not_in(ids), model.isDeleted == is_deleted)).all()
        if result:
            return result
        if not result and exception:
            raise form_rest_exception.error_message_exception(message)
        return None

    def delete_all(self, model: PWebBaseModel, query=None):
        if not query:
            query = model.query
        query.delete()
        pweb_orm.session.commit()

    def delete_by_ids_not_in(self, model: PWebBaseModel, ids, query=None):
        if not query:
            query = model.query
        query.filter(and_(model.id.not_in(ids))).delete()
        pweb_orm.session.commit()

    def delete_by_ids_in(self, model: PWebBaseModel, ids, query=None):
        if not query:
            query = model.query
        query.filter(and_(model.id.in_(ids))).delete()
        pweb_orm.session.commit()

    def check_unique(self, model: PWebBaseModel, field: str, value, model_id=None, exception: bool = True, message: str = "Already used", query=None):
        if not query:
            query = model.query
        query = query.filter(getattr(model, field) == value)
        if model_id:
            query = query.filter(model.id != model_id)
        result = query.first()
        if result and exception:
            raise form_rest_exception.error_details_exception("Unique filed error", details={field: message})

    def update_all(self, query, name_values: dict):
        query.update(name_values)
        pweb_orm.session.commit()
