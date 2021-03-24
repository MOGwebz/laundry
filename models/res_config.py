# -*- coding: utf-8 -*-
from odoo import fields,models,api,_,osv

class LaundrySettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'laundry.config.settings'

    default_note = fields.Text(default_model='laundry.order', string='Terms and Conditions', help="Terms and Conditions")    
    # default_bidfee_acc = fields.Many2one('account.account', default_model='account.move', string='Bid Fee(Auction Purchases)', help="The purchase account related to Bid Fee.")