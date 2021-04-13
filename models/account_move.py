# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class LaundryAccountMove(models.Model):
    _inherit = 'account.move'

    laundry_id = fields.Many2one('laundry.order', string='Laundry Order',)
    pickup_date = fields.Date('Pick Up Date')


    @api.model
    def create(self, vals):
        res = super(LaundryAccountMove,self).create(vals)
        if res.laundry_id:
            res.laundry_id.write({'invoice_id':res.id})        
        return res