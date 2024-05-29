from flask import Blueprint, render_template, request
from pweb.system12.pweb_saas_registry import PWebSaaSRegistry
from pweb_form_rest.common.pweb_fr_config import PWebFRConfig
from pweb_form_rest.swagger.pweb_sd_processor import PWebSDProcessor
from pweb_form_rest.swagger.pweb_swagger_generator import PWebSwaggerGenerator


class PWebSwaggerUI:
    _pweb_app = None

    def register(self, pweb_app):
        self._pweb_app = pweb_app
        self.init_swagger_blueprint()

    def init_swagger_blueprint(self):
        if PWebFRConfig.ENABLE_SWAGGER_UI and self._pweb_app:
            blueprint = Blueprint(
                "PWebSwaggerSystem",
                __name__,
                template_folder="template-assets/templates",
                static_folder="template-assets/assets",
                static_url_path=PWebFRConfig.SWAGGER_UI_ASSETS_URL
            )
            blueprint.add_url_rule(PWebFRConfig.SWAGGER_JSON_URL, "pweb-swagger-json", self.swagger_json)
            blueprint.add_url_rule(PWebFRConfig.SWAGGER_UI_URL, "pweb-swagger-ui", self.swagger_ui)
            self._pweb_app.register_blueprint(blueprint)

    def swagger_ui(self):
        auth = self.check_auth()
        if auth:
            return auth
        return render_template('pweb-swagger-ui.html', config=PWebFRConfig)

    def swagger_json(self):
        auth = self.check_auth()
        if auth:
            return auth
        decorator_processor = PWebSDProcessor(self._pweb_app)
        action_definitions = decorator_processor.get_action_definitions()
        pweb_swagger_generator = PWebSwaggerGenerator()
        pweb_swagger_generator.process_action_definitions(action_definitions)
        return pweb_swagger_generator.get_swagger_spec()

    def check_auth(self):
        if PWebFRConfig.ENABLE_SWAGGER_AUTH:
            auth = request.authorization
            username = PWebSaaSRegistry.get_saas_config(config_key="SWAGGER_AUTH_USERNAME", default=PWebFRConfig.SWAGGER_AUTH_USERNAME)
            password = PWebSaaSRegistry.get_saas_config(config_key="SWAGGER_AUTH_PASSWORD", default=PWebFRConfig.SWAGGER_AUTH_PASSWORD)
            if not (auth and auth.username == username and auth.password == password):
                return ('You are not authorize to access the URL.', 401, {
                    'WWW-Authenticate': 'Basic realm="Login Required"'
                })
        return None
