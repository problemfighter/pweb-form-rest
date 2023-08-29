import pweb_form_rest.common.pweb_fr_config
from ppy_common import ObjectHelper
from pweb_form_rest.swagger.pweb_swagger_ui import PWebSwaggerUI


class PWebFR:

    def init_app(self, pweb_app, config):
        self.update_config(config)
        self.register_swagger(pweb_app)

    def update_config(self, config):
        ObjectHelper.copy_config_property(config, pweb_form_rest.common.pweb_fr_config.PWebFRConfig)

    def register_swagger(self, pweb_app):
        pweb_swagger_ui = PWebSwaggerUI()
        pweb_swagger_ui.register(pweb_app)
