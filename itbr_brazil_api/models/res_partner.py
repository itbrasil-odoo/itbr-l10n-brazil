import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    district = fields.Char(string="District/Neighborhood")

    @api.depends("zip", "country_id")
    def get_brazil_api_zip(self):
        self.ensure_one()
        if self.country_id != self.env.ref("base.br"):
            return
        BrazilApiMixin = self.env["brazil.api.mixin"]
        response = BrazilApiMixin.get_brazil_api_response("cep", record_id=self.zip)

        if not response:
            _logger.warning(_("Brazil API returned an empty response"))
            return
        state_id = self.env["res.country.state"].search(
            [
                ("code", "=", response.get("state")),
                ("country_id", "=", self.country_id.id),
            ],
            limit=1,
        )
        self.write(
            {
                "city": response.get("city").upper(),
                "state_id": state_id.id if state_id else False,
                "district": response.get("neighborhood").upper(),
                "street": response.get("street").upper(),
            }
        )
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }
