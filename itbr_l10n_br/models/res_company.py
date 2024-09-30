import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    is_company = fields.Boolean(
        string="Is a Company",
        related="partner_id.is_company",
        store=True,
        readonly=False,
    )
