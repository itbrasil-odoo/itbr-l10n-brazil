import logging
from urllib.parse import urljoin

import requests

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BrazilApiMixin(models.AbstractModel):
    _name = "brazil.api.mixin"
    _description = "Brazil API Mixin"

    def get_brazil_api_response(self, endpoint, version="v1", record_id=None):
        url = urljoin("https://brasilapi.com.br/api/", f"{endpoint}/{version}/")
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if record_id:
            url = urljoin(url, record_id)

        response = requests.get(url, headers=headers, timeout=120)
        if response.status_code != 200:
            raise UserError(_("Brazil API returned an error: %s") % response.text)
        return response.json()

    def sync_odoo_from_brazil_api(self, odoo_model, data):
        synced_records = []
        if len(data) == 0:
            return self.show_notification(
                _("No records to sync"),
                _("There are no records to sync from the Brazil API"),
            )
        for record in data:
            odoo_domain = record.get("domain", [])
            if "active" in self.env[odoo_model]._fields:
                odoo_domain.append(("active", "in", [True, False]))
            odoo_values = record.get("values", {})
            odoo_record = self.env[odoo_model].search(odoo_domain, limit=1)

            if odoo_record:
                self.common_log_msg(
                    qty=1,
                    module_name=odoo_record._description,
                    update=True,
                    record_name=odoo_record.name,
                )
                odoo_record.write(odoo_values)
            else:
                required_fields = record.get("required_fields", [])
                missing_fields = [
                    field for field in required_fields if not odoo_values.get(field)
                ]
                if missing_fields:
                    _logger.warning(
                        _(
                            "Skipping record in %(model)s due to missing "
                            "required fields: %(fields)s"
                        )
                        % {"model": odoo_model, "fields": ", ".join(missing_fields)}
                    )
                    continue
                self.common_log_msg(
                    qty=1,
                    module_name=odoo_model,
                    sync=True,
                    record_name=odoo_values.get("name"),
                )
                odoo_record = self.env[odoo_model].create(odoo_values)
            synced_records.append(odoo_record.id)
        return synced_records

    def show_notification(self, title, message, nt_type="info"):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": nt_type,
            },
        }

    def common_log_msg(
        self,
        qty=0,
        module_name="Brazil API",
        sync=False,
        update=False,
        record_name=None,
        api_request=False,
    ):
        """Log a message with the quantity of records processed"""
        if api_request:
            msg = _("Making request to Brazil API for %(module_name)s")
        elif qty == 0:
            if sync:
                msg = _("No %(module_name)s records to sync")
            elif update:
                msg = _("No %(module_name)s records to update")
            else:
                msg = _("No %(module_name)s records to process")
        elif qty == 1:
            if sync:
                msg = _("Synced 1 record in %(module_name)s")
            elif update:
                msg = _("Record %(record_name)s updated in %(module_name)s")
            else:
                msg = _("Let's process 1 %(module_name)s record")
        else:
            if sync:
                msg = _("Synced %(qty)s records in %(module_name)s")
            elif update:
                msg = _("%(qty)s records updated in %(module_name)s")
            else:
                msg = _("Let's process %(qty)s %(module_name)s records")

        return _logger.info(
            msg
            % {
                "qty": qty,
                "module_name": module_name,
                "record_name": record_name,
            }
        )

    def open_tree_view(self, name, model, domain):
        """Open a tree view for a model"""
        result = {
            "type": "ir.actions.act_window",
            "res_model": model,
            "views": [[False, "tree"], [False, "form"]],
            "domain": domain,
            "name": name,
        }
        if len(domain[0][2]) == 1:
            result["views"] = [[False, "form"]]
            result["res_id"] = domain[0][2][0]

        return result

    def open_form_view(self, name, model, res_id):
        """Open a form view for a record"""
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": model,
            "view_mode": "form",
            "res_id": res_id,
        }
