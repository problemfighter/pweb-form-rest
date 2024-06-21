from pweb_form_rest.crud.pweb_crud import PWebCRUD
from pweb_form_rest.crud.pweb_response_maker import ResponseMaker
from pweb_form_rest.schema.pweb_rest_schema import PWebDataDTO
from pweb_orm import PWebBaseModel, pweb_orm, make_transient


class PWebCRUDCommon:
    model: PWebBaseModel = None
    pweb_crud: PWebCRUD = PWebCRUD()
    response_maker: ResponseMaker = ResponseMaker()

    def message_or_data_response(self, model, response_dto: PWebDataDTO = None, response_message: str = None):
        if not response_dto:
            return self.response_maker.success_message(response_message)
        return self.response_maker.data_response(model, response_dto, message=response_message)

    def validate_data(self, data: dict, data_dto: PWebDataDTO):
        return self.pweb_crud.validate_data(data=data, data_dto=data_dto)

    def load_model_from_dict(self, data: dict, data_dto: PWebDataDTO, instance=None):
        return self.pweb_crud.load_model_from_dict(data=data, data_dto=data_dto, instance=instance)

    def load_rest_model_from_dict(self, data: dict, data_dto: PWebDataDTO, instance=None):
        return self.pweb_crud.populate_model(data=data, data_dto=data_dto, instance=instance)

    def get_json_data(self, data_dto: PWebDataDTO, is_validate=True, load_only=False, before_validate=None, after_validate=None):
        return self.pweb_crud.get_json_data(data_dto=data_dto, is_validate=is_validate, load_only=load_only, before_validate=before_validate, after_validate=after_validate)

    def get_form_data(self, data_dto: PWebDataDTO, is_validate=True, load_only=False, is_populate_model=False, before_validate=None, after_validate=None):
        return self.pweb_crud.get_form_data(data_dto=data_dto, is_validate=is_validate, is_populate_model=is_populate_model, load_only=load_only, before_validate=before_validate, after_validate=after_validate)

    def check_unique(self, field: str, value, model_id=None, exception: bool = True, message: str = "Already used", query=None):
        self.pweb_crud.check_unique(self.model, field=field, value=value, exception=exception, message=message, query=query, model_id=model_id)

    def get_by_id(self, model_id, exception=True, message: str = "Entry Not Found!", query=None):
        return self.pweb_crud.get_by_id(self.model, id=model_id, exception=exception, message=message, query=query)

    def get_first(self, query, exception=True, message: str = "Entry Not Found!"):
        return self.pweb_crud.get_first(self.model, query=query, exception=exception, message=message)

    def read_all(self, query=None, search_fields: list = None, sort_field=None, sort_order=None, item_per_page=None, enable_pagination=True, enable_sort: bool = True):
        return self.pweb_crud.list(model=self.model, query=query, search_fields=search_fields, sort_field=sort_field, sort_order=sort_order, item_per_page=item_per_page, enable_pagination=enable_pagination, enable_sort=enable_sort)

    def perform_save(self, model, data: dict, before_save=None, after_save=None):
        if before_save and callable(before_save):
            before_save(data=data, model=model)
        model.save()
        if after_save and callable(after_save):
            after_save(data=data, model=model)
        return model

    def save(self, data: dict, request_dto: PWebDataDTO, existing_model=None, before_save=None, after_save=None):
        model = self.pweb_crud.populate_model(data, request_dto, instance=existing_model)
        return self.perform_save(model=model, data=data, before_save=before_save, after_save=after_save)

    def edit(self, model_id, data: dict, request_dto: PWebDataDTO, existing_model=None, query=None, before_save=None, after_save=None):
        if not existing_model:
            existing_model = self.get_by_id(model_id, query=query, exception=True)
        return self.save(data=data, request_dto=request_dto, existing_model=existing_model, before_save=before_save, after_save=after_save)

    def soft_remove(self, model_id: int, query=None, exception=True, before_delete=None, after_delete=None):
        existing_model = self.get_by_id(model_id, exception=exception, query=query)

        if before_delete and callable(before_delete):
            before_delete(model_id=model_id, model=existing_model)

        if existing_model and hasattr(existing_model, "isDeleted"):
            existing_model.isDeleted = True
            existing_model.save()

            if after_delete and callable(after_delete):
                after_delete(model_id=model_id, model=existing_model)

            return True
        return False

    def remove(self, model_id: int, query=None):
        existing_model = self.get_by_id(model_id, exception=True, query=query)
        existing_model.delete()

    def save_all(self, model_list: list):
        self.model.save_all(model_list)

    def clone(self, model, none_props: list = None):
        pweb_orm.session.expunge(model)
        make_transient(model)

        if not none_props:
            none_props = []

        for prop in ["id", "uuid", "created", "updated"] + none_props:
            if hasattr(model, prop):
                setattr(model, prop, None)
        return model
