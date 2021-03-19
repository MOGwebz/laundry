import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LaundryManagementOutlet(models.Model):
    _name = 'laundry.outlet'
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Laundry Management Outlets"
    # _order = 'order_date desc, id desc'

    # name = fields.Char('Outlet Name')
    partner_id = fields.Many2one('res.partner')
    code = fields.Char('Code', size=4)
    sequence_id = fields.Many2one('ir.sequence', string='Outlet Sequence',  help="Outlet Sequence.", copy=False)
    pricelist = fields.Many2one('product.pricelist', 'Pricelist')

    @api.model
    def create(self,vals):
        initials = vals['code']
        if initials:
            initials_upper = initials.upper()
            initials_upper = initials_upper.replace(" ","")
            seq_obj = self.env['ir.sequence']
            seq_vals = {
                    'name': _('%s Sequence') % vals['name'],
                    'implementation': 'no_gap',
                    'padding': 3,
                    'prefix': initials_upper +'/'+'%'+'(y)s'+'/',
                    'number_increment': 1,
                    'number_next_actual': 1,
                    # 'use_date_range': True,
                }
            seq = seq_obj.create(seq_vals)
        vals['sequence_id'] = seq.id
        vals['code'] = initials_upper
        res = super(LaundryManagementOutlet,self).create(vals)
        return res



