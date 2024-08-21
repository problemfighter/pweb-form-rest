from pweb_form_rest.crud.pweb_crud_common import PWebCRUDCommon
from pweb_form_rest.crud.pweb_upload_processor import PWebUploadProcessor
from pweb_form_rest.schema.pweb_rest_schema import PWebDataDTO
from pweb_orm import PWebBaseModel
from ppy_common import PyCommon


class FileDataCRUD(PWebCRUDCommon):
    pweb_upload_processor: PWebUploadProcessor = PWebUploadProcessor()

    def __init__(self, model: PWebBaseModel):
        self.model = model

    def upload_and_save_file(self, form_data, model, request_dto: PWebDataDTO, upload_path, override_names: dict = None, before_save=None, after_save=None):
        override_names = self.pweb_upload_processor.get_file_override_names(uuid=model.uuid, request_dto=request_dto, override_names=override_names)
        uploaded_file_names = self.pweb_upload_processor.validate_and_upload_multiple(form_data=form_data, request_dto=request_dto, upload_path=upload_path, override_name=override_names)
        for name in override_names:
            if hasattr(model, name) and name in uploaded_file_names:
                file_name = uploaded_file_names[name][override_names[name]]
                setattr(model, name, file_name)

        model = self.pweb_upload_processor.delete_orphan_files(override_names=override_names, form_data=form_data, model=model, upload_path=upload_path)
        model = self.perform_save(model=model, data=form_data, before_save=before_save, after_save=after_save)
        return model

    def get_model_by_upload_file_data(self, request_dto: PWebDataDTO, upload_path, override_names: dict = None, existing_model=None, form_data: dict = None, before_save=None, after_save=None, before_validate=None, after_validate=None, ignore_load: list = None):
        if not form_data:
            form_data = self.pweb_crud.get_form_data(request_dto, before_validate=before_validate, after_validate=after_validate)
        model = self.pweb_crud.populate_model(form_data, request_dto, instance=existing_model, ignore_load=ignore_load)
        if not model.uuid:
            model.uuid = PyCommon.uuid()
        return self.upload_and_save_file(form_data=form_data, model=model, request_dto=request_dto, upload_path=upload_path, override_names=override_names, before_save=before_save, after_save=after_save)

    def upload_file_data_and_save(self, request_dto: PWebDataDTO, upload_path, override_names: dict = None, form_data=None, before_save=None, after_save=None, before_validate=None, after_validate=None, ignore_load: list = None):
        model = self.get_model_by_upload_file_data(request_dto=request_dto, upload_path=upload_path, override_names=override_names, form_data=form_data, before_save=before_save, after_save=after_save, before_validate=before_validate, after_validate=after_validate, ignore_load=ignore_load)
        return model

    def upload_file_data(self, request_dto: PWebDataDTO, upload_path, response_dto: PWebDataDTO = None, override_names: dict = None, response_message: str = "Successfully created!", form_data=None, before_save=None, after_save=None, before_validate=None, after_validate=None, ignore_load: list = None):
        model = self.upload_file_data_and_save(request_dto=request_dto, upload_path=upload_path, override_names=override_names, form_data=form_data, before_save=before_save, after_save=after_save, before_validate=before_validate, after_validate=after_validate, ignore_load=ignore_load)
        return self.message_or_data_response(model=model, response_dto=response_dto, response_message=response_message)

    def update_upload_file_data_save(self, request_dto: PWebDataDTO, upload_path, override_names: dict = None, existing_model=None, form_data: dict = None, query=None, before_save=None, after_save=None, before_validate=None, after_validate=None, ignore_load: list = None):
        if not form_data:
            form_data = self.pweb_crud.get_form_data(data_dto=request_dto, before_validate=before_validate, after_validate=after_validate)

        if not existing_model:
            existing_model = self.get_by_id(form_data['id'], query=query, exception=True)

        model = self.get_model_by_upload_file_data(request_dto=request_dto, upload_path=upload_path, override_names=override_names, form_data=form_data, existing_model=existing_model, before_save=before_save, after_save=after_save, ignore_load=ignore_load)
        return model

    def update_upload_file_data(self, request_dto: PWebDataDTO, upload_path, response_dto: PWebDataDTO = None, override_names: dict = None, response_message: str = "Successfully updated!", existing_model=None, form_data: dict = None, query=None, before_save=None, after_save=None, before_validate=None, after_validate=None, ignore_load: list = None):
        model = self.update_upload_file_data_save(request_dto=request_dto, upload_path=upload_path, override_names=override_names, form_data=form_data, existing_model=existing_model, query=query, before_save=before_save, after_save=after_save, before_validate=before_validate, after_validate=after_validate, ignore_load=ignore_load)
        return self.message_or_data_response(model=model, response_dto=response_dto, response_message=response_message)

    def delete_file(self, upload_path, filename, response_message: str = "Successfully deleted!"):
        self.pweb_upload_processor.delete_file(upload_path=upload_path, filename=filename)
        return self.message_or_data_response(model=None, response_message=response_message)
