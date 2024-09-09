from copy import copy
from flask import flash, redirect
from marshmallow import ValidationError
from werkzeug.datastructures import FileStorage
from pweb_form_rest import FileDataCRUD
from pweb_form_rest.common.pweb_fr_exception import FormRESTException
from pweb_form_rest.crud.pweb_crud_common import PWebCRUDCommon
from pweb_form_rest.form.pweb_form import PWebForm
from pweb_form_rest.form.pweb_form_data import PWebFormData
from pweb_form_rest.ui.pweb_ui_helper import PWebSSRUIHelper, ssr_ui_render
from pweb_orm import PWebBaseModel


class FormDataCRUD(PWebCRUDCommon):
    ssr_ui_helper: PWebSSRUIHelper = None
    file_data_crud: FileDataCRUD = None
    pweb_form_data: PWebFormData = PWebFormData()

    def __init__(self, model: PWebBaseModel, ssr_ui_helper: PWebSSRUIHelper = None):
        self.model = model
        self.ssr_ui_helper = ssr_ui_helper
        self.file_data_crud = FileDataCRUD(model=self.model)

    def render(self, view_name, params: dict = None, form: PWebForm = None):
        return ssr_ui_render(view_name=view_name, params=params, form=form, ssr_ui_helper=self.ssr_ui_helper)

    def pre_process_file_upload(self, request_data):
        processed_request_data = copy(request_data)
        requested_files = {}
        for field_name in request_data:
            if isinstance(request_data[field_name], FileStorage):
                filename = request_data[field_name].filename.lower()
                if filename and filename != "":
                    processed_request_data[field_name] = filename
                    requested_files[field_name] = request_data[field_name]
                elif filename == "":
                    del processed_request_data[field_name]
        return processed_request_data, requested_files

    def post_process_file_upload(self, requested_files, model, form: PWebForm, upload_path: str, override_names: dict = None):
        if not requested_files or not upload_path:
            return model
        return self.file_data_crud.upload_and_save_file(form_data=requested_files, model=model, request_dto=form, override_names=override_names, upload_path=upload_path)

    def handle_various_exception(self, exception, form: PWebForm):
        if exception and form:
            if isinstance(exception, ValidationError):
                self.pweb_form_data.handle_validation_exception(exception=exception, definition=form.definition)
            elif isinstance(exception, FormRESTException):
                self.pweb_form_data.handle_form_rest_exception(exception=exception, definition=form.definition)
        message = "Please check the validation error"
        if exception and hasattr(exception, "message"):
            message = exception.message
        flash(message, "error")

    def only_create(self, form: PWebForm, data: dict = None, upload_path: str = None, override_names: dict = None, before_save=None, after_save=None):
        if form.is_post_data() and form.is_valid_data(form_data=data):
            request_data = form.get_request_data(form_data=data)
            processed_request_data, requested_files = self.pre_process_file_upload(request_data=request_data)
            model = self.save(request_dto=form, data=processed_request_data, before_save=before_save, after_save=after_save)
            self.post_process_file_upload(requested_files=requested_files, model=model, form=form, upload_path=upload_path, override_names=override_names)
            return model
        return None

    def only_update(self, update_form: PWebForm, model_id: int = None, existing_model=None, data: dict = None, query=None, upload_path: str = None, override_names: dict = None, before_save=None, after_save=None):
        if update_form.is_post_data() and update_form.is_valid_data(form_data=data):
            request_data = update_form.get_request_data(form_data=data)
            processed_request_data, requested_files = self.pre_process_file_upload(request_data=request_data)
            model = self.edit(request_dto=update_form, model_id=model_id, existing_model=existing_model, data=processed_request_data, query=query, before_save=before_save, after_save=after_save)
            self.post_process_file_upload(requested_files=requested_files, model=model, form=update_form, upload_path=upload_path, override_names=override_names)
            return model
        return None

    def create(self, view_name: str, form: PWebForm, redirect_url=None, data: dict = None, params: dict = None, response_message: str = "Successfully created!", upload_path: str = None, override_names: dict = None, before_save=None, after_save=None):
        if form.is_post_data() and form.is_valid_data(form_data=data):
            model = self.only_create(form=form, data=data, upload_path=upload_path, override_names=override_names, before_save=before_save, after_save=after_save)
            flash(response_message, "success")
            if model and redirect_url:
                return redirect(redirect_url)
            if model:
                return model
        return self.render(view_name=view_name, form=form, params=params)

    def update(self, view_name: str, update_form: PWebForm, model_id: int = None, display_from: PWebForm = None, redirect_url: str = None, details_model=None, params: dict = None, response_message: str = "Successfully updated!", existing_model=None, data: dict = None, query=None, upload_path: str = None, override_names: dict = None, before_save=None, after_save=None):
        if update_form.is_post_data() and update_form.is_valid_data(form_data=data):
            model = self.only_update(update_form=update_form, model_id=model_id, existing_model=existing_model, data=data, query=query, upload_path=upload_path, override_names=override_names, before_save=before_save, after_save=after_save)
            flash(response_message, "success")
            if model and redirect_url:
                return redirect(redirect_url)
            if model:
                return model
        elif update_form.is_get_data():
            if not details_model and model_id:
                details_model = self.get_by_id(model_id=model_id, exception=False, query=query)

            if not details_model:
                flash('Invalid data', 'error')
                if redirect_url:
                    return redirect(redirect_url)

            if display_from and details_model:
                update_form.set_dict_value(display_from.dump(details_model))
                if hasattr(details_model, "id"):
                    update_form.set_value("id", details_model.id)
            else:
                update_form.set_model_value(details_model)

        if not params:
            params = {}
        params["isEdit"] = True
        return self.render(view_name=view_name, form=update_form, params=params)

    def delete(self, model_id: int, redirect_url: str, response_message: str = "Successfully deleted!", error_message: str = "Sorry unable to delete", query=None):
        is_deleted = self.soft_remove(model_id=model_id, query=query, exception=False)
        if is_deleted:
            flash(response_message, 'success')
        else:
            flash(error_message, 'error')
        return redirect(redirect_url)

    def details(self, view_name, model_id: int, redirect_url: str, display_from: PWebForm = None, params: dict = None, query=None):
        data = self.get_by_id(model_id=model_id, query=query, exception=False)
        if not data:
            flash('Invalid data', 'error')
            return redirect(redirect_url)

        if not params:
            params = {}

        if display_from:
            data = display_from.dump(data)
            display_from.set_dict_value(data)
            params["form"] = display_from.definition

        params.update({"data": data})
        return self.render(view_name=view_name, params=params)

    def paginated_list(self, view_name, response_def: PWebForm = None, query=None, search_fields: list = None, sort_field=None, sort_order=None, item_per_page=None, params: dict = None):
        data_list = self.read_all(query=query, search_fields=search_fields, sort_field=sort_field, sort_order=sort_order, item_per_page=item_per_page)
        if response_def and data_list.items:
            data_list.items = response_def.dump(data_list.items, many=True)
        if not params:
            params = {}
        params.update({"table": data_list})
        return self.render(view_name=view_name, params=params)

    def list(self, view_name, response_def: PWebForm = None, query=None, search_fields: list = None, sort_field=None, sort_order=None, params: dict = None):
        data_list = self.read_all(query=query, search_fields=search_fields, sort_field=sort_field, sort_order=sort_order, enable_pagination=False)
        if response_def:
            data_list = response_def.dump(data_list.items, many=True)
        if not params:
            params = {}
        params.update({"table": data_list})
        return self.render(view_name=view_name, params=params)
