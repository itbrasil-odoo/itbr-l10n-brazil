import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ResBank(models.Model):
    _inherit = "res.bank"

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        domain = [
            "|",
            "|",
            ("name", operator, name),
            ("short_name", operator, name),
            ("code_bc", "=", name),
        ]
        return self.search(domain + args, limit=limit).name_get()

    @api.depends("name", "short_name", "code_bc")
    def _compute_display_name(self):
        for record in self:
            record.display_name = (
                f"[{record.code_bc}] {record.short_name or record.name}"
            )

    short_name = fields.Char()

    code_bc = fields.Char(
        string="Brazilian Bank Code",
        size=3,
        help="Brazilian Bank Code ex.: 001 is the code of Banco do Brasil",
        unaccent=False,
    )

    ispb_number = fields.Char(
        string="ISPB Number",
        size=8,
        unaccent=False,
    )

    def get_brazil_api_banks(self):
        BrazilApiMixin = self.env["brazil.api.mixin"]
        sync_to_odoo = []
        response = BrazilApiMixin.get_brazil_api_response("banks")

        if not response:
            return sync_to_odoo

        for bank in response:
            bank_code = bank.get("code")
            bank_name = bank.get("fullName") or bank.get("name")
            bank_ispb = bank.get("ispb")
            bank_short_name = bank.get("name") if bank.get("fullName") else None
            if not bank_name or not bank_code:
                continue

            odoo_domain = [("code_bc", "=", bank_code)]

            odoo_values = {
                "name": bank_name,
                "ispb_number": bank_ispb,
                "short_name": bank_short_name,
                "code_bc": bank_code,
                "country": self.env.ref("base.br").id,
            }

            sync_to_odoo.append(
                {
                    "domain": odoo_domain,
                    "values": odoo_values,
                }
            )
        return sync_to_odoo

    def get_brazil_banks(self):
        BrazilApiMixin = self.env["brazil.api.mixin"]
        records = self.get_brazil_api_banks()
        synced_records = []

        if not records:
            return BrazilApiMixin.show_notification(
                _("No banks to sync"),
                _("There are no banks to sync from the Brazil API"),
            )
        else:
            synced_records = BrazilApiMixin.sync_odoo_from_brazil_api(
                odoo_model="res.bank", data=records
            )
            BrazilApiMixin.common_log_msg(
                qty=len(synced_records),
                module_name=self._description,
                sync=True,
            )
        return BrazilApiMixin.open_tree_view(
            _("Banks"), "res.bank", [("id", "in", synced_records)]
        )
