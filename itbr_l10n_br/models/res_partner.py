import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _l10n_br_module_installed(self):
        return (
            self.env["ir.module.module"]
            .search([("name", "=", "l10n_br")], limit=1)
            .state
            == "installed"
        )

    @api.onchange("company_type", "country_id")
    def _onchange_company_type(self):
        if (
            self.country_id
            and self.country_id == self.env.ref("base.br")
            and not self.vat
            and self._l10n_br_module_installed()
        ):
            if self.company_type == "company":
                self.l10n_latam_identification_type_id = self.env.ref("l10n_br.cnpj")
            elif self.company_type == "person":
                self.l10n_latam_identification_type_id = self.env.ref("l10n_br.cpf")
